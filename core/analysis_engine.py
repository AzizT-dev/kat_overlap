# -*- coding: utf-8 -*-
"""
KAT Analysis – Analysis Engine
Main task orchestrator using separate analysis modules

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import Dict, Any
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    QgsTask, QgsVectorLayer, QgsDistanceArea, QgsProject
)
from .utils import log_message
from .classification import PresetManager

# Import analysis modules
from .polygon_analysis import PolygonAnalyzer
from .line_analysis import LineAnalyzer
from .point_analysis import PointAnalyzer, CadastralPointPolygonAnalyzer


class AnalysisTask(QgsTask):
    """
    QgsTask for performing spatial analysis with progress reporting.
    Orchestrates separate analysis modules for each geometry type.
    """
    
    # Signals for callbacks
    progress_updated = pyqtSignal(int, str)
    log_message_signal = pyqtSignal(str, str)  # level, message
    
    # Analysis type tracking for dynamic headers
    analysis_mode = None  # 'polygon', 'point_polygon', 'point', 'line'
    
    def __init__(self, layers: Dict[str, QgsVectorLayer], params: Dict[str, Any],
                 id_fields: Dict[str, str]):
        """
        Initialize analysis task.
        
        :param layers: Dict with keys 'polygon', 'line', 'point'
        :param params: Analysis parameters
        :param id_fields: Dict mapping layer_id to id_field_name
        """
        super().__init__('KAT Overlap Analysis', QgsTask.CanCancel)
        
        self.layers = layers
        self.params = params
        self.id_fields = id_fields
        self.results = []
        self.errors = []
        
        # Distance area calculator
        self.da = QgsDistanceArea()
        self.da.setSourceCrs(
            QgsProject.instance().crs(),
            QgsProject.instance().transformContext()
        )
        self.da.setEllipsoid(QgsProject.instance().ellipsoid())
        
        # Initialize analyzers
        self._init_analyzers()
    
    def _init_analyzers(self):
        """Initialize analysis modules"""
        self.polygon_analyzer = PolygonAnalyzer(
            self.da, self.id_fields, self.params,
            log_callback=self._emit_log,
            cancel_check=self.isCanceled
        )
        
        self.line_analyzer = LineAnalyzer(
            self.da, self.id_fields, self.params,
            log_callback=self._emit_log,
            cancel_check=self.isCanceled
        )
        
        self.point_analyzer = PointAnalyzer(
            self.da, self.id_fields, self.params,
            log_callback=self._emit_log,
            cancel_check=self.isCanceled
        )
        
        self.cadastral_analyzer = CadastralPointPolygonAnalyzer(
            self.da, self.id_fields, self.params,
            log_callback=self._emit_log,
            cancel_check=self.isCanceled
        )
    
    def run(self) -> bool:
        """Execute analysis with proper geometry type separation"""
        try:
            self._emit_log('info', 'Starting analysis...')
            
            polygon_layer = self.layers.get('polygon')
            line_layer = self.layers.get('line')
            point_layer = self.layers.get('point')
            
            # Determine analysis type and steps
            has_polygon = polygon_layer is not None
            has_point = point_layer is not None
            has_line = line_layer is not None
            
            total_steps = self._calculate_total_steps(has_polygon, has_point, has_line)
            current_step = 0
            
            # CASE 1: Polygon-only analysis
            if has_polygon and not has_point and not self.isCanceled():
                current_step = self._run_polygon_analysis(
                    polygon_layer, current_step, total_steps
                )
            
            # CASE 2: Point-Polygon cadastral topology
            elif has_polygon and has_point and not self.isCanceled():
                current_step = self._run_cadastral_analysis(
                    point_layer, polygon_layer, current_step, total_steps
                )
            
            # CASE 3: Point-only proximity
            elif has_point and not has_polygon and not self.isCanceled():
                current_step = self._run_point_analysis(
                    point_layer, current_step, total_steps
                )
            
            # CASE 4: Line topology analysis
            if has_line and not self.isCanceled():
                current_step = self._run_line_analysis(
                    line_layer, current_step, total_steps
                )
            
            # Deduplicate results (remove inter-layer duplicates of self-overlaps)
            self._deduplicate_results()
            
            self.setProgress(100)
            self._emit_log('info', f'✅ Analysis complete: {len(self.results)} anomalies found')
            return True
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log_message('critical', f"Analysis failed: {e}\n{tb}", e)
            self._emit_log('critical', f"❌ Analysis failed: {e}")
            self.errors.append(str(e))
            return False
    
    def _calculate_total_steps(self, has_polygon: bool, has_point: bool, has_line: bool) -> int:
        """Calculate total analysis steps for progress tracking"""
        total_steps = 0
        
        if has_polygon and not has_point:
            total_steps += 2  # polygon self + inter
            self.analysis_mode = 'polygon'
        if has_polygon and has_point:
            total_steps += 4  # cadastral checks
            self.analysis_mode = 'point_polygon'
        if has_point and not has_polygon:
            total_steps += 1  # point proximity only
            self.analysis_mode = 'point'
        if has_line:
            total_steps += 3  # line self-intersections + overlaps + dangles
            if not self.analysis_mode:
                self.analysis_mode = 'line'
        
        return max(total_steps, 1)
    
    def _run_polygon_analysis(self, layer: QgsVectorLayer, 
                              current_step: int, total_steps: int) -> int:
        """Run polygon overlap analysis"""
        # Self-overlaps
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing polygon self-overlaps...')
        
        results = self.polygon_analyzer.analyze_self_overlaps(layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Inter-layer overlaps
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing polygon inter-layer overlaps...')
        
        results = self.polygon_analyzer.analyze_inter_layer_overlaps(layer)
        self.results.extend(results)
        current_step += 1
        
        return current_step
    
    def _run_cadastral_analysis(self, point_layer: QgsVectorLayer,
                                polygon_layer: QgsVectorLayer,
                                current_step: int, total_steps: int) -> int:
        """Run cadastral point-polygon topology analysis"""
        self._emit_log('info', '📍 Cadastral Point-Polygon Topology Analysis')
        
        # Check 1: ID matching
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Checking ID associations (point ↔ polygon)...')
        
        results = self.cadastral_analyzer.check_id_matching(point_layer, polygon_layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Check 2: Vertex count
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Validating vertex counts...')
        
        results = self.cadastral_analyzer.check_vertex_count(point_layer, polygon_layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Check 3: Coordinate precision
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Checking point-vertex coordinate match...')
        
        results = self.cadastral_analyzer.check_coordinate_precision(point_layer, polygon_layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Check 4: Shared vertices
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Validating shared vertices (contiguous parcels)...')
        
        results = self.cadastral_analyzer.check_shared_vertices(polygon_layer, point_layer)
        self.results.extend(results)
        current_step += 1
        
        return current_step
    
    def _run_point_analysis(self, layer: QgsVectorLayer,
                           current_step: int, total_steps: int) -> int:
        """Run point proximity analysis"""
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing point proximity...')
        
        results = self.point_analyzer.analyze_proximity(layer)
        self.results.extend(results)
        current_step += 1
        
        return current_step
    
    def _run_line_analysis(self, layer: QgsVectorLayer,
                          current_step: int, total_steps: int) -> int:
        """Run line topology analysis"""
        # Self-intersections
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing line self-intersections...')
        
        results = self.line_analyzer.analyze_self_intersections(layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Overlaps
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing line overlaps...')
        
        results = self.line_analyzer.analyze_overlaps(layer)
        self.results.extend(results)
        current_step += 1
        
        if self.isCanceled():
            return current_step
        
        # Dangles
        self.setProgress(int((current_step / total_steps) * 100))
        self._emit_log('info', '🔍 Analyzing line dangles...')
        
        results = self.line_analyzer.analyze_dangles(layer)
        self.results.extend(results)
        current_step += 1
        
        return current_step
    
    def finished(self, result: bool):
        """Called when task finishes"""
        if result:
            log_message('info', 'Analysis task completed successfully')
        else:
            log_message('error', f'Analysis task failed: {self.errors}')
    
    def cancel(self):
        """Cancel the task"""
        self._emit_log('warning', '⚠️ Analysis canceled by user')
        super().cancel()
    
    def _deduplicate_results(self):
        """
        Remove duplicate results between self-overlaps and inter-layer overlaps.
        
        When two features from different source layers overlap, they are detected:
        1. Once as self-overlap in the merged layer
        2. Once as inter-layer overlap via __source_layer_id
        
        This method keeps only the inter-layer version (more informative).
        """
        if not self.results:
            return
        
        # Build set of (id_a_real, id_b_real) pairs from self-overlaps
        self_overlap_pairs = set()
        for result in self.results:
            if result.get('type') == 'polygon_overlap':
                id_a = result.get('id_a_real', result.get('id_a', ''))
                id_b = result.get('id_b_real', result.get('id_b', ''))
                # Normalize pair order
                pair = tuple(sorted([str(id_a), str(id_b)]))
                self_overlap_pairs.add(pair)
        
        # Filter: remove self-overlaps that also exist as inter-layer overlaps
        inter_layer_pairs = set()
        for result in self.results:
            if result.get('type') == 'inter_layer_overlap':
                id_a = result.get('id_a_real', result.get('id_a', ''))
                id_b = result.get('id_b_real', result.get('id_b', ''))
                pair = tuple(sorted([str(id_a), str(id_b)]))
                inter_layer_pairs.add(pair)
        
        # Find duplicates
        duplicates = self_overlap_pairs & inter_layer_pairs
        
        if duplicates:
            # Remove self-overlap entries that are duplicates
            original_count = len(self.results)
            self.results = [
                r for r in self.results
                if not (
                    r.get('type') == 'polygon_overlap' and
                    tuple(sorted([
                        str(r.get('id_a_real', r.get('id_a', ''))),
                        str(r.get('id_b_real', r.get('id_b', '')))
                    ])) in duplicates
                )
            ]
            removed = original_count - len(self.results)
            if removed > 0:
                self._emit_log('info', f'   → Removed {removed} duplicate(s) (self ↔ inter-layer)')
    
    def _emit_log(self, level: str, message: str):
        """Emit log message via signal"""
        try:
            self.log_message_signal.emit(level, message)
        except:
            log_message(level, message)