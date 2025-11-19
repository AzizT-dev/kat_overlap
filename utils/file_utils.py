# -*- coding: utf-8 -*-
"""
KAT Analysis – File Utilities
File utilities and CSV export
"""

import os
from typing import Dict, Optional, Tuple
from PyQt5.QtWidgets import QTableWidget, QCheckBox, QTableWidgetItem
from PyQt5.QtCore import Qt

try:
    from qgis.core import Qgis, QgsApplication
except ImportError:
    class Qgis:
        Info = 0
        Warning = 1
        Critical = 2

def tr(message):
    """Translation helper"""
    return QgsApplication.translate('FileUtils', message)


def _log(level: int, message: str) -> None:
    """
    Log a message to QGIS message log.
    Levels: Qgis.Info, Qgis.Warning, Qgis.Critical
    """
    try:
        from qgis.core import QgsMessageLog
        QgsMessageLog.logMessage(message, "kat_overlap", level)
    except Exception:
        print(f"[kat_overlap] {message}")


def ensure_parent_dir(path: str) -> None:
    """Create parent directories if they don't exist."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def export_checked_table_rows_to_csv(table: QTableWidget,
                                     csv_path: str,
                                     header_map: Optional[Dict[int, str]] = None,
                                     delimiter: str = ";") -> Tuple[bool, Optional[str]]:
    """
    Export only checked rows from a QTableWidget to CSV.
    """
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
            checked = False

        if not checked:
            it = table.item(r, 0)
            if isinstance(it, QTableWidgetItem):
                try:
                    checked = (it.checkState() == Qt.Checked)
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
        _log(Qgis.Warning, tr("No checked rows to export."))
        return False, tr("No checked rows.")

    try:
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=delimiter)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
        _log(Qgis.Info, tr("CSV export (checked rows) successful: {}").format(csv_path))
        return True, None
    except Exception as e:
        msg = tr("CSV write error (checked rows): {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg
