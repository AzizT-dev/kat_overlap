# -*- coding: utf-8 -*-
"""
KAT Analysis – File Utilities
File utilities and CSV export

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os
from typing import Dict, Optional, Tuple
from PyQt5.QtWidgets import QTableWidget, QCheckBox, QTableWidgetItem
from PyQt5.QtCore import Qt

try:
    from qgis.core import Qgis
except ImportError:
    # Fallback for non-QGIS environments
    class Qgis:
        Info = 0
        Warning = 1
        Critical = 2


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
        QgsMessageLog.logMessage(message, "kat_overlap", level)
    except Exception:
        # Fallback: print if QGIS not available
        print(f"[kat_overlap] {message}")


# ============================================================================
# FILE UTILITIES
# ============================================================================

def ensure_parent_dir(path: str) -> None:
    """Create parent directories if they don't exist."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


# ============================================================================
# CSV EXPORT FROM TABLE
# ============================================================================

def export_checked_table_rows_to_csv(table: QTableWidget,
                                     csv_path: str,
                                     header_map: Optional[Dict[int, str]] = None,
                                     delimiter: str = ";") -> Tuple[bool, Optional[str]]:
    """
    Export only checked rows from a QTableWidget to CSV.

    Parameters:
    - table: QTableWidget instance (checkbox expected in column 0, but function is robust)
    - csv_path: destination path for CSV
    - header_map: optional dict mapping column_index -> csv_column_name.
                  If None, uses table.horizontalHeaderItem(col).text()
    - delimiter: CSV delimiter (default: ";")

    Returns:
    - (True, None) on success or (False, error_message) on failure.
    """
    if table is None or not isinstance(table, QTableWidget):
        return False, self.tr("Invalid table.")

    ensure_parent_dir(csv_path)

    # Build header names
    col_count = table.columnCount()
    headers = []
    for c in range(col_count):
        if header_map and c in header_map:
            headers.append(header_map[c])
        else:
            header_item = table.horizontalHeaderItem(c)
            headers.append(header_item.text() if header_item is not None else f"col_{c}")

    # Collect checked rows
    rows_out = []
    for r in range(table.rowCount()):
        checked = False
        # Case 1: checkbox widget in column 0
        try:
            w = table.cellWidget(r, 0)
            if isinstance(w, QCheckBox):
                checked = w.isChecked()
        except Exception:
            checked = False

        # Case 2: checkable QTableWidgetItem in column 0
        if not checked:
            it = table.item(r, 0)
            if isinstance(it, QTableWidgetItem):
                try:
                    checked = (it.checkState() == Qt.Checked)
                except Exception:
                    checked = False

        if not checked:
            continue

        # Build row list using visible text values
        row_data = []
        for c in range(col_count):
            cell_item = table.item(r, c)
            if cell_item is not None:
                row_data.append(cell_item.text())
            else:
                # try to read widget text if present (e.g., a QLabel inside cell)
                widget = table.cellWidget(r, c)
                if widget is not None and hasattr(widget, "text"):
                    try:
                        row_data.append(widget.text())
                    except Exception:
                        row_data.append("")
                else:
                    row_data.append("")
        rows_out.append(row_data)

    if not rows_out:
        _log(Qgis.Warning, self.tr("No checked rows to export."))
        return False, self.tr("No checked rows.")

    # Write CSV
    try:
        import csv as csv_module
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv_module.writer(fh, delimiter=delimiter)
            writer.writerow(headers)
            for row in rows_out:
                writer.writerow(row)
        _log(Qgis.Info, self.tr("CSV export (checked rows) successful: {}").format(csv_path))
        return True, None
    except Exception as e:
        msg = self.tr("CSV write error (checked rows): {}").format(e)
        _log(Qgis.Critical, msg)
        return False, msg