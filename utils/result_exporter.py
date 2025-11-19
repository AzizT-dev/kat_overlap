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

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext,
    QgsFeatureRequest,
    QgsFeature,
    Qgis
)

LOG_TAG = "kat_overlap.exporter"

# ---------------------------------------------------------------------------
# Translation helper
# ---------------------------------------------------------------------------
def tr(text: str, context: str = "kat_overlap") -> str:
    """Qt-style translation helper."""
    return QCoreApplication.translate(context, text)


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
def _log(level: int, message: str) -> None:
    """Log a message to QGIS message log or fallback to print."""
    try:
        from qgis.core import QgsMessageLog
        QgsMessageLog.logMessage(message, LOG_TAG, level)
    except Exception:
        print(f"[{LOG_TAG}] {message}")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def ensure_parent_dir(path: str) -> None:
    """Create parent directories if they don't exist."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


# ===========================================================================
# CSV EXPORT FROM QTABLEWIDGET
# ===========================================================================
def export_checked_table_rows_to_csv(table: QTableWidget,
                                     csv_path: str,
                                     header_map: Optional[Dict[int, str]] = None,
                                     delimiter: str = ";") -> Tuple[bool, Optional[str]]:
    """Export only checked rows from a QTableWidget to CSV."""
    if table is None or not isinstance(table, QTableWidget):
        return False, tr("Invalid table.")

    ensure_parent_dir(csv_path)

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
        try:
            w = table.cellWidget(r, 0)
            if isinstance(w, QCheckBox):
                checked = w.isChecked()
        except Exception:
            pass
        if not checked:
            it = table.item(r, 0)
            if isinstance(it, QTableWidgetItem):
                try:
                    checked = (it.checkState() == Qt.Checked or it.text().strip() == "✓")
                except Exception:
                    pass
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
                if widget and hasattr(widget, "text"):
                    try:
                        text = widget.text()
                    except Exception:
                        text = ""
                row.append(text)
        rows.append(row)

    if not rows:
        _log(Qgis.Warning, tr("No checked rows to export."))
        return False, tr("No checked rows.")

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=delimiter)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
        _log(Qgis.Info, tr("CSV export successful: {}").format(csv_path))
        return True, None
    except Exception as e:
        msg = tr("CSV write error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg


# ===========================================================================
# VECTOR LAYER EXPORT (GPKG/Shapefile/GeoJSON)
# ===========================================================================
def export_layer_to_file(layer: QgsVectorLayer, out_path: str,
                         driver_name: Optional[str] = None,
                         layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Export a QgsVectorLayer to out_path using modern API with fallback."""
    if layer is None or not isinstance(layer, QgsVectorLayer):
        return False, tr("Invalid layer.")

    ensure_parent_dir(out_path)

    # Deduce driver from file extension
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
        opts.layerName = layer_name

    try:
        res, err = QgsVectorFileWriter.writeAsVectorFormatV2(layer, out_path, transform_context, opts)
        if res == QgsVectorFileWriter.NoError:
            _log(Qgis.Info, tr("{} export successful: {}").format(driver_name, out_path))
            return True, None
        msg = tr("Write error (code {}): {}").format(res, err)
        _log(Qgis.Critical, msg)
        return False, msg
    except AttributeError:
        # Fallback to older API
        try:
            err_code = QgsVectorFileWriter.writeAsVectorFormat(layer, out_path, "UTF-8",
                                                               transform_context, driver_name)
            if err_code == 0 or err_code == QgsVectorFileWriter.NoError:
                _log(Qgis.Info, tr("{} export successful (legacy API): {}").format(driver_name, out_path))
                return True, None
            msg = tr("Old API error (code {})").format(err_code)
            _log(Qgis.Critical, msg)
            return False, msg
        except Exception as e:
            msg = tr("Fallback export failed: {}").format(e)
            _log(Qgis.Critical, msg)
            return False, msg
    except Exception as e:
        msg = tr("Export error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg


def export_layer_to_gpkg(layer: QgsVectorLayer, out_gpkg_path: str,
                         layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Convenience wrapper to export a layer to GeoPackage."""
    return export_layer_to_file(layer, out_gpkg_path, driver_name="GPKG", layer_name=layer_name)


# ===========================================================================
# EXPORT SUBSET OF FEATURES BY ID
# ===========================================================================
def export_features_by_id_to_file(layer: QgsVectorLayer,
                                  id_field: str,
                                  ids: Iterable,
                                  out_path: str,
                                  driver_name: str = "GPKG",
                                  out_layer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Export only features whose id_field value is in ids."""
    if layer is None:
        return False, tr("Invalid layer.")

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
    for f in layer.getFeatures(request):
        val = f[id_field] if id_field in layer.fields().names() else None
        if val is None:
            continue
        if str(val) in ids_set:
            feats_to_add.append(f)

    if not feats_to_add:
        msg = tr("No features found for the provided IDs.")
        _log(Qgis.Warning, msg)
        return False, msg

    mem_dp.addFeatures(feats_to_add)
    mem.updateExtents()

    return export_layer_to_file(mem, out_path, driver_name=driver_name, layer_name=out_layer_name)


# ===========================================================================
# XLSX EXPORT (requires openpyxl)
# ===========================================================================
def export_layer_to_xlsx(layer: QgsVectorLayer, xlsx_path: str) -> Tuple[bool, Optional[str]]:
    """Export attributes of a layer to XLSX (does not export geometry)."""
    try:
        from openpyxl import Workbook
    except ImportError:
        msg = tr("openpyxl not found: please install openpyxl.")
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
        _log(Qgis.Info, tr("XLSX export successful: {}").format(xlsx_path))
        return True, None
    except Exception as e:
        msg = tr("XLSX write error: {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg
