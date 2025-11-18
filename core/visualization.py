# -*- coding: utf-8 -*-
"""
KAT Analysis – Visualization  
Geometry highlighting and zoom utilities

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any
from qgis.gui import QgsRubberBand
from qgis.core import QgsRectangle, QgsWkbTypes
from PyQt5.QtGui import QColor


class VisualizationManager:
    """
    Manages geometry highlighting with rubber bands and zoom operations.
    """
    
    @staticmethod
    def highlight_overlap(dialog, row_idx: int, result: Dict[str, Any]):
        """
        Highlight geometries for a single result row.
        
        Parameters:
        - dialog: UI dialog reference (for accessing iface, overlap_geometries)
        - row_idx: Row index
        - result: Result dictionary containing geometry info
        """
        try:
            # Clear existing rubber bands
            if hasattr(dialog, '_current_rubber_bands'):
                for rb in dialog._current_rubber_bands:
                    try:
                        dialog.iface.mapCanvas().scene().removeItem(rb)
                    except Exception:
                        pass
                dialog._current_rubber_bands.clear()
            else:
                dialog._current_rubber_bands = []
            
            # Get geometries
            layer_a = result.get("layer_a", {})
            layer_b = result.get("layer_b", {})
            
            # Highlight layer_a geometry (red)
            if isinstance(layer_a, dict):
                feat_a = layer_a.get("feature")
                if feat_a and feat_a.hasGeometry():
                    rb = QgsRubberBand(dialog.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
                    rb.setToGeometry(feat_a.geometry(), None)
                    rb.setColor(QColor(255, 0, 0, 100))
                    rb.setWidth(2)
                    dialog._current_rubber_bands.append(rb)
            
            # Highlight layer_b geometry (blue)
            if isinstance(layer_b, dict):
                feat_b = layer_b.get("feature")
                if feat_b and feat_b.hasGeometry():
                    rb = QgsRubberBand(dialog.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
                    rb.setToGeometry(feat_b.geometry(), None)
                    rb.setColor(QColor(0, 0, 255, 100))
                    rb.setWidth(2)
                    dialog._current_rubber_bands.append(rb)
            
            # Highlight overlap geometry (yellow)
            overlap_geom = result.get("overlap_geometry")
            if overlap_geom and not overlap_geom.isEmpty():
                rb = QgsRubberBand(dialog.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
                rb.setToGeometry(overlap_geom, None)
                rb.setColor(QColor(255, 255, 0, 150))
                rb.setWidth(3)
                dialog._current_rubber_bands.append(rb)
            
            dialog.iface.mapCanvas().refresh()
        
        except Exception as e:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Highlight error: {}").format(e))
    
    @staticmethod
    def build_overlap_geometries_from_results(dialog, results: List[Dict[str, Any]]):
        """
        Build overlap geometries list from results for quick access.
        
        Parameters:
        - dialog: UI dialog reference
        - results: List of analysis results
        """
        try:
            dialog.overlap_geometries = []
            
            for res in results:
                geom = res.get("overlap_geometry")
                if geom and not geom.isEmpty():
                    dialog.overlap_geometries.append(geom)
        
        except Exception as e:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("error", self.tr("Build overlap geometries error: {}").format(e))
    
    @staticmethod
    def get_min_display_area_from_params(dialog) -> float:
        """
        Get minimum display area from analysis parameters.
        
        Parameters:
        - dialog: UI dialog reference
        
        Returns:
        - Minimum display area in m²
        """
        if hasattr(dialog, 'params'):
            return dialog.params.get('min_display_area', 1.0)
        return 1.0

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API."""
        from qgis.core import QgsApplication
        return QgsApplication.translate('VisualizationManager', message)