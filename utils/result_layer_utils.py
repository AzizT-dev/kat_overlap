# -*- coding: utf-8 -*-
"""
KAT Analysis – Result Layer Utilities
Layer creation utilities for analysis results

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QVariant

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes,
    QgsJsonUtils
)


class ResultLayerBuilder:
    """
    Builder class for creating result memory layers from analysis results.
    Handles dynamic geometry type detection and feature conversion.
    """
    
    @staticmethod
    def create_result_layer(dialog, results: List[Dict[str, Any]]) -> Optional[QgsVectorLayer]:
        """
        Create a memory layer with dynamic geometry type detection.
        
        Parameters:
        - dialog: UI dialog reference (for accessing da, crs_selector, log_message, etc.)
        - results: List of analysis results containing geometry_json
        
        Returns:
        - QgsVectorLayer if successful, None otherwise
        """
        try:
            # Remove old layer if exists
            try:
                if hasattr(dialog, "result_layer") and dialog.result_layer:
                    QgsProject.instance().removeMapLayer(dialog.result_layer.id())
            except Exception:
                pass

            # Determine CRS
            crs = QgsProject.instance().crs()
            if hasattr(dialog, "radio_crs_custom") and dialog.radio_crs_custom.isChecked():
                try:
                    crs = dialog.crs_selector.crs()
                except Exception:
                    pass

            layer_name = self.tr("Overlap_results_{}").format(len(results))

            # Define attribute fields
            fields = [
                QgsField("type", QVariant.String),
                QgsField("id_a", QVariant.String),
                QgsField("id_b", QVariant.String),
                QgsField("measure", QVariant.Double),
                QgsField("ratio_pct", QVariant.Double),
                QgsField("severity", QVariant.String),
                QgsField("area", QVariant.Double),
                QgsField("geom_type", QVariant.String)
            ]

            features_to_add = []
            detected_geom_types = set()
            geom_empty_count = 0

            # Prepare features and detect geometry types
            for idx, r in enumerate(results):
                geom = None
                geom_json = r.get("geometry_json")
                
                if geom_json:
                    try:
                        geom = QgsJsonUtils.geometryFromGeoJson(geom_json)
                        
                        if geom and not geom.isEmpty():
                            try:
                                type_name = QgsWkbTypes.displayString(geom.wkbType())
                                detected_geom_types.add(type_name)
                            except Exception:
                                detected_geom_types.add("Unknown")
                    except Exception:
                        try:
                            geom = QgsGeometry.fromWkt(str(geom_json))
                        except Exception:
                            geom = None

                if geom is None or geom.isEmpty():
                    geom_empty_count += 1
                    continue

                # Calculate area using dialog's distance area calculator if available
                area = 0.0
                try:
                    if hasattr(dialog, "da") and dialog.da and hasattr(dialog.da, "measureArea"):
                        area = float(dialog.da.measureArea(geom))
                    else:
                        area = float(geom.area())
                except Exception:
                    try:
                        area = float(geom.area())
                    except Exception:
                        area = 0.0

                if area <= 0:
                    geom_empty_count += 1
                    continue

                severity = r.get("severity", "")

                # Create feature with attributes
                feat = QgsFeature()
                feat.initAttributes(len(fields))
                
                feat.setAttribute(0, str(r.get("type", "")))
                feat.setAttribute(1, str(r.get("id_a_real") or r.get("id_a", "")))
                feat.setAttribute(2, str(r.get("id_b_real") or r.get("id_b", "")))
                
                try:
                    feat.setAttribute(3, float(r.get("measure", 0.0) or 0.0))
                except Exception:
                    feat.setAttribute(3, 0.0)

                try:
                    ratio_pct = r.get("ratio_percent")
                    if ratio_pct is None:
                        ratio = r.get("ratio", 0.0)
                        ratio_pct = float(ratio) * 100.0
                    feat.setAttribute(4, float(ratio_pct))
                except Exception:
                    feat.setAttribute(4, 0.0)

                feat.setAttribute(5, str(severity))
                feat.setAttribute(6, float(area))
                feat.setAttribute(7, "polygon")

                try:
                    feat.setGeometry(geom)
                except Exception as e:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("warning", self.tr("#{} unable to assign geometry: {}").format(idx, e))
                    geom_empty_count += 1
                    continue

                features_to_add.append(feat)

            # Choose layer geometry type dynamically based on detected types
            def choose_geom_type(detected_types):
                try:
                    if not detected_types:
                        return "GeometryCollection"
                    
                    s = {str(g).lower() for g in detected_types}
                    
                    if all(("polygon" in x or "multipolygon" in x) for x in s):
                        return "MultiPolygon"
                    
                    if all(("linestring" in x or "multilinestring" in x) for x in s):
                        return "MultiLineString"
                    
                    if all(("point" in x or "multipoint" in x) for x in s):
                        return "MultiPoint"
                    
                    return "GeometryCollection"
                except Exception as e:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("warning", self.tr("choose_geom_type error: {}, fallback GeometryCollection").format(e))
                    return "GeometryCollection"

            chosen_type = choose_geom_type(detected_geom_types)

            # Create memory layer
            uri = f"{chosen_type}?crs={crs.authid()}"
            result_layer = QgsVectorLayer(uri, layer_name, "memory")
            provider = result_layer.dataProvider()
            
            provider.addAttributes(fields)
            result_layer.updateFields()

            # Add features to layer
            if features_to_add:
                try:
                    result_layer.startEditing()
                    result_layer.addFeatures(features_to_add)
                    result_layer.commitChanges()
                    added_count = result_layer.featureCount()

                except Exception as e:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("Error adding features: {}").format(e))
                    
                    try:
                        if result_layer.isEditable():
                            result_layer.rollBack()
                    except Exception:
                        pass
                    
                    added_count = result_layer.featureCount()

                if added_count > 0:
                    result_layer.updateExtents()
                    QgsProject.instance().addMapLayer(result_layer)
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("info", self.tr("Layer created: {} ({} features)").format(layer_name, added_count))
                    
                    # Enable export button if available
                    if hasattr(dialog, "export_layer_btn") and dialog.export_layer_btn is not None:
                        dialog.export_layer_btn.setEnabled(True)
                    
                    return result_layer
                else:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("No features could be added to the layer!"))
                    return None
            else:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("warning", self.tr("No valid features to add: {} empty/invalid, total={}").format(geom_empty_count, len(results)))
                return None

        except Exception as e:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Error creating results layer: {}").format(e))
            return None