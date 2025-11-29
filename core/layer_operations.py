# -*- coding: utf-8 -*-
"""
KAT Analysis – Layer Operations
Layer merging, corrections, backup, and export

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os
import tempfile
from typing import List, Tuple, Optional, Dict, Any
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsField, QgsProject, QgsVectorFileWriter,
    QgsWkbTypes, QgsGeometry, QgsCoordinateTransformContext, QgsSymbol,
    QgsRendererRange, QgsGraduatedSymbolRenderer
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from .utils import log_message, tr, ensure_parent_dir, TempLayerTracker

# ===============LAYER COMPATIBILITY & MERGING========================

def check_layers_compatibility(layers: List[QgsVectorLayer]) -> Tuple[bool, Optional[str]]:
    """Check if layers can be merged (same geometry type)"""
    if not layers or len(layers) < 2:
        return True, None
    
    first_geom_type = layers[0].geometryType()
    for layer in layers[1:]:
        if layer.geometryType() != first_geom_type:
            return False, tr("Incompatible geometry types")
    
    return True, None


def merge_layers_to_temp(layers: List[QgsVectorLayer],
                         merge_name: str = "merged_temp") -> Tuple[Optional[QgsVectorLayer], Optional[str]]:
    """
    Merge multiple layers into temporary memory layer with source tracking
    """
    if not layers:
        return None, tr("No layers provided")
    
    if len(layers) == 1:
        return layers[0], None
    
    try:
        ok, msg = check_layers_compatibility(layers)
        if not ok:
            return None, msg
        
        # Find common fields
        common_fields = None
        for layer in layers:
            layer_field_dict = {field.name(): field.type() for field in layer.fields()}
            if common_fields is None:
                common_fields = layer_field_dict
            else:
                common_fields = {name: ftype for name, ftype in common_fields.items()
                                if name in layer_field_dict and layer_field_dict[name] == ftype}
        
        if not common_fields:
            return None, tr("No common fields found")
        
        # Create temporary memory layer
        first_layer = layers[0]
        crs = first_layer.crs()
        wkb_type = first_layer.wkbType()
        uri = f"{QgsWkbTypes.displayString(wkb_type)}?crs={crs.authid()}"
        temp_layer = QgsVectorLayer(uri, merge_name, "memory")
        
        if not temp_layer.isValid():
            return None, tr("Unable to create temporary layer")
        
        provider = temp_layer.dataProvider()
        
        # Add common fields + source tracking
        fields_to_add = []
        for field_name in sorted(common_fields.keys()):
            for layer in layers:
                field = layer.fields().field(field_name)
                if field:
                    fields_to_add.append(field)
                    break
        fields_to_add.append(QgsField("__source_layer_id", QVariant.String))
        fields_to_add.append(QgsField("__source_layer_name", QVariant.String))
        provider.addAttributes(fields_to_add)
        temp_layer.updateFields()
        
        # Merge features
        all_features = []
        for source_layer in layers:
            source_layer_id = source_layer.id()
            source_layer_name = source_layer.name()
            
            for feature in source_layer.getFeatures():
                if feature.geometry() is None or feature.geometry().isEmpty():
                    continue
                
                new_feat = QgsFeature(temp_layer.fields())
                
                # Copy common attributes
                for field_name in common_fields.keys():
                    try:
                        idx = temp_layer.fields().indexOf(field_name)
                        if idx >= 0:
                            new_feat.setAttribute(idx, feature[field_name])
                    except:
                        pass
                
                # Add source tracking
                tracer_idx = temp_layer.fields().indexOf("__source_layer_id")
                name_idx = temp_layer.fields().indexOf("__source_layer_name")
                if tracer_idx >= 0:
                    new_feat.setAttribute(tracer_idx, source_layer_id)
                if name_idx >= 0:
                    new_feat.setAttribute(name_idx, source_layer_name)
                
                new_feat.setGeometry(feature.geometry())
                all_features.append(new_feat)
        
        if not all_features:
            return None, tr("No valid features to merge")
        
        provider.addFeatures(all_features)
        temp_layer.updateExtents()
        
        # Track for cleanup
        TempLayerTracker.track_layer(temp_layer.id())
        
        return temp_layer, None
        
    except Exception as e:
        log_message('error', f"Merge error: {e}", e)
        return None, tr("Merge error: {}").format(str(e))


# =================LAYER CORRECTOR WITH SAFE TRANSACTIONS=======================================

class LayerCorrector:
    """
    Apply corrections to layers with backup and transaction safety
    """
    
    def __init__(self, layer: QgsVectorLayer, id_field: Optional[str] = None):
        """
        Initialize corrector
        
        :param layer: Layer to correct
        :param id_field: Optional ID field for resolution
        """
        self.layer = layer
        self.id_field = id_field
        self.backup_path = None
    
    def create_backup(self) -> Tuple[bool, Optional[str]]:
        """Create backup GPKG before modifications"""
        if not self.layer or not self.layer.isValid():
            return False, tr("Invalid layer")
        
        try:
            temp_dir = tempfile.gettempdir()
            backup_name = f"backup_{self.layer.name()}_{os.getpid()}.gpkg"
            self.backup_path = os.path.join(temp_dir, backup_name)
            
            success, error = export_vector_layer(self.layer, self.backup_path, "GPKG")
            if success:
                log_message('info', f"Backup created: {self.backup_path}")
                return True, None
            else:
                return False, error
        except Exception as e:
            log_message('error', f"Backup failed: {e}", e)
            return False, str(e)
    
    def restore_backup(self) -> Tuple[bool, Optional[str]]:
        """Restore from backup if exists"""
        if not self.backup_path or not os.path.exists(self.backup_path):
            return False, tr("No backup found")
        
        try:
            # Load backup layer
            backup_layer = QgsVectorLayer(self.backup_path, "backup", "ogr")
            if not backup_layer.isValid():
                return False, tr("Invalid backup")
            
            # Clear current layer
            self.layer.startEditing()
            all_ids = [f.id() for f in self.layer.getFeatures()]
            self.layer.dataProvider().deleteFeatures(all_ids)
            
            # Restore features
            features = list(backup_layer.getFeatures())
            self.layer.dataProvider().addFeatures(features)
            self.layer.commitChanges()
            self.layer.updateExtents()
            
            log_message('info', "Layer restored from backup")
            return True, None
        except Exception as e:
            log_message('error', f"Restore failed: {e}", e)
            return False, str(e)
    
    def apply_deletions(self, values: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Delete features matching values or feature IDs (with transaction safety)
        
        :param values: List of ID values to delete
        :return: (success, error_message)
        """
        if not self.layer or not self.layer.isValid():
            return False, tr("Invalid layer")
        
        # Create backup first
        backup_ok, backup_err = self.create_backup()
        if not backup_ok:
            log_message('warning', f"Proceeding without backup: {backup_err}")
        
        try:
            to_delete = []
            id_field = self.id_field
            
            if id_field and id_field in [f.name() for f in self.layer.fields()]:
                # Delete by attribute value
                for feat in self.layer.getFeatures():
                    if str(feat[id_field]) in values:
                        to_delete.append(feat.id())
            else:
                # Delete by FID
                for feat in self.layer.getFeatures():
                    if str(feat.id()) in values:
                        to_delete.append(feat.id())
            
            if not to_delete:
                return True, None
            
            # Transaction
            self.layer.startEditing()
            ok = self.layer.dataProvider().deleteFeatures(to_delete)
            
            if ok:
                if self.layer.commitChanges():
                    self.layer.triggerRepaint()
                    log_message('info', f"Deleted {len(to_delete)} features from {self.layer.name()}")
                    return True, None
                else:
                    self.layer.rollBack()
                    return False, tr("Commit failed")
            else:
                self.layer.rollBack()
                return False, tr("Deletion failed")
                
        except Exception as e:
            try:
                if self.layer.isEditable():
                    self.layer.rollBack()
            except:
                pass
            log_message('error', f"Deletion error: {e}", e)
            return False, str(e)
    
    def apply_geometry_trimming(self, trim_geometry: QgsGeometry) -> Tuple[bool, Optional[str]]:
        """
        Trim layer features using geometry difference (with backup)
        
        :param trim_geometry: Geometry to subtract from features
        :return: (success, error_message)
        """
        if not self.layer or not self.layer.isValid():
            return False, tr("Invalid layer")
        
        # Create backup
        backup_ok, backup_err = self.create_backup()
        if not backup_ok:
            log_message('warning', f"Proceeding without backup: {backup_err}")
        
        try:
            crs = self.layer.crs()
            wkb = self.layer.wkbType()
            uri = f"{QgsWkbTypes.displayString(wkb)}?crs={crs.authid()}"
            mem = QgsVectorLayer(uri, f"{self.layer.name()}_trimmed", "memory")
            mem_dp = mem.dataProvider()
            mem_dp.addAttributes(self.layer.fields())
            mem.updateFields()
            
            feats_out = []
            for feat in self.layer.getFeatures():
                g = feat.geometry()
                if not g or g.isEmpty():
                    feats_out.append(feat)
                    continue
                
                try:
                    # Validate geometries before operation
                    if not g.isGeosValid():
                        g = g.makeValid()
                    if not trim_geometry.isGeosValid():
                        trim_geometry = trim_geometry.makeValid()
                    
                    new_g = g.difference(trim_geometry)
                    
                    # Validate result
                    if not new_g.isGeosValid():
                        new_g = new_g.makeValid()
                except Exception as geom_e:
                    log_message('warning', f"Geometry operation failed for feature {feat.id()}: {geom_e}")
                    new_g = g
                
                f = QgsFeature()
                f.setFields(mem.fields())
                for idx, fld in enumerate(self.layer.fields()):
                    f.setAttribute(idx, feat.attribute(fld.name()))
                f.setGeometry(new_g)
                feats_out.append(f)
            
            mem_dp.addFeatures(feats_out)
            mem.updateExtents()
            QgsProject.instance().addMapLayer(mem)
            
            log_message('info', f"Trimmed layer created: {mem.name()}")
            return True, None
            
        except Exception as e:
            log_message('error', f"Trimming error: {e}", e)
            return False, str(e)


# ==============SYMBOLOGY===============

def apply_severity_symbology(layer: QgsVectorLayer):
    """Apply graduated symbology based on severity"""
    try:
        severity_map = {tr("Critical"): 0, tr("High"): 1, tr("Moderate"): 2, tr("Low"): 3}
        
        if layer.fields().indexOf('severity_num') == -1:
            layer.dataProvider().addAttributes([QgsField("severity_num", QVariant.Int)])
            layer.updateFields()
        
        idx = layer.fields().indexOf('severity_num')
        layer.startEditing()
        for feat in layer.getFeatures():
            sv = feat['severity'] if 'severity' in layer.fields().names() else ''
            layer.changeAttributeValue(feat.id(), idx, severity_map.get(sv, 2))
        layer.commitChanges()
        
        # Create ranges
        ranges = []
        colors = ["#e74c3c", "#e67e22", "#f39c12", "#27ae60"]
        labels = [tr("Critical"), tr("High"), tr("Moderate"), tr("Low")]
        
        for i, color in enumerate(colors):
            sym = QgsSymbol.defaultSymbol(layer.geometryType())
            sym.setColor(QColor(color))
            sym.setOpacity(0.6)
            ranges.append(QgsRendererRange(i, i, sym, labels[i]))
        
        renderer = QgsGraduatedSymbolRenderer('severity_num', ranges)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
    except Exception as e:
        log_message('warning', f"Symbology application failed: {e}")

# ==================EXPORT=================

def export_vector_layer(layer: QgsVectorLayer, path: str,
                       driver: str = "GPKG", layer_name: str = None) -> Tuple[bool, Optional[str]]:
    """Export vector layer to file"""
    try:
        ensure_parent_dir(path)
        transform_context = QgsProject.instance().transformContext()
        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = driver
        opts.fileEncoding = "UTF-8"
        if layer_name:
            opts.layerName = layer_name
        
        res, err = QgsVectorFileWriter.writeAsVectorFormatV2(layer, path, transform_context, opts)
        if res == QgsVectorFileWriter.NoError:
            log_message('info', f"Export successful: {path}")
            return True, None
        
        log_message('error', f"Export failed: {err}")
        return False, tr("Export error: {}").format(err)
    except Exception as e:
        log_message('error', f"Export exception: {e}", e)
        return False, str(e)
