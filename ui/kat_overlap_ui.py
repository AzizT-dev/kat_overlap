# -*- coding: utf-8 -*-
"""
KAT Analysis – Main UI Dialog
Modern interface for overlap analysis

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox,
    QPushButton, QTableWidget, QTextEdit, QProgressBar, QCheckBox,
    QFileDialog, QMessageBox, QSplitter, QWidget, QTableWidgetItem,
    QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import QgsProject, QgsVectorLayer, QgsApplication
from qgis.gui import QgsProjectionSelectionWidget

from ..core.utils import log_message, tr, TempLayerTracker
from ..core.classification import PresetManager
from ..core.analysis_engine import AnalysisTask
from ..core.layer_operations import merge_layers_to_temp
from ..core.results_handler import ResultsTableManager, ResultLayerBuilder, ResultExporter
from ..core.visualization import create_visualization_manager


class ModernKatOverlapUI(QDialog):
    """Main dialog for KAT Overlap Analysis"""
    
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle(tr("KAT Overlap Analyzer"))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(1200, 800)
        
        # State variables
        self.selected_layers = set()
        self.id_fields = {}
        self.results = []
        self.result_layer = None
        self.current_task = None
        self.is_maximized = False
        
        # Visualization manager
        self.viz_manager = create_visualization_manager(iface)
        
        # Setup UI
        self.setup_ui()
        self.load_layers()
        
        log_message('info', "KAT Overlap UI initialized")
    
    def setup_ui(self):
        """Create UI layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)
        
        # Content container
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Configuration
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Results
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        content_layout.addWidget(splitter)
        
        # Bottom: Log panel
        log_group = QGroupBox(tr("Logs"))
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        content_layout.addWidget(log_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        self.setLayout(main_layout)
    
    def _create_title_bar(self):
        """Create custom title bar with window controls"""
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet("""
            #titleBar { background-color: #2c3e50; border: none; }
            QLabel#titleLabel { color: #e6e8ff; font-weight: bold; font-size: 14px; }
            QPushButton#windowControl {
                background-color: transparent; border: none; color: #e6e8ff;
                font-weight: bold; font-size: 16px;
                min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px;
            }
            QPushButton#windowControl:hover { background-color: #34495e; }
            QPushButton#closeBtn {
                background-color: transparent; border: none; color: #e6e8ff;
                font-weight: bold; font-size: 16px;
                min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px;
            }
            QPushButton#closeBtn:hover { background-color: #e74c3c; }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)
        
        title_label = QLabel(tr("KAT Overlap Analyzer"))
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        
        minimize_btn = QPushButton("–")
        minimize_btn.setObjectName("windowControl")
        minimize_btn.clicked.connect(self.showMinimized)
        
        maximize_btn = QPushButton("□")
        maximize_btn.setObjectName("windowControl")
        maximize_btn.clicked.connect(self.toggle_maximize)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(maximize_btn)
        title_layout.addWidget(close_btn)
        
        return title_bar
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
        else:
            self.showMaximized()
            self.is_maximized = True
    
    def create_left_panel(self) -> QWidget:
        """Create left configuration panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Layer selection
        layers_group = QGroupBox(tr("Layer Selection"))
        layers_layout = QVBoxLayout()
        
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(4)
        self.layers_table.setHorizontalHeaderLabels([
            "", tr("Layer"), tr("Type"), tr("ID Field")
        ])
        layers_layout.addWidget(self.layers_table)
        
        layers_group.setLayout(layers_layout)
        layout.addWidget(layers_group)
        
        # Analysis parameters
        params_group = QGroupBox(tr("Analysis Parameters"))
        params_layout = QVBoxLayout()
        
        # Business profile
        profile_label = QLabel(tr("Business Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(PresetManager.get_profile_names())
        params_layout.addWidget(profile_label)
        params_layout.addWidget(self.profile_combo)
        
        # CRS selection
        crs_label = QLabel(tr("Output CRS:"))
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setCrs(QgsProject.instance().crs())
        params_layout.addWidget(crs_label)
        params_layout.addWidget(self.crs_selector)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Action buttons
        self.analyze_btn = QPushButton(tr("▶️ Start Analysis"))
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        self.cancel_btn = QPushButton(tr("⏹️ Cancel"))
        self.cancel_btn.clicked.connect(self.cancel_analysis)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Results table
        results_group = QGroupBox(tr("Analysis Results"))
        results_layout = QVBoxLayout()
        
        # Top row: Select All + Batch Actions + Show Errors
        top_row_layout = QHBoxLayout()
        
        self.select_all_chk = QCheckBox(tr("Select All"))
        self.select_all_chk.stateChanged.connect(self.toggle_select_all)
        top_row_layout.addWidget(self.select_all_chk)
        
        top_row_layout.addSpacing(20)
        
        batch_label = QLabel(tr("Batch action:"))
        top_row_layout.addWidget(batch_label)
        
        self.batch_action_combo = QComboBox()
        self.batch_action_combo.addItems([tr("—"), tr("Set: Validate"), tr("Set: Delete")])
        self.batch_action_combo.currentIndexChanged.connect(self.apply_batch_action)
        self.batch_action_combo.setMinimumWidth(120)
        top_row_layout.addWidget(self.batch_action_combo)
        
        top_row_layout.addStretch()
        
        # NEW: Show errors on canvas checkbox
        self.show_errors_chk = QCheckBox(tr("Show on map"))
        self.show_errors_chk.setToolTip(tr("Display all errors on the map canvas"))
        self.show_errors_chk.stateChanged.connect(self._on_toggle_show_errors)
        self.show_errors_chk.setEnabled(False)
        top_row_layout.addWidget(self.show_errors_chk)
        
        self.selection_count_label = QLabel("")
        self.selection_count_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        top_row_layout.addWidget(self.selection_count_label)
        
        results_layout.addLayout(top_row_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "", tr("Type"), tr("ID A"), tr("ID B"),
            tr("Measure"), tr("Ratio"), tr("Severity"), tr("Action")
        ])
        self.results_table.cellDoubleClicked.connect(self.on_result_double_click)
        results_layout.addWidget(self.results_table)
        
        # Action buttons row
        btn_layout = QHBoxLayout()
        
        # Reset button now also refreshes layers
        self.reset_ui_btn = QPushButton(tr("🔄 Reset"))
        self.reset_ui_btn.clicked.connect(self.reset_ui)
        self.reset_ui_btn.setToolTip(tr("Reset interface and reload layers"))
        btn_layout.addWidget(self.reset_ui_btn)
        
        self.apply_corrections_btn = QPushButton(tr("🔧 Apply"))
        self.apply_corrections_btn.clicked.connect(self.apply_corrections)
        self.apply_corrections_btn.setEnabled(False)
        self.apply_corrections_btn.setToolTip(tr("Apply corrections based on Action column"))
        btn_layout.addWidget(self.apply_corrections_btn)
        
        self.export_csv_btn = QPushButton(tr("💾 Export"))
        self.export_csv_btn.clicked.connect(self.export_results)
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.setToolTip(tr("Export results to CSV/TXT"))
        btn_layout.addWidget(self.export_csv_btn)
        
        self.export_layer_btn = QPushButton(tr("📤 Layer"))
        self.export_layer_btn.clicked.connect(self.export_result_layer)
        self.export_layer_btn.setEnabled(False)
        self.export_layer_btn.setToolTip(tr("Export anomalies layer"))
        btn_layout.addWidget(self.export_layer_btn)
        
        results_layout.addLayout(btn_layout)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        panel.setLayout(layout)
        return panel
    
    def load_layers(self):
        """Load project layers into table"""
        try:
            self.layers_table.setRowCount(0)
            self.selected_layers.clear()
            self.id_fields.clear()
            
            row = 0
            for layer_id, layer in QgsProject.instance().mapLayers().items():
                if not isinstance(layer, QgsVectorLayer):
                    continue
                
                self.layers_table.insertRow(row)
                
                chk = QCheckBox()
                chk.stateChanged.connect(
                    lambda state, lid=layer_id: self.on_layer_selected(lid, state)
                )
                self.layers_table.setCellWidget(row, 0, chk)
                
                self.layers_table.setItem(row, 1, QTableWidgetItem(layer.name()))
                
                geom_type = {0: "Point", 1: "Line", 2: "Polygon"}.get(layer.geometryType(), "Unknown")
                self.layers_table.setItem(row, 2, QTableWidgetItem(geom_type))
                
                id_combo = QComboBox()
                id_combo.addItem(tr("FID"))
                for field in layer.fields():
                    id_combo.addItem(field.name())
                id_combo.currentTextChanged.connect(
                    lambda text, lid=layer_id: self.on_id_field_changed(lid, text)
                )
                self.layers_table.setCellWidget(row, 3, id_combo)
                
                row += 1
            
            self.layers_table.resizeColumnsToContents()
            self.log("info", tr("Loaded {} layers").format(row))
            
        except Exception as e:
            self.log("error", tr("Failed to load layers: {}").format(e))
    
    def on_layer_selected(self, layer_id: str, state: int):
        """Handle layer selection"""
        if state == Qt.Checked:
            if len(self.selected_layers) >= 4:
                QMessageBox.warning(self, tr("Limit"), tr("Maximum 4 layers allowed"))
                return
            self.selected_layers.add(layer_id)
        else:
            self.selected_layers.discard(layer_id)
        
        self.analyze_btn.setEnabled(len(self.selected_layers) > 0)
    
    def on_id_field_changed(self, layer_id: str, field_name: str):
        """Handle ID field selection"""
        if field_name == tr("FID"):
            self.id_fields.pop(layer_id, None)
        else:
            self.id_fields[layer_id] = field_name
    
    def start_analysis(self):
        """Start analysis task"""
        try:
            layers = self.get_layers_for_analysis()
            if not any(layers.values()):
                QMessageBox.warning(self, tr("Error"), tr("No layers selected"))
                return
            
            params = {
                'business_profile': self.profile_combo.currentText(),
                'min_overlap_area': PresetManager.EPSILON_AREA_DEFAULT,
                'max_point_distance': 10.0,
                'min_point_distance': PresetManager.EPSILON_DIST_DEFAULT,
            }
            
            self.current_task = AnalysisTask(layers, params, self.id_fields)
            self.current_task.log_message_signal.connect(self.log)
            self.current_task.taskCompleted.connect(self.on_analysis_complete)
            self.current_task.progressChanged.connect(self.on_progress_changed)
            
            self.analyze_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            QgsApplication.taskManager().addTask(self.current_task)
            self.log("info", tr("Analysis started..."))
            
        except Exception as e:
            self.log("error", tr("Failed to start analysis: {}").format(e))
            log_message('error', f"Analysis start failed: {e}", e)
    
    def cancel_analysis(self):
        """Cancel running analysis"""
        if self.current_task:
            self.current_task.cancel()
            self.log("warning", tr("Analysis canceled"))
        
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def on_progress_changed(self, progress: float):
        """Update progress bar"""
        self.progress_bar.setValue(int(progress))
    
    def on_analysis_complete(self):
        """Handle analysis completion"""
        try:
            if self.current_task and self.current_task.results:
                self.results = self.current_task.results
                
                ResultsTableManager.populate_table(
                    self.results_table, self.results, None
                )
                
                self._update_selection_count()
                
                crs = self.crs_selector.crs()
                self.result_layer = ResultLayerBuilder.create_result_layer(self.results, crs)
                
                if self.result_layer:
                    self._apply_topology_style(self.result_layer)
                
                # Enable buttons
                self.export_csv_btn.setEnabled(True)
                self.apply_corrections_btn.setEnabled(True)
                self.show_errors_chk.setEnabled(True)
                if self.result_layer:
                    self.export_layer_btn.setEnabled(True)
                
                self.log("info", tr("Analysis complete: {} results").format(len(self.results)))
            else:
                self.log("warning", tr("Analysis returned no results"))
            
        except Exception as e:
            self.log("error", tr("Error processing results: {}").format(e))
            log_message('error', f"Results processing failed: {e}", e)
        finally:
            self.analyze_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.current_task = None
    
    def get_layers_for_analysis(self) -> dict:
        """Get and merge selected layers by type"""
        layers_by_type = {'polygon': [], 'line': [], 'point': []}
        
        for layer_id in self.selected_layers:
            layer = QgsProject.instance().mapLayer(layer_id)
            if not layer:
                continue
            
            geom_type = layer.geometryType()
            if geom_type == 2:
                layers_by_type['polygon'].append(layer)
            elif geom_type == 1:
                layers_by_type['line'].append(layer)
            elif geom_type == 0:
                layers_by_type['point'].append(layer)
        
        result = {}
        for geom_type, layer_list in layers_by_type.items():
            if len(layer_list) == 0:
                result[geom_type] = None
            elif len(layer_list) == 1:
                result[geom_type] = layer_list[0]
            else:
                merged, error = merge_layers_to_temp(layer_list, f"merged_{geom_type}")
                if merged:
                    result[geom_type] = merged
                    self.log("info", tr("Merged {} {} layers").format(len(layer_list), geom_type))
                else:
                    self.log("error", tr("Merge failed: {}").format(error))
                    result[geom_type] = layer_list[0]
        
        return result
    
    def on_result_double_click(self, row: int, col: int):
        """Handle double-click on result row - zoom and highlight"""
        if 0 <= row < len(self.results):
            result = self.results[row]
            if self.viz_manager:
                self.viz_manager.highlight_and_zoom(result, self.selected_layers)
    
    def _on_toggle_show_errors(self, state: int):
        """Toggle display of all errors on canvas"""
        if self.viz_manager:
            if state == Qt.Checked:
                self.viz_manager.show_all_errors(self.results, color_by_severity=True)
                self.log("info", tr("Errors displayed on map"))
            else:
                self.viz_manager.hide_all_errors()
                self.log("info", tr("Errors hidden from map"))
    
    def reset_ui(self):
        """Reset UI for new analysis AND reload layers"""
        # Clear results
        self.results = []
        self.result_layer = None
        self.results_table.setRowCount(0)
        self.select_all_chk.setChecked(False)
        self.batch_action_combo.setCurrentIndex(0)
        self.selection_count_label.setText("")
        self.show_errors_chk.setChecked(False)
        self.show_errors_chk.setEnabled(False)
        
        # Clear log
        self.log_text.clear()
        
        # Clear highlights
        if self.viz_manager:
            self.viz_manager.clear_highlights()
        
        # Disable action buttons
        self.export_csv_btn.setEnabled(False)
        self.apply_corrections_btn.setEnabled(False)
        self.export_layer_btn.setEnabled(False)
        
        TempLayerTracker.cleanup_all()
        
        self.load_layers()        
        self.log("info", tr("✨ UI reset - Ready for new analysis"))
    
    def toggle_select_all(self, state: int):
        """Toggle all checkboxes in results table"""
        for row in range(self.results_table.rowCount()):
            widget = self.results_table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(state == Qt.Checked)
        self._update_selection_count()
    
    def apply_batch_action(self, index: int):
        """Apply batch action to selected rows"""
        if index == 0:
            return
        
        action_text = tr("Validate") if index == 1 else tr("Delete")
        action_col = self.results_table.columnCount() - 1
        
        affected = 0
        for row in range(self.results_table.rowCount()):
            chk_widget = self.results_table.cellWidget(row, 0)
            if not isinstance(chk_widget, QCheckBox) or not chk_widget.isChecked():
                continue
            
            action_widget = self.results_table.cellWidget(row, action_col)
            if isinstance(action_widget, QComboBox):
                idx = action_widget.findText(action_text)
                if idx >= 0:
                    action_widget.setCurrentIndex(idx)
                    affected += 1
        
        self.batch_action_combo.blockSignals(True)
        self.batch_action_combo.setCurrentIndex(0)
        self.batch_action_combo.blockSignals(False)
        
        if affected > 0:
            self.log("info", tr("Batch action '{}' applied to {} rows").format(action_text, affected))
    
    def _update_selection_count(self):
        """Update the selection count label"""
        checked = sum(
            1 for row in range(self.results_table.rowCount())
            if isinstance(self.results_table.cellWidget(row, 0), QCheckBox)
            and self.results_table.cellWidget(row, 0).isChecked()
        )
        total = self.results_table.rowCount()
        if total > 0:
            self.selection_count_label.setText(f"{checked}/{total} selected")
        else:
            self.selection_count_label.setText("")
    
    def apply_corrections(self):
        """Apply corrections based on Action column"""
        action_col = self.results_table.columnCount() - 1
        delete_count = 0
        for row in range(self.results_table.rowCount()):
            action_widget = self.results_table.cellWidget(row, action_col)
            if isinstance(action_widget, QComboBox) and action_widget.currentText() == tr("Delete"):
                delete_count += 1
        
        if delete_count == 0:
            QMessageBox.information(self, tr("Info"), tr("No features marked for deletion"))
            return
        
        reply = QMessageBox.question(
            self,
            tr("Confirm Corrections"),
            tr("Apply corrections?\n\n{} features marked for deletion will be removed.").format(delete_count),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            from ..core.layer_operations import LayerCorrector
            
            to_delete = {}
            
            for row in range(self.results_table.rowCount()):
                action_widget = self.results_table.cellWidget(row, action_col)
                if not isinstance(action_widget, QComboBox):
                    continue
                
                action = action_widget.currentText()
                if action != tr("Delete"):
                    continue
                
                if row >= len(self.results):
                    continue
                result = self.results[row]
                
                layer_a_id = result.get('layer_a_id')
                id_a = result.get('id_a_real', result.get('id_a'))
                
                if layer_a_id and id_a:
                    if layer_a_id not in to_delete:
                        to_delete[layer_a_id] = []
                    to_delete[layer_a_id].append(str(id_a))
            
            total_deleted = 0
            for layer_id, id_values in to_delete.items():
                layer = QgsProject.instance().mapLayer(layer_id)
                if not layer:
                    continue
                
                id_field = self.id_fields.get(layer_id)
                corrector = LayerCorrector(layer, id_field)
                
                success, error = corrector.apply_deletions(id_values)
                if success:
                    total_deleted += len(id_values)
                    self.log("info", tr("Deleted {} features from {}").format(len(id_values), layer.name()))
                else:
                    self.log("error", tr("Correction failed for {}: {}").format(layer.name(), error))
            
            if total_deleted > 0:
                QMessageBox.information(
                    self,
                    tr("Success"),
                    tr("Corrections applied: {} features deleted").format(total_deleted)
                )
                self.log("info", tr("💡 Tip: Re-run analysis to verify corrections"))
            
        except Exception as e:
            self.log("error", tr("Correction failed: {}").format(e))
            QMessageBox.critical(self, tr("Error"), str(e))
    
    def export_results(self):
        """Export results to CSV or TXT"""
        format_choice, ok = QInputDialog.getItem(
            self, tr("Export Format"), tr("Choose export format:"),
            ["CSV (;)", "TXT (Tab)"], 0, False
        )
        
        if not ok:
            return
        
        delimiter = ";" if "CSV" in format_choice else "\t"
        extension = ".csv" if "CSV" in format_choice else ".txt"
        
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Export Results"), "", f"{format_choice} (*{extension})"
        )
        
        if not path:
            return
        
        if not path.endswith(extension):
            path += extension
        
        try:
            summary_lines = ["=" * 80, tr("KAT OVERLAP ANALYSIS - RESULTS REPORT"), "=" * 80, ""]
            summary_lines.append(tr("ANALYSIS CONFIGURATION:"))
            summary_lines.append(f"  {tr('Business Profile')}: {self.profile_combo.currentText()}")
            summary_lines.append(f"  {tr('Selected Layers')}: {len(self.selected_layers)}")
            
            for layer_id in self.selected_layers:
                layer = QgsProject.instance().mapLayer(layer_id)
                if layer:
                    id_field = self.id_fields.get(layer_id, "FID")
                    summary_lines.append(f"    - {layer.name()} (ID: {id_field})")
            
            summary_lines.extend(["", tr("RESULTS SUMMARY:")])
            summary_lines.append(f"  {tr('Total anomalies found')}: {len(self.results)}")
            
            severity_counts = {}
            for result in self.results:
                sev = result.get('severity', 'Unknown')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for sev, count in sorted(severity_counts.items()):
                summary_lines.append(f"    - {sev}: {count}")
            
            summary_lines.extend(["", "=" * 80, ""])
            
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                for line in summary_lines:
                    f.write(line + "\n")
                
                writer = csv.writer(f, delimiter=delimiter)
                
                headers = [tr("N°")]
                for col in range(1, self.results_table.columnCount()):
                    header_item = self.results_table.horizontalHeaderItem(col)
                    headers.append(header_item.text() if header_item else f"Col{col}")
                writer.writerow(headers)
                
                row_num = 1
                for row in range(self.results_table.rowCount()):
                    widget = self.results_table.cellWidget(row, 0)
                    if not (isinstance(widget, QCheckBox) and widget.isChecked()):
                        continue
                    
                    row_data = [str(row_num)]
                    for col in range(1, self.results_table.columnCount()):
                        item = self.results_table.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            combo = self.results_table.cellWidget(row, col)
                            if isinstance(combo, QComboBox):
                                row_data.append(combo.currentText())
                            else:
                                row_data.append("")
                    
                    writer.writerow(row_data)
                    row_num += 1
            
            self.log("info", tr("Results exported: {}").format(path))
            QMessageBox.information(self, tr("Success"), tr("Export complete: {} rows").format(row_num - 1))
            
        except Exception as e:
            self.log("error", tr("Export failed: {}").format(e))
            QMessageBox.warning(self, tr("Error"), str(e))
    
    def export_result_layer(self):
        """Export result layer to file"""
        if not self.result_layer:
            QMessageBox.warning(self, tr("Error"), tr("No result layer available"))
            return
        
        path, selected_filter = QFileDialog.getSaveFileName(
            self, tr("Export Layer"), "",
            "GeoPackage (*.gpkg);;Shapefile (*.shp);;GeoJSON (*.geojson)"
        )
        
        if not path:
            return
        
        try:
            if "Shapefile" in selected_filter:
                if not path.endswith('.shp'):
                    path = path.rsplit('.', 1)[0] + '.shp'
                driver = "ESRI Shapefile"
            elif "GeoJSON" in selected_filter:
                if not path.endswith('.geojson'):
                    path = path.rsplit('.', 1)[0] + '.geojson'
                driver = "GeoJSON"
            else:
                if not path.endswith('.gpkg'):
                    path = path.rsplit('.', 1)[0] + '.gpkg'
                driver = "GPKG"
            
            success, error = ResultExporter.export_layer_to_file(
                self.result_layer, path, driver
            )
            
            if success:
                self.log("info", tr("Layer exported: {}").format(path))
                QMessageBox.information(self, tr("Success"), tr("Export complete"))
            else:
                self.log("error", tr("Export failed: {}").format(error))
                QMessageBox.warning(self, tr("Error"), error)
                
        except Exception as e:
            self.log("error", tr("Export failed: {}").format(e))
            QMessageBox.warning(self, tr("Error"), str(e))
    
    def _apply_topology_style(self, layer):
        """Apply red-green symbology like QGIS Topology Checker"""
        try:
            from qgis.PyQt.QtGui import QColor
            from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol
        except Exception:
            # if imports fail, abort silently
            return

        if layer is None:
            return

        # mapping canonical key -> translated label
        label_map = {
            'critical': self.tr('Critical'),
            'high': self.tr('High'),
            'moderate': self.tr('Moderate'),
            'low': self.tr('Low')
        }
        ordered_keys = ['critical', 'high', 'moderate', 'low']

        # Build categories only for keys actually present in the layer (to keep legend clean)
        present_keys = set()
        # Try to read values from features if possible
        try:
            if layer.fields().indexOf('severity') != -1:
                for f in layer.getFeatures():
                    v = f['severity']
                    if v is None:
                        continue
                    # normalize variants to canonical keys
                    s = str(v).strip().lower()
                    if 'crit' in s:
                        present_keys.add('critical')
                    elif 'high' in s:
                        present_keys.add('high')
                    elif 'mod' in s:
                        present_keys.add('moderate')
                    else:
                        present_keys.add('low')
        except Exception:
            # if we cannot iterate features (large layer), default to all keys
            present_keys = set(ordered_keys)

        # preserve order
        unique_keys = [k for k in ordered_keys if k in present_keys]

        categories = []
        for key in unique_keys:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if key == 'critical':
                symbol.setColor(QColor(255,0,0,180))
            elif key == 'high':
                symbol.setColor(QColor(255,165,0,180))
            elif key == 'moderate':
                symbol.setColor(QColor(255,200,0,140))
            else:
                symbol.setColor(QColor(0,255,0,140))
            symbol.setOpacity(0.75)
            categories.append(QgsRendererCategory(key, symbol, label_map.get(key, key)))

        if categories:
            renderer = QgsCategorizedSymbolRenderer('severity', categories)
            layer.setRenderer(renderer)
            try:
                layer.triggerRepaint()
            except Exception:
                pass
    
    def log(self, level: str, message: str):
        """Log message to UI and QGIS log"""
        colors = {'info': 'black', 'warning': 'orange', 'error': 'red', 'critical': 'darkred'}
        color = colors.get(level.lower(), 'black')
        
        self.log_text.append(f'<span style="color:{color};">[{level.upper()}] {message}</span>')
        log_message(level, message)
    
    def closeEvent(self, event):
        """Handle dialog close - reset UI state for next opening"""
        if self.viz_manager:
            self.viz_manager.clear_highlights()
        
        TempLayerTracker.cleanup_all()
        
        self.results = []
        self.result_layer = None
        self.current_task = None
        
        self.results_table.setRowCount(0)
        self.select_all_chk.setChecked(False)
        self.batch_action_combo.setCurrentIndex(0)
        self.selection_count_label.setText("")
        self.show_errors_chk.setChecked(False)
        self.show_errors_chk.setEnabled(False)
        
        self.log_text.clear()
        
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        
        self.export_csv_btn.setEnabled(False)
        self.apply_corrections_btn.setEnabled(False)
        self.export_layer_btn.setEnabled(False)
        
        self.analyze_btn.setEnabled(len(self.selected_layers) > 0)
        self.cancel_btn.setEnabled(False)
        
        event.accept()
