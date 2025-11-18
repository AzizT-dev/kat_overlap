# -*- coding: utf-8 -*-
"""
KAT Analysis – Layer Helpers
Layer selection, loading and management utilities

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import Dict, List, Set, Any, Tuple
from PyQt5.QtWidgets import QMessageBox, QCheckBox, QComboBox, QTableWidgetItem, QTableWidget
from PyQt5.QtCore import Qt

from qgis.core import QgsProject, QgsVectorLayer
from .layer_manager import check_layers_compatibility, merge_layers_to_temp


class LayerSelectionManager:
    """
    Manages layer selection, loading from QGIS project, and multi-layer fusion logic.
    """
    
    @staticmethod
    def load_project_layers(dialog):
        """
        Load all vector layers from QGIS project into the layers table.
        
        Parameters:
        - dialog: UI dialog reference containing layers_table, layer_widgets, etc.
        """
        try:
            dialog.layers_table.setRowCount(0)
            dialog.all_layers = []
            dialog.layer_widgets = {}
            dialog.selected_layers.clear()
            row = 0
            
            for layer_id, lyr in QgsProject.instance().mapLayers().items():
                if not isinstance(lyr, QgsVectorLayer):
                    continue
                
                dialog.layers_table.insertRow(row)
                
                # Checkbox for layer selection
                chk = QCheckBox()
                chk.stateChanged.connect(
                    lambda state, lid=layer_id, cb=chk: 
                    LayerSelectionManager._on_layer_selection_changed(dialog, lid, state, cb)
                )
                dialog.layers_table.setCellWidget(row, 0, chk)
                
                # Layer name
                dialog.layers_table.setItem(row, 1, QTableWidgetItem(lyr.name()))
                
                # Geometry type
                dialog.layers_table.setItem(row, 2, QTableWidgetItem(
                    LayerSelectionManager._get_geometry_type_name(lyr)
                ))
                
                # ID field combo
                id_combo = QComboBox()
                id_combo.addItem(self.tr("Aucun"))
                for f in lyr.fields():
                    id_combo.addItem(f.name())
                id_combo.setMinimumHeight(27)
                id_combo.setMaximumHeight(32)
                id_combo.currentTextChanged.connect(
                    lambda txt, lid=layer_id: 
                    LayerSelectionManager._on_id_field_changed(dialog, lid, txt)
                )
                dialog.layers_table.setCellWidget(row, 3, id_combo)
                
                # Store widget references
                dialog.layer_widgets[layer_id] = {
                    'checkbox': chk,
                    'id_combo': id_combo,
                    'row': row,
                    'layer': lyr
                }
                row += 1
            
            dialog.layers_table.resizeColumnsToContents()
            LayerSelectionManager._update_analyze_button_state(dialog)
            
        except Exception as e:
            import traceback
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Layer loading error: {}\n{}").format(e, traceback.format_exc()))
    
    @staticmethod
    def _get_geometry_type_name(layer: QgsVectorLayer) -> str:
        """
        Get human-readable geometry type name.
        
        Parameters:
        - layer: QgsVectorLayer
        
        Returns:
        - Geometry type name (Point/Line/Polygon/Unknown)
        """
        gtype = layer.geometryType()
        return {0: self.tr("Point"), 1: self.tr("Ligne"), 2: self.tr("Polygone")}.get(gtype, self.tr("Inconnu"))
    
    @staticmethod
    def _on_layer_selection_changed(dialog, layer_id: str, state: int, checkbox_widget=None):
        """
        Handle layer selection checkbox state change.
        
        Parameters:
        - dialog: UI dialog reference
        - layer_id: Layer ID
        - state: Qt.Checked or Qt.Unchecked
        - checkbox_widget: QCheckBox widget for blocking signals if needed
        """
        try:
            if state == Qt.Checked:
                # Limit to 4 layers for performance
                if len(dialog.selected_layers) >= 4:
                    QMessageBox.warning(
                        dialog,
                        self.tr("Limitation"),
                        self.tr("Maximum 4 layers selected for performance reasons")
                    )
                    if checkbox_widget:
                        checkbox_widget.blockSignals(True)
                        checkbox_widget.setChecked(False)
                        checkbox_widget.blockSignals(False)
                    return
                dialog.selected_layers.add(layer_id)
            else:
                dialog.selected_layers.discard(layer_id)
            
            LayerSelectionManager._update_analyze_button_state(dialog)
            
        except Exception as e:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Layer selection error: {}").format(e))
    
    @staticmethod
    def _on_id_field_changed(dialog, layer_id: str, field_name: str):
        """
        Handle ID field combo selection change.
        
        Parameters:
        - dialog: UI dialog reference
        - layer_id: Layer ID
        - field_name: Selected field name
        """
        if field_name == self.tr("Aucun"):
            dialog.id_fields.pop(layer_id, None)
        else:
            dialog.id_fields[layer_id] = field_name
    
    @staticmethod
    def _update_analyze_button_state(dialog):
        """
        Enable/disable analyze button based on layer selection.
        
        Parameters:
        - dialog: UI dialog reference
        """
        if hasattr(dialog, 'btn_analyze'):
            dialog.btn_analyze.setEnabled(len(dialog.selected_layers) > 0)
    
    @staticmethod
    def get_selected_layers(dialog) -> Dict[str, QgsVectorLayer]:
        """
        Get selected layers with automatic fusion if multiple layers of same type.
        
        NEW in v2.3: If 2+ layers of same type → automatic fusion to temp layer
        
        Parameters:
        - dialog: UI dialog reference
        
        Returns:
        - Dictionary: {'polygon': layer_or_merged, 'line': layer_or_merged, 'point': layer_or_merged}
        """
        # 1. Collect selected layers from project
        layers_dict = {'polygon': [], 'line': [], 'point': []}
        
        for lid in dialog.selected_layers:
            layer = QgsProject.instance().mapLayer(lid)
            if not layer:
                continue
            
            geom_type = layer.geometryType()
            if geom_type == 2:
                layers_dict['polygon'].append(layer)
            elif geom_type == 1:
                layers_dict['line'].append(layer)
            elif geom_type == 0:
                layers_dict['point'].append(layer)
        
        result = {'polygon': None, 'line': None, 'point': None}
        
        # 2. For each geometry type
        for geom_type, layer_list in layers_dict.items():
            if not layer_list:
                continue
            
            # If single layer of this type: use directly
            if len(layer_list) == 1:
                result[geom_type] = layer_list[0]
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("✅ {}: {}").format(geom_type.capitalize(), layer_list[0].name()))
            
            # If 2+ layers of same type: merge them
            elif len(layer_list) >= 2:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("🔗 Merging {} {} layers...").format(len(layer_list), geom_type))
                
                # Check compatibility
                ok, msg = check_layers_compatibility(layer_list)
                if not ok:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("❌ {} incompatibility: {}").format(geom_type, msg))
                        dialog._log_message("info", self.tr("   → Using first layer only"))
                    result[geom_type] = layer_list[0]
                    continue
                
                # Merge layers
                merge_name = f"merged_{geom_type}_{len(layer_list)}"
                merged_layer, err = merge_layers_to_temp(layer_list, merge_name=merge_name)
                
                if err:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("❌ {} merge error: {}").format(geom_type, err))
                        dialog._log_message("info", self.tr("   → Using first layer only"))
                    result[geom_type] = layer_list[0]
                else:
                    # Success: use merged layer
                    result[geom_type] = merged_layer
                    feat_count = merged_layer.featureCount()
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("info", self.tr("✅ {} merge: {} features ({} layers)").format(geom_type, feat_count, len(layer_list)))
                        dialog._log_message("info", self.tr("   → Field '__source_layer_id' identifies source"))
        
        return result

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API."""
        from qgis.core import QgsApplication
        return QgsApplication.translate('LayerSelectionManager', message)