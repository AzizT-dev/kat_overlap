# -*- coding: utf-8 -*-
"""
KAT Analyse – Overlap UI
Main user interface

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QFrame, QSplitter, QAbstractItemView, QWidget, QMessageBox,
    QRadioButton, QCheckBox, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QCoreApplication
from PyQt5.QtGui import QColor
from qgis.gui import QgsProjectionSelectionWidget
import os, sys, traceback
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import QTextEdit
from qgis.core import QgsProject, QgsVectorLayer, QgsApplication
from qgis.utils import iface as qgis_iface

# Plugin path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

from .ui.theme import get_light_style, get_dark_style
from .core.analysis_task import AnalysisTask
from .core.classification import PresetManager
from .utils.result_layer_utils import ResultLayerBuilder
from .core.layer_helpers import LayerSelectionManager
from .core.ui_export_manager import UIExportManager
from .core.correction_manager import CorrectionManager
from .core.visualization import VisualizationManager
from .core.results_table_manager import ResultsTableManager
from .core.temp_layer_manager import TempLayerManager

LOG_TAG = "kat_overlap.ui"

class ModernKatOverlapUI(QDialog):
    """Main UI dialog for KAT Overlap analysis - Panels merged"""

    theme_changed = pyqtSignal(str)
    analysis_requested = pyqtSignal(dict)
    layers_requested = pyqtSignal()
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, object)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None, iface=None):
        super().__init__(parent)
        self.setObjectName("ModernKatOverlapUI")
        self.iface = iface or qgis_iface
        self.current_theme = "light"
        self.selected_rows = set()
        self.overlap_geometries = []
        self.selected_layers = set()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(1200, 800)
        self.apply_theme(self.current_theme)
        self._init_state()
        self.init_ui()
        try:
            self.log_signal.connect(self._log_message)
            self.progress_signal.connect(lambda pct, msg=None: self._on_task_progress(pct, msg))
            self.finished_signal.connect(self._on_task_finished)
            self.error_signal.connect(self._on_task_error)
        except Exception:
            pass
        self.load_project_layers()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_project_changes)
        self.update_timer.start(2000)
        self.last_layer_count = len(QgsProject.instance().mapLayers())

    def _init_state(self):
        self.task = None
        self.all_layers = []
        self.id_fields: Dict[str, str] = {}
        self.layer_widgets: Dict[str, Dict[str, Any]] = {}
        self.result_layer = None
        self._original_results: List[Dict[str, Any]] = []
        self.params = {}
        self._current_rubber_bands = []
        from qgis.core import QgsDistanceArea
        self.da = QgsDistanceArea()
        try:
            self.da.setEllipsoid(QgsProject.instance().ellipsoid())
            self.da.setSourceCrs(QgsProject.instance().crs(), QgsProject.instance().transformContext())
        except Exception:
            pass

    def apply_theme(self, theme):
        self.current_theme = theme
        if theme == "dark":
            stylesheet = get_dark_style()
        else:
            stylesheet = get_light_style()
        self.setStyleSheet(stylesheet)
        self.theme_changed.emit(theme)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._create_title_bar())
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.create_left_panel())
        splitter.addWidget(self.create_right_panel())
        splitter.setSizes([360, 840])
        content_layout.addWidget(splitter)
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)

    def _create_title_bar(self):
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet("""
            #titleBar {
                background-color: #2c3e50;
                border: none;
            }
            QLabel#titleLabel {
                color: #e6e8ff;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#windowControl {
                background-color: transparent;
                border: none;
                color: #e6e8ff;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#windowControl:hover {
                background-color: #34495e;
            }
            QPushButton#closeBtn {
                background-color: transparent;
                border: none;
                color: #e6e8ff;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#closeBtn:hover {
                background-color: #e74c3c;
            }
        """)         
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)
        title_label = QLabel(self.tr("KAT Analyse – Overlap area v1.0.0"))
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        minimize_btn = QPushButton("–"); minimize_btn.clicked.connect(self.showMinimized)
        maximize_btn = QPushButton("□"); maximize_btn.clicked.connect(self.toggle_maximize)
        close_btn = QPushButton("×"); close_btn.clicked.connect(self.close)
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(maximize_btn)
        title_layout.addWidget(close_btn)
        return title_bar

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def check_project_changes(self):
        try:
            current_count = len(QgsProject.instance().mapLayers())
            if current_count != self.last_layer_count:
                self.load_project_layers()
                self.last_layer_count = current_count
        except Exception:
            pass

    # ================== LEFT PANEL =====================
    def create_left_panel(self):
        panel = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Layers table
        layers_group = QGroupBox(self.tr("Layer Selection"))
        layers_group.setToolTip(self.tr("""Available treatments:
        • Single-layer:
        1 point layer → Duplicate/proximity analysis
        1 line layer → Topology check
        1 polygon layer → Self-intersections

        • Multi-layers (same type):
        2-4 point layers → Proximity analysis
        2-4 line layers → Topology check
        2-4 polygon layers → Inter-layer overlaps

        • Mixed combinations:
        Points + Polygons → Point-polygon association"""))
        layers_layout = QVBoxLayout()
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(4)
        self.layers_table.setHorizontalHeaderLabels([
            self.tr("Select"), self.tr("Layer"), self.tr("Type"), self.tr("ID Field")
        ])
        self.layers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layers_table.verticalHeader().setVisible(False)
        self.layers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layers_table.setMinimumHeight(300)
        self.layers_table.verticalHeader().setDefaultSectionSize(40)
        self.layers_table.setColumnWidth(3, 150)
        layers_layout.addWidget(self.layers_table)
        layers_group.setLayout(layers_layout)
        layout.addWidget(layers_group)

        # Analysis parameters
        params_group = QGroupBox(self.tr("Analysis Parameters"))
        params_layout = QVBoxLayout()
        self.profile_combo = QComboBox()
        try:
            self.profile_combo.addItems(PresetManager.get_profile_names())
        except Exception:
            self.profile_combo.addItem(self.tr("Custom"))
        params_layout.addWidget(QLabel(self.tr("Business profile")))
        params_layout.addWidget(self.profile_combo)
        self.profile_combo.currentTextChanged.connect(self._on_profile_selection_changed)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # CRS and options
        layout.addWidget(self.create_crs_group())
        layout.addWidget(self.create_options_group())

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_analyze = QPushButton(self.tr("▶️ Run Analysis"))
        self.btn_analyze.clicked.connect(self.run_analysis)
        self.btn_cancel = QPushButton(self.tr("❌ Cancel"))
        self.btn_cancel.clicked.connect(self._cancel_task)
        self.btn_cancel.setEnabled(False)
        self.reset_ui_btn = QPushButton(self.tr("🔄 Reset UI"))
        self.reset_ui_btn.clicked.connect(self._on_reset_ui)
        btn_layout.addWidget(self.btn_analyze)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.reset_ui_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    # ================== RIGHT PANEL =====================
    def create_right_panel(self):
        panel = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Stats + filters row
        header_layout = QHBoxLayout()
        stats_layout = QHBoxLayout()
        self.stats_data = [
            (self.tr("Total"), "0", "#3498db"),
            (self.tr("Critical"), "0", "#e74c3c"),
            (self.tr("High"), "0", "#e67e22"),
            (self.tr("Moderate"), "0", "#f39c12"),
            (self.tr("Low"), "0", "#27ae60")
        ]
        self.stat_labels = {}
        for label, value, color in self.stats_data:
            f = QFrame()
            fl = QVBoxLayout()
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"color:{color}; font-weight:bold;")
            txt_lbl = QLabel(label)
            txt_lbl.setStyleSheet("color:#7f8c8d; font-size:10px;")
            fl.addWidget(val_lbl)
            fl.addWidget(txt_lbl)
            f.setLayout(fl)
            stats_layout.addWidget(f)
            self.stat_labels[label] = val_lbl
        header_layout.addLayout(stats_layout)
        header_layout.addWidget(self._create_filters_widget())
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Results table
        self.create_results_table()
        layout.addWidget(self.results_table)

        # Action buttons
        btns_row = QHBoxLayout()
        self.export_btn = QPushButton(self.tr("Export Selection"))
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.correct_btn = QPushButton(self.tr("Correct Selection"))
        self.correct_btn.clicked.connect(self._on_correct_selection)
        self.correct_btn.setEnabled(False)
        self.export_layer_btn = QPushButton(self.tr("Export Result Layer"))
        self.export_layer_btn.clicked.connect(self.export_result_layer)
        self.export_layer_btn.setEnabled(False)
        btns_row.addWidget(self.export_btn)
        btns_row.addWidget(self.correct_btn)
        btns_row.addWidget(self.export_layer_btn)
        btns_row.addStretch()
        layout.addLayout(btns_row)

        # Logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(140)
        layout.addWidget(self.log_text)
        panel.setLayout(layout)
        return panel

    # ================== PANELS FUNCTIONS (CRS + OPTIONS) =====================
    def create_crs_group(self):
        crs_group = QGroupBox(self.tr("Output Coordinate System"))
        crs_layout = QVBoxLayout()
        self.radio_crs_source = QRadioButton(self.tr("Keep source layer CRS"))
        self.radio_crs_custom = QRadioButton(self.tr("Choose custom EPSG"))
        self.radio_crs_source.setChecked(True)
        bgrp = QButtonGroup()
        bgrp.addButton(self.radio_crs_source)
        bgrp.addButton(self.radio_crs_custom)
        self.radio_crs_custom.toggled.connect(lambda checked: self.crs_selector.setEnabled(checked))
        crs_layout.addWidget(self.radio_crs_source)
        crs_layout.addWidget(self.radio_crs_custom)
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setEnabled(False)
        crs_layout.addWidget(self.crs_selector)
        crs_group.setLayout(crs_layout)
        return crs_group

    def create_options_group(self):
        options_group = QGroupBox(self.tr("Options"))
        options_layout = QVBoxLayout()
        self.create_layer_checkbox = QCheckBox(self.tr("Create results layer"))
        self.create_layer_checkbox.setChecked(True)
        options_layout.addWidget(self.create_layer_checkbox)
        self.generate_fid_checkbox = QCheckBox(self.tr("Generate unique ID (for Points)"))
        self.generate_fid_checkbox.setToolTip(
            self.tr("Generate a unique identifier per point to avoid false duplicates "
                    "(points from shared vertices).")
        )
        options_layout.addWidget(self.generate_fid_checkbox)
        options_group.setLayout(options_layout)
        return options_group

    def _create_filters_widget(self):
        filter_container = QGroupBox(self.tr("Filters and Actions"))
        layout = QVBoxLayout()
        h = QHBoxLayout()
        h.addWidget(QLabel(self.tr("Filter by severity:")))
        self.combo_severity_filter = QComboBox()
        self.combo_severity_filter.addItems([
            self.tr("All"), self.tr("Critical"), self.tr("High"),
            self.tr("Moderate"), self.tr("Low"), self.tr("Critical + High"),
            self.tr("Moderate + Low")
        ])
        self.combo_severity_filter.setEnabled(True)
        self.combo_severity_filter.currentIndexChanged.connect(self._on_severity_filter_changed)
        h.addStretch()
        layout.addLayout(h)
        filter_container.setLayout(layout)
        return filter_container

    def create_results_table(self):
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        headers = [
            "", self.tr("Anomaly"), self.tr("ID 1"), self.tr("ID 2"),
            self.tr("Measure"), self.tr("Ratio/Dist"), self.tr("Severity"),
            self.tr("Action")
        ]
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setColumnWidth(0, 36)
        self.results_table.setColumnWidth(7, 140)
        self.results_table.cellClicked.connect(self._on_row_clicked)
        self.results_table.doubleClicked.connect(self._on_table_double_click)

    # ================== TR =====================

    def load_project_layers(self):
        """Load project layers - MODULARIZED"""
        LayerSelectionManager.load_project_layers(self)

    def get_selected_layers(self):
        """Get selected layers with auto-fusion - MODULARIZED"""
        return LayerSelectionManager.get_selected_layers(self)

    # ========================================================================
    # ANALYSIS
    # ========================================================================

    def run_analysis(self):
        """Launch analysis"""
        try:
            layers = self.get_selected_layers()
            if not any(layers.values()):
                QMessageBox.warning(self, self.tr("Warning"), self.tr("No valid layer selected."))
                return
            
            if not self._validate_crs_selection():
                return
            
            params = {
                'profile': self.profile_combo.currentText(),
                'output_crs': self.crs_selector.crs() if self.radio_crs_custom.isChecked() else None,
                'create_result_layer': self.create_layer_checkbox.isChecked(),
                'generate_fid': self.generate_fid_checkbox.isChecked(),
                'min_display_area': float(1.0)
            }
            
            self.btn_analyze.setEnabled(False)
            self.btn_cancel.setEnabled(True)
            self._clear_results()
            self._log_message("info", self.tr("Starting analysis ..."))

            self.task = AnalysisTask(
                description="KAT Overlap",
                layers=layers,
                params=params,
                id_fields=self.id_fields,
                generate_fid=params['generate_fid'],
                on_progress=self.progress_signal.emit,
                on_log=self.log_signal.emit,
                on_finished=self.finished_signal.emit,
                on_error=self.error_signal.emit
            )
            QgsApplication.taskManager().addTask(self.task)
        
        except Exception as e:
            self._log_message("error", self.tr("Error starting analysis: {}\n{}").format(e, traceback.format_exc()))
            self.btn_analyze.setEnabled(True)
            self.btn_cancel.setEnabled(False)

    def _validate_crs_selection(self):
        """Validate CRS selection"""
        if self.radio_crs_custom.isChecked():
            crs = self.crs_selector.crs()
            if not crs.isValid():
                QMessageBox.warning(self, self.tr("Invalid CRS"), self.tr("Please select a valid coordinate system"))
                return False
        return True

    def _cancel_task(self):
        """Cancel running task"""
        try:
            if self.task:
                self.task.cancel()
                self._log_message("info", self.tr("Cancellation requested."))
                self.btn_cancel.setEnabled(False)
        except Exception as e:
            self._log_message("error", self.tr("Error cancelling: {}").format(e))

    def _on_task_progress(self, pct: int, message: Optional[str] = None):
        """Task progress callback"""
        if message:
            self._log_message("info", message)

    def _on_task_log(self, level, msg):
        """Task log callback"""
        self._log_message(level, msg)

    def _on_task_finished(self, results: List[Dict[str, Any]]):
        """Task finished callback - MODULARIZED"""
        try:
            self._log_message("info", self.tr("Analysis finished."))
            self.btn_analyze.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            self._original_results = results or []
            
            first_type = results[0].get("type", "") if results else None
            
            # MODULARIZED: Set headers
            ResultsTableManager.set_results_headers_for_type(self, first_type)
            
            # MODULARIZED: Populate table
            ResultsTableManager.populate_results_table(self, results or [])
            
            # MODULARIZED: Build overlap geometries
            VisualizationManager.build_overlap_geometries_from_results(self, results or [])
            
            # Update stats
            self._update_stats_labels()
            
            # MODULARIZED: Create result layer
            if self.create_layer_checkbox.isChecked() and results:
                self._create_result_layer(results)
            
            self.task = None
        
        except Exception as e:
            self._log_message("error", self.tr("Error on_finished: {}\n{}").format(e, traceback.format_exc()))

    def _on_task_error(self, message: str):
        """Task error callback"""
        self._log_message("error", message)
        self.btn_analyze.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.task = None

    # ========================================================================
    # RESULTS MANAGEMENT
    # ========================================================================

    def _create_result_layer(self, results: list):
        """Create result layer - MODULARIZED"""
        self.result_layer = ResultLayerBuilder.create_result_layer(self, results)

    def _clear_results(self):
        """Clear results"""
        try:
            self.results_table.setRowCount(0)
            self.selected_rows.clear()
            self.overlap_geometries = []
            self._original_results = []
            
            if self.export_btn:
                self.export_btn.setEnabled(False)
            if self.correct_btn:
                self.correct_btn.setEnabled(False)
            
            self._update_stats_labels()
            
            if hasattr(self, "log_text") and self.log_text:
                self.log_text.clear()
        except Exception:
            pass

    def _update_stats_labels(self):
        """Update statistics labels"""
        try:
            results = self._original_results
            total = len(results)
            
            severities = {self.tr("Critical"): 0, self.tr("High"): 0, self.tr("Moderate"): 0, self.tr("Low"): 0}
            
            for r in results:
                area = r.get("area_m2", 0.0)
                anomaly = r.get("anomaly", "")
                
                if anomaly in ("duplicate", "point_duplicate", "point_proximity"):
                    severities[self.tr("High")] += 1
                elif area > 100:
                    severities[self.tr("Critical")] += 1
                elif area > 10:
                    severities[self.tr("High")] += 1
                elif area > 1:
                    severities[self.tr("Moderate")] += 1
                else:
                    severities[self.tr("Low")] += 1
            
            self.stat_labels[self.tr("Total")].setText(str(total))
            self.stat_labels[self.tr("Critical")].setText(str(severities[self.tr("Critical")]))
            self.stat_labels[self.tr("High")].setText(str(severities[self.tr("High")]))
            self.stat_labels[self.tr("Moderate")].setText(str(severities[self.tr("Moderate")]))
            self.stat_labels[self.tr("Low")].setText(str(severities[self.tr("Low")]))
        
        except Exception as e:
            self._log_message("error", self.tr("Error stats: {}").format(e))

    # ========================================================================
    # TABLE INTERACTIONS - MODULARIZED
    # ========================================================================

    def _on_row_clicked(self, row: int, column: int):
        """Handle row click - MODULARIZED"""
        try:
            if row < len(self._original_results):
                result = self._original_results[row]
                VisualizationManager.highlight_overlap(self, row, result)
        except Exception as e:
            self._log_message("error", self.tr("Error _on_row_clicked: {}").format(e))

    def _on_table_double_click(self, index):
        """Handle double click - zoom to feature"""
        try:
            row = index.row()
            if row < len(self._original_results):
                result = self._original_results[row]
                self._log_message("info", self.tr("Zooming to row {}").format(row+1))
        except Exception as e:
            self._log_message("error", self.tr("Error double-click: {}").format(e))

    def _on_severity_filter_changed(self, idx):
        """Apply severity filter"""
        try:
            sel = self.combo_severity_filter.currentText()
            visible_count = 0
            
            for r in range(self.results_table.rowCount()):
                item = self.results_table.item(r, 6)
                if not item:
                    continue
                
                sev = item.text()
                show = True
                
                if sel == self.tr("All"):
                    show = True
                elif sel == self.tr("Critical + High"):
                    show = sev in (self.tr("Critical"), self.tr("High"))
                elif sel == self.tr("Moderate + Low"):
                    show = sev in (self.tr("Moderate"), self.tr("Low"))
                else:
                    show = (sev == sel)
                
                self.results_table.setRowHidden(r, not show)
                if show:
                    visible_count += 1
            
            self._log_message("info", self.tr("Filter: {} → {}/{} rows").format(sel, visible_count, self.results_table.rowCount()))
        
        except Exception as e:
            self._log_message("error", self.tr("Error filter: {}").format(e))

    # ========================================================================
    # EXPORTS - MODULARIZED
    # ========================================================================

    def export_results(self):
        """Export selected results to CSV - MODULARIZED"""
        UIExportManager.export_results(self)

    def export_result_layer(self):
        """Export result layer - MODULARIZED"""
        UIExportManager.export_result_layer(self)

    def export_selected_entities_by_id(self, use_action_delete_only: bool = False):
        """Export selected entities by ID - MODULARIZED"""
        UIExportManager.export_selected_entities_by_id(self, use_action_delete_only)

    # ========================================================================
    # CORRECTIONS - MODULARIZED
    # ========================================================================

    def _on_correct_selection(self):
        """Apply corrections - MODULARIZED"""
        CorrectionManager.apply_corrections_from_table(self)

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _on_profile_selection_changed(self, text):
        """Handle profile selection change"""
        try:
            preset = PresetManager.get_preset(text)
            layers = self.get_selected_layers()
            geom_type = 'polygon' if layers.get('polygon') else ('point' if layers.get('point') else 'line')
            info_html = PresetManager.format_threshold_info(preset, geom_type)
            self.log_text.clear()
            self.log_text.append(self.tr("[i] Profile: {}").format(text))
            self.log_text.append(info_html)
        except Exception:
            self._log_message("info", self.tr("Profile: {}").format(text))

    def _log_message(self, level, message):
        """Log message to UI"""
        prefix = {"info": self.tr("[i]"), "warning": self.tr("[!]"), "error": self.tr("[x]")}
        txt = f"{prefix.get(level, '')} {message}"
        try:
            if hasattr(self, "log_text") and self.log_text is not None:
                self.log_text.append(txt)
        except Exception:
            print(LOG_TAG, txt)

    def _on_reset_ui(self):
        """Reset UI state"""
        for lid, w in self.layer_widgets.items():
            try:
                w['checkbox'].blockSignals(True)
                w['checkbox'].setChecked(False)
                w['checkbox'].blockSignals(False)
                w['id_combo'].setCurrentIndex(0)
            except Exception:
                pass
        
        self.id_fields.clear()
        self.selected_layers.clear()
        self._clear_results()
        self.log_text.clear()

    # ========================================================================
    # CLEANUP - MODULARIZED
    # ========================================================================

    def closeEvent(self, event):
        """Handle dialog close - MODULARIZED cleanup"""
        try:
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
        except Exception:
            pass
        
        # MODULARIZED: Cleanup temp layers
        TempLayerManager.cleanup_temp_layers(self)
        
        # MODULARIZED: Cleanup rubber bands
        TempLayerManager.cleanup_rubber_bands(self)
        
        try:
            self._clear_results()
            self.selected_layers.clear()
            self.id_fields.clear()
        except Exception:
            pass
        
        if self.task:
            try:
                self.task.cancel()
            except Exception:
                pass
        
        event.accept()

    def tr(self, text):
        """Translation method for this dialog"""
        return QCoreApplication.translate('ModernKatOverlapUI', text)
