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
        """
        Populate results table with analysis results.
        
        Parameters:
        - dialog: UI dialog reference
        - results: List of analysis results
        """
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
        """Compute severity based on area or anomaly type."""
        anomaly = result.get("anomaly", "")
        area = result.get("area_m2", 0.0)
        
        if anomaly in ("doublon", "point_duplicate", "point_proximity"):
            return self.tr("Élevée")
        
        if area > 100:
            return self.tr("Critique")
        elif area > 10:
            return self.tr("Élevée")
        elif area > 1:
            return self.tr("Modéré")
        else:
            return self.tr("Faible")
    
    @staticmethod
    def _get_severity_color(severity: str) -> QColor:
        """Get color for severity level."""
        colors = {
            self.tr("Critique"): QColor("#e74c3c"),
            self.tr("Élevée"): QColor("#e67e22"),
            self.tr("Modéré"): QColor("#f39c12"),
            self.tr("Faible"): QColor("#95a5a6")
        }
        return colors.get(severity, QColor("#2c3e50"))
    
    @staticmethod
    def _create_action_combo(dialog, row: int, result: Dict[str, Any]) -> QComboBox:
        """Create action combo box for a result row."""
        combo = QComboBox()
        anomaly = result.get("anomaly", result.get("type", ""))
        
        if anomaly in ("doublon", "point_duplicate", "point_proximity"):
            combo.addItems([self.tr("Valider"), self.tr("Supprimer")])
        elif "overlap" in anomaly:
            combo.addItems([self.tr("Valider"), self.tr("Supprimer")])
        else:
            combo.addItems([self.tr("Valider"), self.tr("Supprimer")])
        
        combo.currentTextChanged.connect(
            lambda text: ResultsTableManager._on_action_changed(dialog, row, text)
        )
        
        return combo
    
    @staticmethod
    def _on_row_checkbox_changed(dialog, row: int, state: int):
        """Handle row checkbox state change."""
        if state == Qt.Checked:
            dialog.selected_rows.add(row)
        else:
            dialog.selected_rows.discard(row)
        
        # Enable/disable buttons based on selection
        has_selection = len(dialog.selected_rows) > 0
        if hasattr(dialog, 'export_btn'):
            dialog.export_btn.setEnabled(has_selection)
        if hasattr(dialog, 'correct_btn'):
            dialog.correct_btn.setEnabled(has_selection)
    
    @staticmethod
    def _on_action_changed(dialog, row: int, action_text: str):
        """Handle action combo selection change."""
        if hasattr(dialog, '_log_message'):
            dialog._log_message("info", self.tr("Line {}: action = {}").format(row+1, action_text))
    
    @staticmethod
    def set_results_headers_for_type(dialog, analysis_type: Optional[str]):
        """Set appropriate headers based on analysis type."""
        if isinstance(analysis_type, str) and "overlap" in analysis_type.lower():
            measure_label = self.tr("Superficie (m²)")
        else:
            measure_label = self.tr("Mesure (m)")
        
        headers = ["", self.tr("Anomalie"), self.tr("ID 1"), self.tr("ID 2"), measure_label, self.tr("Ratio/Dist"), self.tr("Gravité"), self.tr("Action")]
        dialog.results_table.setHorizontalHeaderLabels(headers)

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API."""
        from qgis.core import QgsApplication
        return QgsApplication.translate('ResultsTableManager', message)