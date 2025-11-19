# -*- coding: utf-8 -*-
"""
KAT Analysis – Layer Helpers
Layer selection, loading, and management utilities (English texts)

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import Dict, List
from PyQt5.QtWidgets import QMessageBox, QCheckBox, QComboBox, QTableWidgetItem
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsVectorLayer
from .layer_manager import check_layers_compatibility, merge_layers_to_temp


class LayerSelectionManager:
    """Manages layer selection, loading, and merging (English texts)."""

    @staticmethod
    def load_project_layers(dialog):
        """Load all vector layers into the table (English texts)."""
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

                chk = QCheckBox()
                chk.stateChanged.connect(
                    lambda state, lid=layer_id, cb=chk:
                    LayerSelectionManager._on_layer_selection_changed(dialog, lid, state, cb)
                )
                dialog.layers_table.setCellWidget(row, 0, chk)

                dialog.layers_table.setItem(row, 1, QTableWidgetItem(lyr.name()))
                dialog.layers_table.setItem(row, 2, QTableWidgetItem(
                    LayerSelectionManager._get_geometry_type_name(lyr)
                ))

                id_combo = QComboBox()
                id_combo.addItem(LayerSelectionManager.tr("None"))
                for f in lyr.fields():
                    id_combo.addItem(f.name())
                id_combo.setMinimumHeight(27)
                id_combo.setMaximumHeight(32)
                id_combo.currentTextChanged.connect(
                    lambda txt, lid=layer_id:
                    LayerSelectionManager._on_id_field_changed(dialog, lid, txt)
                )
                dialog.layers_table.setCellWidget(row, 3, id_combo)

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
                dialog._log_message("error", LayerSelectionManager.tr(
                    "Layer loading error: {}\n{}").format(e, traceback.format_exc()))

    @staticmethod
    def _get_geometry_type_name(layer: QgsVectorLayer) -> str:
        gtype = layer.geometryType()
        return {0: LayerSelectionManager.tr("Point"),
                1: LayerSelectionManager.tr("Line"),
                2: LayerSelectionManager.tr("Polygon")}.get(gtype, LayerSelectionManager.tr("Unknown"))

    @staticmethod
    def _on_layer_selection_changed(dialog, layer_id: str, state: int, checkbox_widget=None):
        try:
            if state == Qt.Checked:
                if len(dialog.selected_layers) >= 4:
                    QMessageBox.warning(
                        dialog,
                        LayerSelectionManager.tr("Limit"),
                        LayerSelectionManager.tr("Maximum 4 layers selected for performance")
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
                dialog._log_message("error", LayerSelectionManager.tr(
                    "Layer selection error: {}").format(e))

    @staticmethod
    def _on_id_field_changed(dialog, layer_id: str, field_name: str):
        if field_name == LayerSelectionManager.tr("None"):
            dialog.id_fields.pop(layer_id, None)
        else:
            dialog.id_fields[layer_id] = field_name

    @staticmethod
    def _update_analyze_button_state(dialog):
        if hasattr(dialog, 'btn_analyze'):
            dialog.btn_analyze.setEnabled(len(dialog.selected_layers) > 0)

    @staticmethod
    def get_selected_layers(dialog) -> Dict[str, QgsVectorLayer]:
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

        for geom_type, layer_list in layers_dict.items():
            if not layer_list:
                continue

            if len(layer_list) == 1:
                result[geom_type] = layer_list[0]
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", LayerSelectionManager.tr(
                        "✅ {}: {}").format(geom_type.capitalize(), layer_list[0].name()))
            else:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", LayerSelectionManager.tr(
                        "🔗 Merging {} {} layers...").format(len(layer_list), geom_type))

                ok, msg = check_layers_compatibility(layer_list)
                if not ok:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", LayerSelectionManager.tr(
                            "❌ {} incompatibility: {}").format(geom_type, msg))
                        dialog._log_message("info", LayerSelectionManager.tr("   → Using first layer only"))
                    result[geom_type] = layer_list[0]
                    continue

                merge_name = f"merged_{geom_type}_{len(layer_list)}"
                merged_layer, err = merge_layers_to_temp(layer_list, merge_name=merge_name)

                if err:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", LayerSelectionManager.tr(
                            "❌ {} merge error: {}").format(geom_type, err))
                        dialog._log_message("info", LayerSelectionManager.tr("   → Using first layer only"))
                    result[geom_type] = layer_list[0]
                else:
                    result[geom_type] = merged_layer
                    feat_count = merged_layer.featureCount()
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("info", LayerSelectionManager.tr(
                            "✅ {} merge: {} features ({} layers)").format(geom_type, feat_count, len(layer_list)))
                        dialog._log_message("info", LayerSelectionManager.tr(
                            "   → Field '__source_layer_id' identifies source"))

        return result

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API."""
        from qgis.core import QgsApplication
        return QgsApplication.translate('LayerSelectionManager', message)
