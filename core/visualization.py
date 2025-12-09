# -*- coding: utf-8 -*-
"""
KAT Analysis – Visualization
Thread-safe geometry highlighting and map canvas operations

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QMetaObject, Qt, QThread
from PyQt5.QtGui import QColor
from qgis.gui import QgsRubberBand, QgsMapCanvas
from qgis.core import QgsGeometry, QgsWkbTypes, QgsRectangle, QgsProject
from .utils import log_message, IDResolver, tr


# ==============ISUALIZATION COLORS===================

class VisualizationColors:
    """Standard colors for visualization"""
    
    # Severity colors
    CRITICAL = QColor(231, 76, 60, 180)    # Red
    HIGH = QColor(230, 126, 34, 180)       # Orange
    MODERATE = QColor(241, 196, 15, 180)   # Yellow
    LOW = QColor(39, 174, 96, 180)         # Green
    
    # Selection colors
    FEATURE_A = QColor(0, 0, 255, 100)     # Blue (semi-transparent)
    FEATURE_B = QColor(0, 255, 0, 100)     # Green (semi-transparent)
    CONFLICT = QColor(255, 215, 0, 200)    # Gold (more opaque)
    
    # Global error display
    GLOBAL_ERROR = QColor(255, 0, 0, 150)  # Red (semi-transparent)
    
    @staticmethod
    def get_severity_color(severity: str) -> QColor:
        """Get color for severity level"""
        severity_lower = severity.lower() if severity else ''
        
        if 'critical' in severity_lower:
            return VisualizationColors.CRITICAL
        elif 'high' in severity_lower:
            return VisualizationColors.HIGH
        elif 'moderate' in severity_lower:
            return VisualizationColors.MODERATE
        else:
            return VisualizationColors.LOW


# ==================RUBBERBAND MANAGER (Thread-Safe)===================

class RubberBandManager:
    """Thread-safe rubber band management for highlighting geometries"""
    
    def __init__(self, canvas: QgsMapCanvas):
        """Initialize manager"""
        self.canvas = canvas
        self.rubber_bands = []
    
    def clear_all(self):
        """Remove all rubber bands from canvas (thread-safe)"""
        def _clear():
            try:
                for rb in self.rubber_bands:
                    try:
                        self.canvas.scene().removeItem(rb)
                    except:
                        pass
                self.rubber_bands.clear()
            except Exception as e:
                log_message('warning', f"Rubber band cleanup failed: {e}")
        
        if QThread.currentThread() != self.canvas.thread():
            QMetaObject.invokeMethod(
                self.canvas,
                lambda: _clear(),
                Qt.QueuedConnection
            )
        else:
            _clear()
    
    def add_geometry(self, geometry: QgsGeometry, color: QColor = None,
                    width: int = 2, opacity: float = 0.6) -> Optional[QgsRubberBand]:
        """Add a geometry to highlight (thread-safe)"""
        if not geometry or geometry.isEmpty():
            return None
        
        if color is None:
            color = QColor(255, 0, 0)
        
        def _add():
            try:
                geom_type = geometry.type()
                if geom_type == QgsWkbTypes.PointGeometry:
                    rb_type = QgsWkbTypes.PointGeometry
                elif geom_type == QgsWkbTypes.LineGeometry:
                    rb_type = QgsWkbTypes.LineGeometry
                else:
                    rb_type = QgsWkbTypes.PolygonGeometry
                
                rb = QgsRubberBand(self.canvas, rb_type)
                rb.setToGeometry(geometry, None)
                rb.setColor(color)
                rb.setWidth(width)
                rb.setOpacity(opacity)
                
                self.rubber_bands.append(rb)
                return rb
            except Exception as e:
                log_message('error', f"Failed to add rubber band: {e}", e)
                return None
        
        if QThread.currentThread() != self.canvas.thread():
            result = [None]
            QMetaObject.invokeMethod(
                self.canvas,
                lambda: result.__setitem__(0, _add()),
                Qt.BlockingQueuedConnection
            )
            return result[0]
        else:
            return _add()
    
    def count(self) -> int:
        """Return number of rubber bands"""
        return len(self.rubber_bands)

# ============VISUALIZATION MANAGER==================

class VisualizationManager:
    """
    High-level visualization operations for analysis results.
    """
    
    def __init__(self, canvas: QgsMapCanvas):
        """Initialize manager"""
        self.canvas = canvas
        self.global_rb_manager = RubberBandManager(canvas)
        self._global_errors_visible = False
        self._rb_feature_a = None
        self._rb_feature_b = None
        self._rb_conflict = None
        self._init_selection_rubber_bands()
    
    def _init_selection_rubber_bands(self):
        """Create persistent rubber bands for selection (created once, reused)"""
        try:
            # Feature A - Blue
            self._rb_feature_a = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self._rb_feature_a.setColor(VisualizationColors.FEATURE_A)
            self._rb_feature_a.setWidth(2)
            self._rb_feature_a.setVisible(False)
            
            # Feature B - Green
            self._rb_feature_b = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self._rb_feature_b.setColor(VisualizationColors.FEATURE_B)
            self._rb_feature_b.setWidth(2)
            self._rb_feature_b.setVisible(False)
            
            # Conflict zone - Gold
            self._rb_conflict = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self._rb_conflict.setColor(VisualizationColors.CONFLICT)
            self._rb_conflict.setWidth(4)
            self._rb_conflict.setVisible(False)
            
        except Exception as e:
            log_message('error', f"Failed to initialize selection rubber bands: {e}")
    

    # =================GLOBAL ERROR DISPLAY====================
    
    def show_all_errors(self, results: List[Dict[str, Any]], 
                       color_by_severity: bool = True) -> int:
        """
        Display ALL error geometries on the canvas.
        
        :param results: List of result dictionaries
        :param color_by_severity: Use different colors per severity level
        :return: Number of errors displayed
        """
        # Clear existing global errors
        self.global_rb_manager.clear_all()
        
        count = 0
        for result in results:
            geom = self._extract_result_geometry(result)
            if geom and not geom.isEmpty():
                # Determine color
                if color_by_severity:
                    severity = result.get('severity', 'Low')
                    color = VisualizationColors.get_severity_color(severity)
                else:
                    color = VisualizationColors.GLOBAL_ERROR
                
                # Add rubber band
                rb = self.global_rb_manager.add_geometry(geom, color, width=3)
                if rb:
                    count += 1
        
        self._global_errors_visible = True
        self._refresh_canvas()
        log_message('info', f"Displaying {count} errors on canvas")
        return count
    
    def hide_all_errors(self):
        """Hide all global error displays"""
        self.global_rb_manager.clear_all()
        self._global_errors_visible = False
        self._refresh_canvas()
    
    def toggle_global_errors(self, results: List[Dict[str, Any]] = None,
                            color_by_severity: bool = True) -> bool:
        """
        Toggle global error display on/off.
        
        :param results: Results list (required if turning on)
        :param color_by_severity: Use severity colors
        :return: New visibility state
        """
        if self._global_errors_visible:
            self.hide_all_errors()
            return False
        else:
            if results:
                self.show_all_errors(results, color_by_severity)
            return True
    
    @property
    def global_errors_visible(self) -> bool:
        """Check if global errors are currently displayed"""
        return self._global_errors_visible
    

    # ================SELECTION HIGHLIGHT=====================
    
    def highlight_result(self, result: Dict[str, Any], 
                        selected_layer_ids: set = None) -> bool:
        """
        Highlight a single analysis result using persistent rubber bands.
        Does NOT clear global error display.
        
        :param result: Result dictionary
        :param selected_layer_ids: Set of selected layer IDs
        :return: Success status
        """
        try:
            # Hide previous selection
            self._hide_selection_rubber_bands()
            
            # Conflict geometry (yellow/gold)
            conflict_geom = self._extract_result_geometry(result)
            if conflict_geom and not conflict_geom.isEmpty():
                self._update_rubber_band(self._rb_conflict, conflict_geom, 
                                        VisualizationColors.CONFLICT)
            
            # Feature A geometry (blue)
            geom_a = self._resolve_feature_geometry(
                result.get('id_a_real') or result.get('id_a'),
                result.get('layer_a_id'),
                selected_layer_ids
            )
            if geom_a:
                self._update_rubber_band(self._rb_feature_a, geom_a,
                                        VisualizationColors.FEATURE_A)
            
            # Feature B geometry (green)
            geom_b = self._resolve_feature_geometry(
                result.get('id_b_real') or result.get('id_b'),
                result.get('layer_b_id'),
                selected_layer_ids
            )
            if geom_b:
                self._update_rubber_band(self._rb_feature_b, geom_b,
                                        VisualizationColors.FEATURE_B)
            
            self._refresh_canvas()
            return True
            
        except Exception as e:
            log_message('error', f"Highlight failed: {e}", e)
            return False
    
    def _update_rubber_band(self, rb: QgsRubberBand, geom: QgsGeometry, 
                           color: QColor = None):
        """Update a persistent rubber band with new geometry"""
        if not rb:
            return
        
        try:
            # Determine correct geometry type
            geom_type = geom.type()
            
            # Reset and update
            rb.reset(geom_type)
            rb.setToGeometry(geom, None)
            
            if color:
                rb.setColor(color)
            
            rb.setVisible(True)
            
        except Exception as e:
            log_message('warning', f"Failed to update rubber band: {e}")
    
    def _hide_selection_rubber_bands(self):
        """Hide selection rubber bands (but don't destroy them)"""
        for rb in [self._rb_feature_a, self._rb_feature_b, self._rb_conflict]:
            if rb:
                try:
                    rb.setVisible(False)
                except:
                    pass
    
    def zoom_to_result(self, result: Dict[str, Any],
                      selected_layer_ids: set = None, buffer: float = 10.0) -> bool:
        """
        Zoom to a result's extent with buffer.
        
        :param result: Result dictionary
        :param selected_layer_ids: Set of selected layer IDs
        :param buffer: Buffer distance in map units
        :return: Success status
        """
        try:
            geom = self._extract_result_geometry(result)
            
            if not geom or geom.isEmpty():
                # Fallback: combine source geometries
                geom_a = self._resolve_feature_geometry(
                    result.get('id_a_real') or result.get('id_a'),
                    result.get('layer_a_id'),
                    selected_layer_ids
                )
                geom_b = self._resolve_feature_geometry(
                    result.get('id_b_real') or result.get('id_b'),
                    result.get('layer_b_id'),
                    selected_layer_ids
                )
                
                if geom_a and geom_b:
                    geom = geom_a.combine(geom_b)
                elif geom_a:
                    geom = geom_a
                elif geom_b:
                    geom = geom_b
            
            if not geom or geom.isEmpty():
                log_message('warning', "No geometry to zoom to")
                return False
            
            # Get bounding box with buffer
            bbox = geom.boundingBox()
            bbox.grow(buffer)
            
            # Zoom (thread-safe)
            def _zoom():
                try:
                    self.canvas.setExtent(bbox)
                    self.canvas.refresh()
                except Exception as e:
                    log_message('error', f"Zoom failed: {e}", e)
            
            if QThread.currentThread() != self.canvas.thread():
                QMetaObject.invokeMethod(self.canvas, _zoom, Qt.QueuedConnection)
            else:
                _zoom()
            
            return True
            
        except Exception as e:
            log_message('error', f"Zoom to result failed: {e}", e)
            return False
    
    def highlight_and_zoom(self, result: Dict[str, Any],
                          selected_layer_ids: set = None) -> bool:
        """Highlight and zoom to result in one operation"""
        highlight_ok = self.highlight_result(result, selected_layer_ids)
        zoom_ok = self.zoom_to_result(result, selected_layer_ids)
        return highlight_ok or zoom_ok
    
    def clear_highlights(self):
        """Clear ALL highlights from canvas (global + selection)"""
        self._hide_selection_rubber_bands()
        self.global_rb_manager.clear_all()
        self._global_errors_visible = False
        self._refresh_canvas()
    
    def clear_selection_only(self):
        """Clear only selection highlights (keep global errors)"""
        self._hide_selection_rubber_bands()
        self._refresh_canvas()
    
    # ================HELPER METHODS===========================
    
    def _extract_result_geometry(self, result: Dict[str, Any]) -> Optional[QgsGeometry]:
        """Extract geometry from result dictionary"""
        # Try geometry_json
        geom_json = result.get('geometry_json')
        if geom_json:
            try:
                from qgis.core import QgsJsonUtils
                geom = QgsJsonUtils.geometryFromGeoJson(geom_json)
                if geom and not geom.isEmpty():
                    return geom
            except:
                pass
        
        # Try geometry_wkt
        geom_wkt = result.get('geometry_wkt')
        if geom_wkt:
            try:
                geom = QgsGeometry.fromWkt(str(geom_wkt))
                if geom and not geom.isEmpty():
                    return geom
            except:
                pass
        
        # Try overlap_geometry (legacy)
        overlap_geom = result.get('overlap_geometry')
        if overlap_geom and isinstance(overlap_geom, QgsGeometry):
            return overlap_geom
        
        return None
    
    def _resolve_feature_geometry(self, feature_id: Any, layer_id: str,
                                  selected_layer_ids: set = None) -> Optional[QgsGeometry]:
        """Resolve feature geometry from ID"""
        try:
            layer, feature = IDResolver.resolve_to_feature(
                feature_id, selected_layer_ids
            )
            if feature and feature.hasGeometry():
                return feature.geometry()
        except Exception as e:
            log_message('warning', f"Feature resolution failed: {e}")
        
        return None
    
    def _refresh_canvas(self):
        """Refresh canvas (thread-safe)"""
        def _refresh():
            try:
                self.canvas.refresh()
            except:
                pass
        
        if QThread.currentThread() != self.canvas.thread():
            QMetaObject.invokeMethod(self.canvas, _refresh, Qt.QueuedConnection)
        else:
            _refresh()
    
    def cleanup(self):
        """Cleanup all resources before destruction"""
        try:
            # Clear global errors
            self.global_rb_manager.clear_all()
            
            # Remove persistent rubber bands
            for rb in [self._rb_feature_a, self._rb_feature_b, self._rb_conflict]:
                if rb:
                    try:
                        self.canvas.scene().removeItem(rb)
                    except:
                        pass
            
            self._rb_feature_a = None
            self._rb_feature_b = None
            self._rb_conflict = None
            
        except Exception as e:
            log_message('warning', f"Visualization cleanup error: {e}")


# ================FACTORY FUNCTION==================

def create_visualization_manager(iface) -> Optional[VisualizationManager]:
    """
    Factory function to create VisualizationManager from iface
    
    :param iface: QGIS interface
    :return: VisualizationManager or None
    """
    try:
        canvas = iface.mapCanvas()
        if canvas:
            return VisualizationManager(canvas)
    except Exception as e:
        log_message('error', f"Failed to create visualization manager: {e}")
    
    return None
