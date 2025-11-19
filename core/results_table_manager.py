# -*- coding: utf-8 -*-
"""
KAT Analysis – Results Table Manager  
Results table population and interaction handlers

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QTableWidgetItem, QCheckBox, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class ResultsTableManager:
    """
    Manages results table population, filtering, and user interactions.
    """

    @staticmethod
    def populate_results_table(dialog, results: List[Dict[str, Any]]):
        dialog._original_results = results
        dialog.results_table.setRowCount(len(results))

        for i, r in enumerate(results):
            # Checkbox column
            chk = QCheckBox()
            chk.stateChanged.connect(
                lambda state, row=i: ResultsTableManager._on_row_checkbox_changed(dialog, row, state)
            )
            dialog.results_table.setCellWidget(i, 0, chk)

            # Anomaly type
            dialog.results_table.setItem(i, 1, QTableWidgetItem(str(r.get("type", ""))))

            # IDs
            id_a_real = r.get("id_a_real") or r.get("id_a") or ""
            id_b_real = r.get("id_b_real") or r.get("id_b") or ""
            dialog.results_table.setItem(i, 2, QTableWidgetItem(str(id_a_real)))
            dialog.results_table.setItem(i, 3, QTableWidgetItem(str(id_b_real)))

            # Measure
            measure_val = r.get("measure", 0.0) or 0.0
            measure_text = f"{float(measure_val):.3f}"
            dialog.results_table.setItem(i, 4, QTableWidgetItem(measure_text))

            # Ratio/Distance
            ratio_pct = r.get("ratio_percent", 0.0) or 0.0
            dialog.results_table.setItem(i, 5, QTableWidgetItem(f"{ratio_pct:.1f}%"))

            # Severity
            severity = ResultsTableManager._compute_severity(r)
            sev_item = QTableWidgetItem(severity)
            sev_item.setForeground(ResultsTableManager._get_severity_color(severity))
            dialog.results_table.setItem(i, 6, sev_item)

            # Action combo
            action_combo = ResultsTableManager._create_action_combo(dialog, i, r)
            dialog.results_table.setCellWidget(i, 7, action_combo)

        dialog.results_table.resizeColumnsToContents()

    @staticmethod
    def _compute_severity(result: Dict[str, Any]) -> str:
        anomaly = result.get("anomaly", "")
        area = result.get("area_m2", 0.0)

        if anomaly in ("doublon", "point_duplicate", "point_proximity"):
            return ResultsTableManager.tr("High")

        if area > 100:
            return ResultsTableManager.tr("Critical")
        elif area > 10:
            return ResultsTableManager.tr("High")
        elif area > 1:
            return ResultsTableManager.tr("Moderate")
        else:
            return ResultsTableManager.tr("Low")

    @staticmethod
    def _get_severity_color(severity: str) -> QColor:
        colors = {
            ResultsTableManager.tr("Critical"): QColor("#e74c3c"),
            ResultsTableManager.tr("High"): QColor("#e67e22"),
            ResultsTableManager.tr("Moderate"): QColor("#f39c12"),
            ResultsTableManager.tr("Low"): QColor("#95a5a6")
        }
        return colors.get(severity, QColor("#2c3e50"))

    @staticmethod
    def _create_action_combo(dialog, row: int, result: Dict[str, Any]) -> QComboBox:
        combo = QComboBox()
        anomaly = result.get("anomaly", result.get("type", ""))
        combo.addItems([ResultsTableManager.tr("Validate"), ResultsTableManager.tr("Delete")])
        combo.currentTextChanged.connect(
            lambda text: ResultsTableManager._on_action_changed(dialog, row, text)
        )
        return combo

    @staticmethod
    def _on_row_checkbox_changed(dialog, row: int, state: int):
        if state == Qt.Checked:
            dialog.selected_rows.add(row)
        else:
            dialog.selected_rows.discard(row)

        has_selection = len(dialog.selected_rows) > 0
        if hasattr(dialog, 'export_btn'):
            dialog.export_btn.setEnabled(has_selection)
        if hasattr(dialog, 'correct_btn'):
            dialog.correct_btn.setEnabled(has_selection)

    @staticmethod
    def _on_action_changed(dialog, row: int, action_text: str):
        if hasattr(dialog, '_log_message'):
            dialog._log_message("info", ResultsTableManager.tr("Line {}: action = {}").format(row + 1, action_text))

    @staticmethod
    def set_results_headers_for_type(dialog, analysis_type: Optional[str]):
        if isinstance(analysis_type, str) and "overlap" in analysis_type.lower():
            measure_label = ResultsTableManager.tr("Area (m²)")
        else:
            measure_label = ResultsTableManager.tr("Measure (m)")

        headers = ["", ResultsTableManager.tr("Anomaly"), ResultsTableManager.tr("ID 1"), ResultsTableManager.tr("ID 2"),
                   measure_label, ResultsTableManager.tr("Ratio/Dist"), ResultsTableManager.tr("Severity"),
                   ResultsTableManager.tr("Action")]
        dialog.results_table.setHorizontalHeaderLabels(headers)

    @staticmethod
    def tr(message):
        from qgis.core import QgsApplication
        return QgsApplication.translate('ResultsTableManager', message)
