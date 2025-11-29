# -*- coding: utf-8 -*-
"""
KAT Analysis – Results Handler
Results table population, layer creation, and export utilities

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os
import csv
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox, QComboBox
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
    QgsWkbTypes, QgsJsonUtils, QgsVectorFileWriter, QgsCoordinateTransformContext
)
from .utils import log_message, tr, ensure_parent_dir, normalize_result


# ===============ANALYSIS TYPE DETECTION====================

def detect_analysis_type(results: List[Dict[str, Any]]) -> str:
    """Detect analysis type from results content."""
    if not results:
        return 'polygon'
    
    anomaly_types = set(r.get('type', r.get('anomaly', '')) for r in results)
    
    cadastral_types = {'orphan_point', 'orphan_polygon', 'vertex_count_mismatch', 
                       'point_vertex_mismatch', 'shared_vertex_missing'}
    if anomaly_types & cadastral_types:
        return 'point_polygon'
    
    if 'point_proximity' in anomaly_types:
        return 'point'
    
    line_types = {'line_self_intersection', 'line_overlap', 'line_dangle'}
    if anomaly_types & line_types:
        return 'line'
    
    return 'polygon'

def normalize_severity(raw):
    """Normalize various severity text values to canonical keys:
    returns one of: 'critical', 'high', 'moderate', 'low'
    """
    if raw is None:
        return 'low'
    s = str(raw).strip().lower()
    if 'crit' in s:
        return 'critical'
    if 'high' in s:
        return 'high'
    if 'mod' in s:
        return 'moderate'
    return 'low'

# ==================RESULTS TABLE MANAGER=====================

class ResultsTableManager:
    """Manages results table population and interactions"""
    
    @staticmethod
    def populate_table(table: QTableWidget, results: List[Dict[str, Any]], 
                      analysis_type: str = None):
        """
        Populate QTableWidget with analysis results.
        Uses a unified 8-column layout for all analysis types.
        """
        try:
            log_message('info', f"Populating table with {len(results)} results")
            
            if not results:
                log_message('warning', "No results to populate")
                return
            
            # Auto-detect analysis type
            if analysis_type is None:
                analysis_type = detect_analysis_type(results)
            
            log_message('info', f"Detected analysis type: {analysis_type}")
            
            # Normalize results
            normalized = [normalize_result(r) for r in results]
            
            # Configure headers based on analysis type
            if analysis_type == 'point_polygon':
                headers = ["", "Anomaly", "Parcel ID", "Details", "Count", "Severity", "Action"]
            elif analysis_type == 'point':
                headers = ["", "Anomaly", "ID A", "ID B", "Distance (m)", "Severity", "Action"]
            elif analysis_type == 'line':
                headers = ["", "Anomaly", "ID A", "ID B", "Distance (m)", "Severity", "Action"]
            else:  # polygon
                headers = ["", "Anomaly", "ID A", "ID B", "Area (m²)", "Ratio (%)", "Severity", "Action"]
            
            # Setup table
            table.setRowCount(0)
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(normalized))
            
            log_message('info', f"Table setup: {len(headers)} cols, {len(normalized)} rows")
            
            # Populate each row
            for row_idx, result in enumerate(normalized):
                col = 0
                
                # Column 0: Checkbox
                chk = QCheckBox()
                table.setCellWidget(row_idx, col, chk)
                col += 1
                
                # Column 1: Anomaly type
                anom_type = str(result.get('type', result.get('anomaly', '')))
                table.setItem(row_idx, col, QTableWidgetItem(anom_type))
                col += 1
                
                # Column 2: ID A / Parcel ID
                id_a = str(result.get('id_a_real', result.get('id_a', '')))
                table.setItem(row_idx, col, QTableWidgetItem(id_a))
                col += 1
                
                # Column 3: ID B / Details
                id_b = str(result.get('id_b_real', result.get('id_b', '')))
                table.setItem(row_idx, col, QTableWidgetItem(id_b))
                col += 1
                
                # Column 4: Measure (Area/Distance/Count)
                measure = result.get('measure', 0.0)
                try:
                    if analysis_type == 'point_polygon':
                        measure_str = str(int(measure)) if measure else "-"
                    else:
                        measure_str = f"{float(measure):.3f}"
                except:
                    measure_str = str(measure)
                table.setItem(row_idx, col, QTableWidgetItem(measure_str))
                col += 1
                
                # Column 5: Ratio (only for polygon type) or Severity
                if analysis_type == 'polygon':
                    ratio = result.get('ratio_percent', 0.0)
                    try:
                        ratio_str = f"{float(ratio):.1f}%"
                    except:
                        ratio_str = "0.0%"
                    table.setItem(row_idx, col, QTableWidgetItem(ratio_str))
                    col += 1
                
                # Severity column
                severity = normalize_severity(result.get('severity', 'low'))
                sev_item = QTableWidgetItem(severity)
                sev_item.setForeground(ResultsTableManager._get_severity_color(severity))
                table.setItem(row_idx, col, sev_item)
                col += 1
                
                # Action column (last)
                action_combo = QComboBox()
                action_combo.addItems(["Validate", "Delete"])
                table.setCellWidget(row_idx, col, action_combo)
            
            table.resizeColumnsToContents()
            log_message('info', f"Table populated: {table.rowCount()} rows visible")
            
        except Exception as e:
            import traceback
            log_message('error', f"Table population error: {e}\n{traceback.format_exc()}")
    
    @staticmethod
    def _get_severity_color(severity: str) -> QColor:
        """Get color for severity level"""
        s = severity.lower() if severity else 'low'
        colors = {
            'critical': QColor("#e74c3c"),
            'high': QColor("#e67e22"),
            'moderate': QColor("#f39c12"),
            'low': QColor("#95a5a6")
        }
        return colors.get(s, QColor("#2c3e50"))
    
    @staticmethod
    def get_checked_rows(table: QTableWidget) -> List[int]:
        """Get indices of checked rows"""
        checked = []
        for row in range(table.rowCount()):
            widget = table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                checked.append(row)
        return checked
    
    @staticmethod
    def get_action_for_row(table: QTableWidget, row: int) -> str:
        """Get action selected for a row"""
        last_col = table.columnCount() - 1
        widget = table.cellWidget(row, last_col)
        if isinstance(widget, QComboBox):
            return widget.currentText()
        return "Validate"

# ==================RESULT LAYER BUILDER===============

class ResultLayerBuilder:
    """Creates memory layers from analysis results"""
    
    @staticmethod
    def create_result_layer(results: List[Dict[str, Any]], 
                           crs=None, layer_name: str = None) -> Optional[QgsVectorLayer]:
        """Create a memory layer with results"""
        try:
            if not results:
                log_message('warning', "No results to create layer")
                return None
            
            if crs is None:
                crs = QgsProject.instance().crs()
            
            analysis_type = detect_analysis_type(results)
            
            if not layer_name:
                type_names = {
                    'polygon': "Overlap_results",
                    'point_polygon': "Cadastral_topology_results",
                    'point': "Point_proximity_results",
                    'line': "Line_topology_results"
                }
                layer_name = f"temp_{type_names.get(analysis_type, 'Unknown')}"
            
            # Collect valid geometries
            geom_types = set()
            valid_features = []
            
            for result in results:
                geom = ResultLayerBuilder._extract_geometry(result)
                if geom and not geom.isEmpty():
                    try:
                        type_str = QgsWkbTypes.displayString(geom.wkbType())
                        geom_types.add(type_str)
                        valid_features.append((result, geom))
                    except:
                        continue
            
            log_message('info', f"Valid geometries: {len(valid_features)}")
            
            if not valid_features:
                log_message('warning', "No valid geometries in results")
                return None
            
            chosen_type = ResultLayerBuilder._choose_geometry_type(geom_types)
            
            uri = f"{chosen_type}?crs={crs.authid()}"
            layer = QgsVectorLayer(uri, layer_name, "memory")
            
            if not layer.isValid():
                log_message('error', "Failed to create memory layer")
                return None
            
            # Add fields
            fields = [
                QgsField("type", QVariant.String),
                QgsField("id_a", QVariant.String),
                QgsField("id_b", QVariant.String),
                QgsField("measure", QVariant.Double),
                QgsField("severity", QVariant.String),
            ]
            
            if analysis_type == 'polygon':
                fields.append(QgsField("ratio_pct", QVariant.Double))
                fields.append(QgsField("area", QVariant.Double))
            
            provider = layer.dataProvider()
            provider.addAttributes(fields)
            layer.updateFields()
            
            # Add features
            features_to_add = []
            for result, geom in valid_features:
                feat = QgsFeature(layer.fields())
                feat.setGeometry(geom)
                
                feat.setAttribute('type', str(result.get('type', '')))
                feat.setAttribute('id_a', str(result.get('id_a_real', '')))
                feat.setAttribute('id_b', str(result.get('id_b_real', '')))
                
                try:
                    feat.setAttribute('measure', float(result.get('measure', 0.0)))
                except:
                    feat.setAttribute('measure', 0.0)
                    
                feat.setAttribute('severity', str(result.get('severity', 'Low')))
                
                if analysis_type == 'polygon':
                    try:
                        feat.setAttribute('ratio_pct', float(result.get('ratio_percent', 0.0)))
                        feat.setAttribute('area', float(result.get('area_m2', 0.0)))
                    except:
                        pass
                
                features_to_add.append(feat)
            
            provider.addFeatures(features_to_add)
            layer.updateExtents()
            
            QgsProject.instance().addMapLayer(layer)
            log_message('info', f"Result layer created: {layer.name()} ({len(features_to_add)} features)")
            
            return layer
            
        except Exception as e:
            import traceback
            log_message('error', f"Layer creation failed: {e}\n{traceback.format_exc()}")
            return None
    
    @staticmethod
    def _extract_geometry(result: Dict[str, Any]) -> Optional[QgsGeometry]:
        """Extract geometry from result dictionary"""
        geom_json = result.get('geometry_json')
        if geom_json:
            try:
                geom = QgsJsonUtils.geometryFromGeoJson(geom_json)
                if geom and not geom.isEmpty():
                    return geom
            except:
                pass
        
        geom_wkt = result.get('geometry_wkt')
        if geom_wkt:
            try:
                geom = QgsGeometry.fromWkt(str(geom_wkt))
                if geom and not geom.isEmpty():
                    return geom
            except:
                pass
        
        overlap_geom = result.get('overlap_geometry')
        if overlap_geom and isinstance(overlap_geom, QgsGeometry):
            return overlap_geom
        
        return None
    
    @staticmethod
    def _choose_geometry_type(geom_types: set) -> str:
        """Choose appropriate layer geometry type"""
        if not geom_types:
            return "GeometryCollection"
        
        types_lower = {str(t).lower() for t in geom_types}
        
        if all('polygon' in t or 'multipolygon' in t for t in types_lower):
            return "MultiPolygon"
        elif all('linestring' in t or 'multilinestring' in t for t in types_lower):
            return "MultiLineString"
        elif all('point' in t or 'multipoint' in t for t in types_lower):
            return "MultiPoint"
        else:
            return "GeometryCollection"

# ====================EXPORT UTILITIES=====================

class ResultExporter:
    """Export results to various formats"""
    
    @staticmethod
    def export_to_csv(table: QTableWidget, csv_path: str, 
                     checked_only: bool = True, delimiter: str = ";") -> Tuple[bool, Optional[str]]:
        """Export table rows to CSV"""
        try:
            ensure_parent_dir(csv_path)
            
            headers = []
            for col in range(1, table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"col_{col}")
            
            rows_to_export = []
            for row in range(table.rowCount()):
                if checked_only:
                    widget = table.cellWidget(row, 0)
                    if not (isinstance(widget, QCheckBox) and widget.isChecked()):
                        continue
                
                row_data = []
                for col in range(1, table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        widget = table.cellWidget(row, col)
                        if isinstance(widget, QComboBox):
                            row_data.append(widget.currentText())
                        else:
                            row_data.append("")
                rows_to_export.append(row_data)
            
            if not rows_to_export:
                return False, "No rows to export"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(headers)
                writer.writerows(rows_to_export)
            
            log_message('info', f"CSV exported: {csv_path}")
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def export_layer_to_file(layer: QgsVectorLayer, output_path: str,
                            driver: str = "GPKG") -> Tuple[bool, Optional[str]]:
        """Export layer to file"""
        try:
            ensure_parent_dir(output_path)
            
            if not driver:
                ext = os.path.splitext(output_path)[1].lower()
                driver = {'.gpkg': 'GPKG', '.shp': 'ESRI Shapefile', 
                         '.geojson': 'GeoJSON', '.json': 'GeoJSON'}.get(ext, 'GPKG')
            
            transform_context = QgsProject.instance().transformContext()
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = driver
            options.fileEncoding = "UTF-8"
            
            result, error = QgsVectorFileWriter.writeAsVectorFormatV2(
                layer, output_path, transform_context, options
            )
            
            if result == QgsVectorFileWriter.NoError:
                return True, None
            return False, str(error)
                
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def export_to_xlsx(table: QTableWidget, xlsx_path: str,
                      checked_only: bool = True) -> Tuple[bool, Optional[str]]:
        """Export table to XLSX"""
        try:
            from openpyxl import Workbook
        except ImportError:
            return False, "openpyxl not installed"
        
        try:
            ensure_parent_dir(xlsx_path)
            wb = Workbook()
            ws = wb.active
            ws.title = "Results"
            
            headers = []
            for col in range(1, table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"col_{col}")
            ws.append(headers)
            
            exported_count = 0
            for row in range(table.rowCount()):
                if checked_only:
                    widget = table.cellWidget(row, 0)
                    if not (isinstance(widget, QCheckBox) and widget.isChecked()):
                        continue
                
                row_data = []
                for col in range(1, table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        widget = table.cellWidget(row, col)
                        if isinstance(widget, QComboBox):
                            row_data.append(widget.currentText())
                        else:
                            row_data.append("")
                ws.append(row_data)
                exported_count += 1
            
            if exported_count == 0:
                return False, "No rows to export"
            
            wb.save(xlsx_path)
            return True, None
            
        except Exception as e:
            return False, str(e)
