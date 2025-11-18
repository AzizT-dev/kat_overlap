# -*- coding: utf-8 -*-
"""
KAT Analysis – Layer Manager

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os, traceback
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsField, QgsFields, QgsProject, QgsVectorFileWriter,
    QgsWkbTypes, QgsGeometry, QgsFeatureRequest, QgsCoordinateTransformContext, QgsSymbol,
    QgsRendererRange, QgsGraduatedSymbolRenderer
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from typing import Dict, Any, List, Optional, Tuple

from qgis.core import QgsApplication

def tr(message):
    """Get the translation for a string using Qt translation API."""
    return QgsApplication.translate('LayerManager', message)

LOG_TAG = "kat_overlap.layer_manager"


# ============================================================================
# ROBUST MULTI-LAYER FUSION v2.6 - SOLUTION 1+3
# ============================================================================

def check_layers_compatibility(layers: List[QgsVectorLayer]) -> Tuple[bool, Optional[str]]:
    """
    Check RELAXED compatibility: same geometry type only.
    Schema differences are automatically handled during fusion.
    """
    if not layers or len(layers) < 2:
        return True, None
    
    first_geom_type = layers[0].geometryType()
    for layer in layers[1:]:
        if layer.geometryType() != first_geom_type:
            return False, self.tr("Incompatible geometry types")
    
    return True, None


def merge_layers_to_temp(layers: List[QgsVectorLayer], 
                         merge_name: str = "merged_temp") -> Tuple[Optional[QgsVectorLayer], Optional[str]]:
    """
    Merge N layers of same type into 1 temporary memory layer.
    SOLUTION 1: Keep only FIELDS COMMON to all layers
    """
    if not layers:
        return None, self.tr("No layers provided")
    
    if len(layers) < 2:
        return layers[0], None
    
    try:
        ok, msg = check_layers_compatibility(layers)
        if not ok:
            return None, msg
        
        # FIND FIELDS COMMON TO ALL LAYERS
        common_fields = None
        
        for layer in layers:
            layer_field_dict = {}
            for field in layer.fields():
                fname = field.name()
                ftype = field.type()
                layer_field_dict[fname] = ftype
            
            if common_fields is None:
                common_fields = layer_field_dict
            else:
                common_fields = {
                    name: ftype for name, ftype in common_fields.items() 
                    if name in layer_field_dict and layer_field_dict[name] == ftype
                }
        
        if not common_fields:
            return None, self.tr("No common fields found")
        
        # Create temp layer
        first_layer = layers[0]
        crs = first_layer.crs()
        geom_type = first_layer.geometryType()
        wkb_type = first_layer.wkbType()
        geom_type_str = QgsWkbTypes.displayString(wkb_type)
        
        uri = f"{geom_type_str}?crs={crs.authid()}"
        temp_layer = QgsVectorLayer(uri, merge_name, "memory")
        
        if not temp_layer.isValid():
            return None, self.tr("Unable to create temp layer")
        
        provider = temp_layer.dataProvider()
        
        # Add COMMON fields + traceability
        fields_to_add = []
        
        for field_name in sorted(common_fields.keys()):
            for layer in layers:
                field = layer.fields().field(field_name)
                if field:
                    fields_to_add.append(field)
                    break
        
        tracer_field = QgsField("__source_layer_id", QVariant.String)
        source_name_field = QgsField("__source_layer_name", QVariant.String)
        fields_to_add.append(tracer_field)
        fields_to_add.append(source_name_field)
        
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
                
                for field_name in common_fields.keys():
                    try:
                        field_idx = temp_layer.fields().indexOf(field_name)
                        if field_idx >= 0:
                            value = feature[field_name]
                            new_feat.setAttribute(field_idx, value)
                    except Exception:
                        pass
                
                tracer_idx = temp_layer.fields().indexOf("__source_layer_id")
                name_idx = temp_layer.fields().indexOf("__source_layer_name")
                
                if tracer_idx >= 0:
                    new_feat.setAttribute(tracer_idx, source_layer_id)
                if name_idx >= 0:
                    new_feat.setAttribute(name_idx, source_layer_name)
                
                new_feat.setGeometry(feature.geometry())
                all_features.append(new_feat)
        
        if not all_features:
            return None, self.tr("No valid features")
        
        provider.addFeatures(all_features)
        temp_layer.updateExtents()
        
        return temp_layer, None
    
    except Exception as e:
        return None, self.tr("Merge error: {}").format(str(e))


def get_selected_layers_by_type(selected_layer_ids: set) -> Dict[str, List[QgsVectorLayer]]:
    """Group layers by geometry type"""
    layers_by_type = {'polygon': [], 'line': [], 'point': []}
    
    for lid in selected_layer_ids:
        layer = QgsProject.instance().mapLayer(lid)
        if not layer:
            continue
        
        geom_type = layer.geometryType()
        if geom_type == 2:
            layers_by_type['polygon'].append(layer)
        elif geom_type == 1:
            layers_by_type['line'].append(layer)
        elif geom_type == 0:
            layers_by_type['point'].append(layer)
    
    return layers_by_type


# ============================================================================
# LAYER MANAGER
# ============================================================================

class LayerManager:
    @staticmethod
    def build_overlap_display_layer(overlap_items: list, crs, base_name: str = "KAT_Overlap", min_area_display: float = 1.0):
        """Create an anomaly display layer"""
        fields = QgsFields()
        fields.append(QgsField("anomaly", QVariant.String))
        fields.append(QgsField("id_a", QVariant.String))
        fields.append(QgsField("id_b", QVariant.String))
        fields.append(QgsField("measure", QVariant.Double))
        fields.append(QgsField("ratio_pct", QVariant.Double))
        fields.append(QgsField("severity", QVariant.String))
        
        uri = f"MultiPolygon?crs={crs.authid()}"
        display_layer = QgsVectorLayer(uri, f"{base_name}_overlap", "memory")
        prov = display_layer.dataProvider()
        prov.addAttributes(fields)
        display_layer.updateFields()
        
        feats_to_add = []
        for item in overlap_items:
            geom = item.get("geometry")
            if geom is None:
                continue
            try:
                area = geom.area() if geom is not None else 0.0
            except Exception:
                try:
                    area = float(item.get("measure", 0))
                except Exception:
                    area = 0.0
            
            if area and area < float(min_area_display):
                continue
            
            f = QgsFeature()
            f.setFields(fields)
            f.setAttribute("anomaly", item.get("anomaly", ""))
            f.setAttribute("id_a", str(item.get("id_a_real", item.get("id_a", ""))))
            f.setAttribute("id_b", str(item.get("id_b_real", item.get("id_b", ""))))
            f.setAttribute("measure", float(item.get("measure", 0) or 0))
            try:
                f.setAttribute("ratio_pct", float(item.get("ratio", 0) or 0) * 100.0)
            except Exception:
                f.setAttribute("ratio_pct", 0.0)
            f.setAttribute("severity", str(item.get("severity", "")))
            
            try:
                f.setGeometry(item.get("geometry"))
            except Exception:
                pass
            
            feats_to_add.append(f)
        
        if feats_to_add:
            prov.addFeatures(feats_to_add)
            display_layer.updateExtents()
            QgsProject.instance().addMapLayer(display_layer)
            return display_layer
        else:
            return None

    @staticmethod
    def apply_symbology_by_severity(layer: QgsVectorLayer):
        """Apply symbology by severity"""
        try:
            severity_map = {self.tr("Critique"): 0, self.tr("Élevée"): 1, self.tr("Modéré"): 2, self.tr("Faible"): 3}
            
            if layer.fields().indexOf('severity_num') == -1:
                layer.dataProvider().addAttributes([QgsField("severity_num", QVariant.Int)])
                layer.updateFields()
            
            idx = layer.fields().indexOf('severity_num')
            layer.startEditing()
            
            for feat in layer.getFeatures():
                sv = feat['severity'] if 'severity' in layer.fields().names() else ''
                layer.changeAttributeValue(feat.id(), idx, severity_map.get(sv, 2))
            
            layer.commitChanges()
            
            ranges = []
            s0 = QgsSymbol.defaultSymbol(layer.geometryType())
            s0.setColor(QColor("#e74c3c"))
            s0.setOpacity(0.6)
            
            s1 = QgsSymbol.defaultSymbol(layer.geometryType())
            s1.setColor(QColor("#e67e22"))
            s1.setOpacity(0.6)
            
            s2 = QgsSymbol.defaultSymbol(layer.geometryType())
            s2.setColor(QColor("#f39c12"))
            s2.setOpacity(0.6)
            
            s3 = QgsSymbol.defaultSymbol(layer.geometryType())
            s3.setColor(QColor("#27ae60"))
            s3.setOpacity(0.6)
            
            ranges.append(QgsRendererRange(0, 0, s0, self.tr("Critique")))
            ranges.append(QgsRendererRange(1, 1, s1, self.tr("Élevée")))
            ranges.append(QgsRendererRange(2, 2, s2, self.tr("Modéré")))
            ranges.append(QgsRendererRange(3, 3, s3, self.tr("Faible")))
            
            renderer = QgsGraduatedSymbolRenderer('severity_num', ranges)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
        except Exception:
            pass


class LayerCorrector:
    def __init__(self, layer: QgsVectorLayer, id_field: Optional[str]):
        self.layer = layer
        self.id_field = id_field

    def apply_corrections_by_values_or_fids(self, values: List[str]) -> Tuple[bool, Optional[str]]:
        """Delete features"""
        try:
            if self.layer is None:
                return False, self.tr("Invalid layer")
            
            to_delete = []
            id_field = self.id_field
            
            if id_field and id_field in [f.name() for f in self.layer.fields()]:
                for feat in self.layer.getFeatures():
                    try:
                        if str(feat[id_field]) in values:
                            to_delete.append(feat.id())
                    except Exception:
                        continue
            else:
                for feat in self.layer.getFeatures():
                    if str(feat.id()) in values:
                        to_delete.append(feat.id())
            
            if not to_delete:
                return True, None
            
            ok = self.layer.dataProvider().deleteFeatures(to_delete)
            if not ok:
                return False, self.tr("Deletion failed")
            
            self.layer.triggerRepaint()
            return True, None
        except Exception as e:
            return False, str(e)

    def apply_trimming_by_geometry(self, geom: QgsGeometry) -> Tuple[bool, Optional[str]]:
        """Trim by geometry"""
        try:
            if self.layer is None:
                return False, self.tr("Invalid layer")
            
            crs = self.layer.crs()
            wkb = self.layer.wkbType()
            uri = f"{QgsWkbTypes.displayString(wkb)}?crs={crs.authid()}"
            mem = QgsVectorLayer(uri, f"{self.layer.name()}_corrected", "memory")
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
                    new_g = g.difference(geom)
                except Exception:
                    new_g = g
                
                f = QgsFeature()
                f.setFields(mem.fields())
                for idx, fld in enumerate(self.layer.fields()):
                    f.setAttribute(idx, feat.attribute(fld.name()))
                
                try:
                    f.setGeometry(new_g)
                except Exception:
                    f.setGeometry(g)
                
                feats_out.append(f)
            
            mem_dp.addFeatures(feats_out)
            mem.updateExtents()
            QgsProject.instance().addMapLayer(mem)
            return True, None
        except Exception as e:
            return False, str(e)


def export_vector_layer(layer: QgsVectorLayer, path: str, driver: str = "GPKG", layer_name: str = None) -> Tuple[bool, Optional[str]]:
    """Export layer"""
    try:
        transform_context = QgsProject.instance().transformContext()
        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = driver
        opts.fileEncoding = "UTF-8"
        if layer_name:
            opts.layerName = layer_name
        
        res, err = QgsVectorFileWriter.writeAsVectorFormatV2(layer, path, transform_context, opts)
        if res == QgsVectorFileWriter.NoError:
            return True, None
        return False, self.tr("Error: {}").format(err)
    except Exception as e:
        return False, str(e)

def tr(message):
    """Get the translation for a string using Qt translation API."""
    from qgis.core import QgsApplication
    return QgsApplication.translate('LayerManager', message)