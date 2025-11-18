# -*- coding: utf-8 -*-
"""
KAT Analysis – Result Exporter
Export utilities for analysis results

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os
import csv
from typing import Optional, List, Dict, Iterable, Tuple

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext,
    QgsFeatureRequest,
    Qgis
)

LOG_TAG = "kat_overlap.exporter"


# ============================================================================
# LOGGING HELPER
# ============================================================================

def _log(level: int, message: str) -> None:
    """
    Log a message to QGIS message log.
    Levels: Qgis.Info, Qgis.Warning, Qgis.Critical
    """
    try:
        from qgis.core import QgsMessageLog
        QgsMessageLog.logMessage(message, LOG_TAG, level)
    except Exception:
        # Fallback: print if QGIS not available
        print(f"[{LOG_TAG}] {message}")


# ============================================================================
# UTILITIES
# ============================================================================

def ensure_parent_dir(path: str) -> None:
    """Create parent directories if they don't exist."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


# ============================================================================
# CSV EXPORT FROM QTABLEWIDGET
# ============================================================================

def export_checked_table_rows_to_csv(table: QTableWidget,
                                     csv_path: str,
                                     header_map: Optional[Dict[int, str]] = None,
                                     delimiter: str = ";") -> Tuple[bool, Optional[str]]:
    """
    Export only checked rows from a QTableWidget to CSV.

    Parameters:
    - table: QTableWidget where selection checkbox is expected in column 0.
    - csv_path: destination file path
    - header_map: optional mapping col_index->csv_name. If None, header labels are used.
    - delimiter: CSV delimiter (default: ";")

    Returns:
    - (True, None) on success or (False, error_message) on failure.
    """
    if table is None or not isinstance(table, QTableWidget):
        return False, self.tr("Invalid table.")

    ensure_parent_dir(csv_path)

    # Build headers
    col_count = table.columnCount()
    headers = []
    for c in range(col_count):
        if header_map and c in header_map:
            headers.append(header_map[c])
        else:
            h = table.horizontalHeaderItem(c)
            headers.append(h.text() if h else f"col_{c}")

    rows = []
    for r in range(table.rowCount()):
        checked = False
        # Try widget checkbox in col 0
        try:
            w = table.cellWidget(r, 0)
            if isinstance(w, QCheckBox):
                checked = w.isChecked()
        except Exception:
            checked = False
        # Try item check state fallback
        if not checked:
            it = table.item(r, 0)
            if isinstance(it, QTableWidgetItem):
                try:
                    checked = (it.checkState() == Qt.Checked or it.text().strip() == "✓")
                except Exception:
                    checked = False
        if not checked:
            continue

        row = []
        for c in range(col_count):
            it = table.item(r, c)
            if it:
                row.append(it.text())
            else:
                widget = table.cellWidget(r, c)
                text = ""
                if widget is not None and hasattr(widget, "text"):
                    try:
                        text = widget.text()
                    except Exception:
                        text = ""
                row.append(text)
        rows.append(row)

    if not rows:
        _log(Qgis.Warning, self.tr("No checked rows to export."))
        return False, self.tr("No checked rows.")

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=delimiter)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
        _log(Qgis.Info, self.tr("CSV export successful: {}").format(csv_path))
        return True, None
    except Exception as e:
        msg = self.tr("CSV write error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg


# ============================================================================
# VECTOR LAYER EXPORT (GPKG/Shapefile/GeoJSON)
# ============================================================================

def export_layer_to_file(layer: QgsVectorLayer, out_path: str,
                         driver_name: Optional[str] = None,
                         layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Export a QgsVectorLayer to out_path using the modern API with fallback.

    Parameters:
    - layer: QgsVectorLayer to export
    - out_path: destination file path
    - driver_name: if None, deduced from file extension (GPKG, ESRI Shapefile, GeoJSON, etc.)
    - layer_name: optional layer name in output file

    Returns:
    - (success: bool, error_message: Optional[str])
    """
    if layer is None or not isinstance(layer, QgsVectorLayer):
        return False, self.tr("Invalid layer.")

    ensure_parent_dir(out_path)

    # Deduce driver if not provided
    if not driver_name:
        ext = os.path.splitext(out_path)[1].lower()
        if ext in (".gpkg",):
            driver_name = "GPKG"
        elif ext in (".shp",):
            driver_name = "ESRI Shapefile"
        elif ext in (".geojson", ".json"):
            driver_name = "GeoJSON"
        else:
            driver_name = "GPKG"

    transform_context = QgsProject.instance().transformContext()
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = driver_name
    opts.fileEncoding = "UTF-8"
    if layer_name:
        try:
            opts.layerName = layer_name
        except Exception:
            pass

    try:
        res, err = QgsVectorFileWriter.writeAsVectorFormatV2(layer, out_path, transform_context, opts)
        if res == QgsVectorFileWriter.NoError:
            _log(Qgis.Info, self.tr("{} export successful: {}").format(driver_name, out_path))
            return True, None
        msg = self.tr("Write error (code {}): {}").format(res, err)
        _log(Qgis.Critical, msg)
        return False, msg
    except AttributeError:
        # Fallback to older API
        try:
            err_code = QgsVectorFileWriter.writeAsVectorFormat(layer, out_path, "UTF-8",
                                                               transform_context, driver_name)
            if err_code == 0 or err_code == QgsVectorFileWriter.NoError:
                _log(Qgis.Info, self.tr("{} export successful (legacy API): {}").format(driver_name, out_path))
                return True, None
            msg = self.tr("Old API error (code {})").format(err_code)
            _log(Qgis.Critical, msg)
            return False, msg
        except Exception as e:
            msg = self.tr("Fallback export failed: {}").format(e)
            _log(Qgis.Critical, msg)
            return False, msg
    except Exception as e:
        msg = self.tr("Export error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg


def export_layer_to_gpkg(layer: QgsVectorLayer, out_gpkg_path: str,
                         layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Convenience wrapper to export a layer to GeoPackage format.
    
    Parameters:
    - layer: QgsVectorLayer to export
    - out_gpkg_path: destination .gpkg file path
    - layer_name: optional layer name in GeoPackage
    
    Returns:
    - (success: bool, error_message: Optional[str])
    """
    return export_layer_to_file(layer, out_gpkg_path, driver_name="GPKG", layer_name=layer_name)


# ============================================================================
# EXPORT SUBSET OF FEATURES BY ID
# ============================================================================

def export_features_by_id_to_file(layer: QgsVectorLayer,
                                  id_field: str,
                                  ids: Iterable,
                                  out_path: str,
                                  driver_name: str = "GPKG",
                                  out_layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Export only features whose id_field value is in ids to out_path.
    Useful to export selected results into a GeoPackage or shapefile.

    Parameters:
    - layer: source QgsVectorLayer
    - id_field: attribute field name to filter on
    - ids: iterable of id values to export
    - out_path: destination file path
    - driver_name: output driver (default: "GPKG")
    - out_layer_name: optional layer name in output

    Returns:
    - (success: bool, error_message: Optional[str])
    """
    if layer is None:
        return False, self.tr("Invalid layer.")

    ensure_parent_dir(out_path)
    ids_set = set(str(i) for i in ids)

    # Create temporary memory layer with same schema
    geom_wkb = layer.wkbType()
    crs = layer.crs().authid()
    mem = QgsVectorLayer(f"?crs={crs}", "temp_export", "memory")
    mem_dp = mem.dataProvider()
    mem_dp.addAttributes(layer.fields())
    mem.updateFields()

    feats_to_add = []
    request = QgsFeatureRequest()
    
    # Iterate to collect matching features
    for f in layer.getFeatures(request):
        val = f[id_field] if id_field in layer.fields().names() else None
        if val is None:
            continue
        if str(val) in ids_set:
            feats_to_add.append(f)

    if not feats_to_add:
        msg = self.tr("No features found for the provided IDs.")
        _log(Qgis.Warning, msg)
        return False, msg

    mem_dp.addFeatures(feats_to_add)
    mem.updateExtents()

    # Export memory layer to disk
    return export_layer_to_file(mem, out_path, driver_name=driver_name, layer_name=out_layer_name)


# ============================================================================
# XLSX EXPORT (requires openpyxl)
# ============================================================================

def export_layer_to_xlsx(layer: QgsVectorLayer, xlsx_path: str) -> Tuple[bool, Optional[str]]:
    """
    Export attributes of a layer to XLSX (does not export geometry).
    Requires openpyxl package.

    Parameters:
    - layer: QgsVectorLayer to export
    - xlsx_path: destination .xlsx file path

    Returns:
    - (success: bool, error_message: Optional[str])
    """
    try:
        from openpyxl import Workbook
    except ImportError:
        msg = self.tr("openpyxl not found: please install openpyxl.")
        _log(Qgis.Critical, msg)
        return False, msg

    ensure_parent_dir(xlsx_path)
    try:
        wb = Workbook()
        ws = wb.active
        headers = [f.name() for f in layer.fields()]
        ws.append(headers)
        
        for feat in layer.getFeatures():
            row = [feat.attribute(f.name()) for f in layer.fields()]
            ws.append(row)
        
        wb.save(xlsx_path)
        _log(Qgis.Info, self.tr("XLSX export successful: {}").format(xlsx_path))
        return True, None
    except Exception as e:
        msg = self.tr("XLSX write error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg