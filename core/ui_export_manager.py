# -*- coding: utf-8 -*-
"""
KAT Analysis – UI Export Manager
Export dialog handlers for results, entities and layers

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os, sys
import csv
from typing import Optional, Dict, Set
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QCheckBox

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsVectorFileWriter,
    QgsFeature, QgsGeometry, QgsWkbTypes
)

# Plugin path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
try:
    from utils.result_exporter import (
        export_checked_table_rows_to_csv,
        export_features_by_id_to_file
    )
except ImportError:
    export_checked_table_rows_to_csv = None
    export_features_by_id_to_file = None


class UIExportManager:
    """
    Manages all export operations from UI: CSV, entities, result layer.
    """
    
    @staticmethod
    def export_selected_entities_by_id(dialog, use_action_supprimer_only: bool = False):
        """
        Export selected entities by their IDs to separate files per layer.
        
        Parameters:
        - dialog: UI dialog reference
        - use_action_supprimer_only: If True, only export rows marked with "Supprimer" action
        """
        if not hasattr(dialog, '_original_results') or not dialog._original_results:
            QMessageBox.information(dialog, self.tr("Export entities"), self.tr("No results available."))
            return
        
        # Collect layer IDs and feature IDs
        layer_to_ids: Dict[str, Set[str]] = {}
        
        for idx, res in enumerate(dialog._original_results):
            if idx >= dialog.results_table.rowCount():
                continue
            
            # Check action combo if filtering by "Supprimer"
            if use_action_supprimer_only:
                combo = dialog.results_table.cellWidget(idx, 7)
                action = combo.currentText() if combo else self.tr("Valider")
                if action != self.tr("Supprimer"):
                    continue
            
            # Extract IDs from layer_a and layer_b
            for side in ["layer_a", "layer_b"]:
                try:
                    side_info = res.get(side, {})
                    if not isinstance(side_info, dict):
                        continue
                    
                    lid = side_info.get("layer_id") or (
                        side_info.get("layer").id() 
                        if isinstance(side_info.get("layer"), QgsVectorLayer) 
                        else side_info.get("layer_id")
                    )
                    
                    # Try real id attr first
                    idval = res.get("id_a_real") if side == "layer_a" else res.get("id_b_real")
                    if not idval:
                        # Fallback to feature id
                        feat = side_info.get("feature")
                        if feat is not None:
                            idval = str(feat.id())
                    
                    if lid and idval is not None:
                        layer_to_ids.setdefault(lid, set()).add(str(idval))
                
                except Exception as e:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("Error reading line {} for entity export: {}").format(idx, e))
        
        if not layer_to_ids:
            QMessageBox.information(dialog, self.tr("Export entities"), self.tr("No entities identified for export."))
            return
        
        # For each layer, ask for a file and export
        for lid, ids in layer_to_ids.items():
            layer = QgsProject.instance().mapLayer(lid)
            if not layer:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("warning", self.tr("Layer not found: {}").format(lid))
                continue
            
            default = os.path.join(os.path.expanduser("~"), f"{layer.name()}_subset.gpkg")
            path, _ = QFileDialog.getSaveFileName(
                dialog,
                self.tr("Export entities - {}").format(layer.name()),
                default,
                self.tr("GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)"))
            
            if not path:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("Export cancelled for {}").format(layer.name()))
                continue
            
            if export_features_by_id_to_file is not None:
                try:
                    id_field = dialog.id_fields.get(
                        lid,
                        layer.fields().names()[0] if layer.fields().count() > 0 else ''
                    )
                    
                    ok, msg = export_features_by_id_to_file(
                        layer,
                        id_field,
                        list(ids),
                        path,
                        driver_name="GPKG",
                        out_layer_name=None
                    )
                    
                    if ok:
                        if hasattr(dialog, '_log_message'):
                            dialog._log_message("info", self.tr("Entity export for {} successful: {}").format(layer.name(), path))
                    else:
                        if hasattr(dialog, '_log_message'):
                            dialog._log_message("error", self.tr("Entity export for {} failed: {}").format(layer.name(), msg))
                        QMessageBox.warning(dialog, self.tr("Export entities"), self.tr("Export failed for {}: {}").format(layer.name(), msg))
                
                except Exception as e:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("Entity export exception for {}: {}").format(layer.name(), e))
                    QMessageBox.warning(dialog, self.tr("Export entities"), self.tr("Export exception for {}: {}").format(layer.name(), e))
            else:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("error", self.tr("export_features_by_id_to_file function not available."))
                QMessageBox.warning(dialog, self.tr("Export entities"), self.tr("Export impossible: utility missing."))
    
    @staticmethod
    def export_results(dialog):
        """
        Export checked rows from results table to CSV or TXT.
        
        Parameters:
        - dialog: UI dialog reference
        """
        # Check if any row is checked
        any_checked = False
        for r in range(dialog.results_table.rowCount()):
            w = dialog.results_table.cellWidget(r, 0)
            if isinstance(w, QCheckBox) and w.isChecked():
                any_checked = True
                break
        
        if not any_checked:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("warning", self.tr("No checked rows to export."))
            QMessageBox.information(dialog, self.tr("Export"), self.tr("Check at least one row before exporting."))
            return
        
        default = os.path.join(os.path.expanduser("~"), "kat_overlap_selection.csv")
        path, _ = QFileDialog.getSaveFileName(
            dialog,
            self.tr("Export (checked rows)"),
            default,
            self.tr("CSV files (*.csv);;TXT files (*.txt)"))
        
        if not path:
            return
        
        delim = "\t" if path.lower().endswith(".txt") else ";"
        
        # Try using utility function if available
        if export_checked_table_rows_to_csv is not None:
            try:
                ok, msg = export_checked_table_rows_to_csv(
                    dialog.results_table,
                    path,
                    header_map=None,
                    delimiter=delim
                )
                
                if ok:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("info", self.tr("Export (checked rows) successful: {}").format(path))
                    QMessageBox.information(dialog, self.tr("Export"), self.tr("Export successful: {}").format(path))
                else:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("Export (checked rows) failed: {}").format(msg))
                    QMessageBox.warning(dialog, self.tr("Export"), self.tr("Export failed: {}").format(msg))
            
            except Exception as e:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("error", self.tr("Export failed (utility exception): {}").format(e))
                QMessageBox.warning(dialog, self.tr("Export"), self.tr("Export failed: {}").format(e))
            return
        
        # Fallback: manual CSV export
        try:
            headers = [
                dialog.results_table.horizontalHeaderItem(c).text()
                for c in range(dialog.results_table.columnCount())
            ]
            
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh, delimiter=delim)
                writer.writerow(headers)
                
                for r in range(dialog.results_table.rowCount()):
                    w = dialog.results_table.cellWidget(r, 0)
                    checked = (isinstance(w, QCheckBox) and w.isChecked())
                    
                    if not checked:
                        continue
                    
                    row_vals = []
                    for c in range(dialog.results_table.columnCount()):
                        if c == 7:  # Action column
                            combo = dialog.results_table.cellWidget(r, c)
                            row_vals.append(combo.currentText() if combo else "")
                        else:
                            it = dialog.results_table.item(r, c)
                            row_vals.append(it.text() if it else "")
                    
                    writer.writerow(row_vals)
            
            if hasattr(dialog, '_log_message'):
                dialog._log_message("info", self.tr("Export successful: {}").format(path))
            QMessageBox.information(dialog, self.tr("Export"), self.tr("Export successful: {}").format(path))
        
        except Exception as e:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Export failed: {}").format(e))
            QMessageBox.warning(dialog, self.tr("Export"), self.tr("Export failed: {}").format(e))
    
    @staticmethod
    def export_result_layer(dialog):
        """
        Export the result layer to disk with GeometryCollection handling for Shapefile.
        
        Parameters:
        - dialog: UI dialog reference
        """
        if not hasattr(dialog, 'result_layer') or not dialog.result_layer:
            QMessageBox.information(dialog, self.tr("Export layer"), self.tr("No result layer present."))
            return
        
        default = os.path.join(os.path.expanduser("~"), f"{dialog.result_layer.name()}.gpkg")
        path, _ = QFileDialog.getSaveFileName(
            dialog,
            self.tr("Export result layer"),
            default,
            self.tr("GeoPackage (*.gpkg);;ESRI Shapefile (*.shp);;GeoJSON (*.geojson)"))
        
        if not path:
            return
        
        try:
            transform_context = QgsProject.instance().transformContext()
            layer_to_export = dialog.result_layer
            ext = os.path.splitext(path)[1].lower()
            
            # Check if layer has GeometryCollection
            is_geometry_collection = False
            geom_type = dialog.result_layer.wkbType()
            
            if (QgsWkbTypes.flatType(geom_type) == QgsWkbTypes.GeometryCollection or
                "GeometryCollection" in QgsWkbTypes.displayString(geom_type)):
                is_geometry_collection = True
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("⚠️ GeometryCollection detected"))
            
            # Convert GeometryCollection to MultiPolygon for Shapefile
            if ext == ".shp" and is_geometry_collection:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("Converting GeometryCollection → MultiPolygon for Shapefile..."))
                
                uri = f"MultiPolygon?crs={dialog.result_layer.crs().authid()}"
                temp_layer = QgsVectorLayer(uri, "temp_shp_export", "memory")
                temp_layer.startEditing()
                provider = temp_layer.dataProvider()
                provider.addAttributes(dialog.result_layer.fields())
                temp_layer.updateFields()
                
                feats = []
                skipped = 0
                
                for feat in dialog.result_layer.getFeatures():
                    new_feat = QgsFeature(temp_layer.fields())
                    
                    # Copy attributes
                    for i, field in enumerate(dialog.result_layer.fields()):
                        new_feat.setAttribute(i, feat.attribute(field.name()))
                    
                    # Process geometry
                    geom = feat.geometry()
                    if geom and not geom.isNull():
                        flat_type = QgsWkbTypes.flatType(geom.wkbType())
                        
                        if flat_type == QgsWkbTypes.GeometryCollection:
                            # Extract polygons from collection
                            polygons = []
                            
                            for part in geom.asGeometryCollection():
                                if part.type() == QgsWkbTypes.PolygonGeometry:
                                    if part.isMultipart():
                                        polygons.extend(part.asMultiPolygon())
                                    else:
                                        polygons.append(part.asPolygon())
                            
                            if polygons:
                                multi_geom = QgsGeometry.fromMultiPolygonXY(polygons)
                                new_feat.setGeometry(multi_geom)
                            else:
                                skipped += 1
                                continue
                        
                        elif geom.type() == QgsWkbTypes.PolygonGeometry:
                            new_feat.setGeometry(geom)
                        else:
                            skipped += 1
                            continue
                    else:
                        skipped += 1
                        continue
                    
                    feats.append(new_feat)
                
                provider.addFeatures(feats)
                temp_layer.commitChanges()
                temp_layer.updateExtents()
                layer_to_export = temp_layer
                
                if skipped > 0 and hasattr(dialog, '_log_message'):
                    dialog._log_message("warning", self.tr("⚠️ {} non-polygonal entities ignored").format(skipped))
                
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("✅ {} entities converted for Shapefile export").format(len(feats)))
            
            # Configure writer options
            opts = QgsVectorFileWriter.SaveVectorOptions()
            if ext == ".gpkg":
                opts.driverName = "GPKG"
            elif ext == ".shp":
                opts.driverName = "ESRI Shapefile"
                opts.layerOptions = ["ENCODING=UTF-8"]
            elif ext in (".geojson", ".json"):
                opts.driverName = "GeoJSON"
            else:
                opts.driverName = "GPKG"
            
            opts.fileEncoding = "UTF-8"
            
            # Write layer
            res, err = QgsVectorFileWriter.writeAsVectorFormatV2(
                layer_to_export,
                path,
                transform_context,
                opts
            )
            
            if res == QgsVectorFileWriter.NoError:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("✅ Layer exported: {}").format(path))
                QMessageBox.information(dialog, self.tr("Export"), self.tr("✅ Layer exported successfully!\n\n{}").format(path))
            else:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("error", self.tr("❌ Export failed: {}").format(err))
                QMessageBox.warning(dialog, self.tr("Export"), self.tr("❌ Export failed:\n{}").format(err))
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("❌ Export failed: {}").format(e))
                dialog._log_message("debug", error_detail)
            QMessageBox.warning(dialog, self.tr("Export"), self.tr("❌ Export failed:\n{}").format(e))

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API."""
        from qgis.core import QgsApplication
        return QgsApplication.translate('UIExportManager', message)