# -*- coding: utf-8 -*-
"""
KAT Analysis – Layer Manager  
Layer operations, corrections, merging, export (texts in English)

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os, traceback
from typing import Dict, Any, List, Optional, Tuple
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsField, QgsFields, QgsProject, QgsVectorFileWriter,
    QgsWkbTypes, QgsGeometry, QgsFeatureRequest, QgsCoordinateTransformContext, QgsSymbol,
    QgsRendererRange, QgsGraduatedSymbolRenderer, QgsApplication
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

LOG_TAG = "kat_overlap.layer_manager"


# ---------------------------------------------------------------------------
# TRANSLATION UTILITY
# ---------------------------------------------------------------------------
def tr(message: str) -> str:
    """Get the translation for a string using Qt translation API (English texts)."""
    return QgsApplication.translate('LayerManager', message)


# ========================================================================
# ROBUST MULTI-LAYER FUSION
# ========================================================================

def check_layers_compatibility(layers: List[QgsVectorLayer]) -> Tuple[bool, Optional[str]]:
    """Check relaxed compatibility: same geometry type only."""
    if not layers or len(layers) < 2:
        return True, None

    first_geom_type = layers[0].geometryType()
    for layer in layers[1:]:
        if layer.geometryType() != first_geom_type:
            return False, tr("Incompatible geometry types")

    return True, None


def merge_layers_to_temp(layers: List[QgsVectorLayer],
                         merge_name: str = "merged_temp") -> Tuple[Optional[QgsVectorLayer], Optional[str]]:
    """Merge multiple layers of the same type into a temporary memory layer."""
    if not layers:
        return None, tr("No layers provided")

    if len(layers) < 2:
        return layers[0], None

    try:
        ok, msg = check_layers_compatibility(layers)
        if not ok:
            return None, msg

        # Find common fields across all layers
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

        # Add common fields + traceability
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
                for field_name in common_fields.keys():
                    try:
                        idx = temp_layer.fields().indexOf(field_name)
                        if idx >= 0:
                            new_feat.setAttribute(idx, feature[field_name])
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
            return None, tr("No valid features to merge")

        provider.addFeatures(all_features)
        temp_layer.updateExtents()
        return temp_layer, None

    except Exception as e:
        return None, tr("Merge error: {}").format(str(e))


# ========================================================================
# LAYER CORRECTION
# ========================================================================

class LayerCorrector:
    """Apply deletions and geometry trimming."""

    def __init__(self, layer: QgsVectorLayer, id_field: Optional[str]):
        self.layer = layer
        self.id_field = id_field

    def apply_corrections_by_values_or_fids(self, values: List[str]) -> Tuple[bool, Optional[str]]:
        """Delete features matching values or feature IDs."""
        try:
            if self.layer is None:
                return False, tr("Invalid layer")

            to_delete = []
            id_field = self.id_field
            if id_field and id_field in [f.name() for f in self.layer.fields()]:
                for feat in self.layer.getFeatures():
                    if str(feat[id_field]) in values:
                        to_delete.append(feat.id())
            else:
                for feat in self.layer.getFeatures():
                    if str(feat.id()) in values:
                        to_delete.append(feat.id())

            if not to_delete:
                return True, None

            ok = self.layer.dataProvider().deleteFeatures(to_delete)
            if not ok:
                return False, tr("Deletion failed")

            self.layer.triggerRepaint()
            return True, None
        except Exception as e:
            return False, str(e)

    def apply_trimming_by_geometry(self, geom: QgsGeometry) -> Tuple[bool, Optional[str]]:
        """Trim layer features using a geometry difference."""
        try:
            if self.layer is None:
                return False, tr("Invalid layer")

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


# ========================================================================
# SYMBOLOGY BY SEVERITY
# ========================================================================

def apply_symbology_by_severity(layer: QgsVectorLayer):
    """Apply symbology ranges based on severity (English labels)."""
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

        # Create color ranges
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
    except Exception:
        pass


# ========================================================================
# VECTOR LAYER EXPORT
# ========================================================================

def export_vector_layer(layer: QgsVectorLayer, path: str,
                        driver: str = "GPKG", layer_name: str = None) -> Tuple[bool, Optional[str]]:
    """Export vector layer to disk."""
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
        return False, tr("Export error: {}").format(err)
    except Exception as e:
        return False, str(e)
