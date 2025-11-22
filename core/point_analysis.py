# -*- coding: utf-8 -*-
"""
KAT Analysis – Point Analysis Module
Point proximity and cadastral point-polygon topology checks

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Callable
from collections import defaultdict
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsDistanceArea,
    QgsWkbTypes, QgsSpatialIndex, QgsRectangle, QgsPointXY
)
from .utils import log_message, normalize_result
from .classification import PresetManager


class PointAnalyzer:
    """
    Point analysis including:
    - Point proximity (duplicate/near-duplicate detection)
    - Cadastral point-polygon topology checks
    """
    
    def __init__(self, da: QgsDistanceArea, id_fields: Dict[str, str],
                 params: Dict[str, Any], log_callback: Callable = None,
                 cancel_check: Callable = None):
        """
        Initialize point analyzer.
        
        :param da: QgsDistanceArea for measurements
        :param id_fields: Dict mapping layer_id to id_field_name
        :param params: Analysis parameters
        :param log_callback: Function to emit log messages
        :param cancel_check: Function to check if analysis should cancel
        """
        self.da = da
        self.id_fields = id_fields
        self.params = params
        self.log_callback = log_callback or (lambda l, m: None)
        self.cancel_check = cancel_check or (lambda: False)
    
    def _emit_log(self, level: str, message: str):
        """Emit log message"""
        self.log_callback(level, message)
    
    def _get_preset(self):
        """Get classification preset from params"""
        profile_name = self.params.get('business_profile', 'Land Registry/Cadastre (GPS ±2m)')
        return PresetManager.get_preset(profile_name)
    
    def _get_id_value(self, feature: QgsFeature, layer: QgsVectorLayer) -> str:
        """Get ID value for a feature using configured ID field"""
        layer_id = layer.id()
        id_field = self.id_fields.get(layer_id)
        
        if id_field and id_field in [f.name() for f in layer.fields()]:
            value = feature[id_field]
            if value is not None:
                return str(value)
        
        return str(feature.id())
    
    def analyze_proximity(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze point proximity using spatial index.
        Detects points that are closer than max_point_distance threshold.
        
        :param layer: Point layer to analyze
        :return: List of proximity results
        """
        results = []
        preset = self._get_preset()
        max_distance = self.params.get('max_point_distance', 10.0)
        min_distance = self.params.get('min_point_distance', PresetManager.EPSILON_DIST_DEFAULT)
        
        # Build spatial index
        index = QgsSpatialIndex()
        features_dict = {}
        
        for feat in layer.getFeatures():
            if self.cancel_check():
                return results
            if feat.hasGeometry() and not feat.geometry().isEmpty():
                index.addFeature(feat)
                features_dict[feat.id()] = feat
        
        # Process features
        processed_pairs = set()
        proximity_found = 0
        
        for fid, feat_a in features_dict.items():
            if self.cancel_check():
                return results
            
            geom_a = feat_a.geometry()
            point_a = geom_a.asPoint()
            
            # Search in buffer around point
            search_rect = QgsRectangle(
                point_a.x() - max_distance, point_a.y() - max_distance,
                point_a.x() + max_distance, point_a.y() + max_distance
            )
            candidate_ids = index.intersects(search_rect)
            
            for cid in candidate_ids:
                if cid <= fid:
                    continue
                
                pair_key = tuple(sorted([fid, cid]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                feat_b = features_dict.get(cid)
                if not feat_b:
                    continue
                
                geom_b = feat_b.geometry()
                point_b = geom_b.asPoint()
                
                try:
                    distance = point_a.distance(point_b)
                    
                    if min_distance <= distance <= max_distance:
                        severity = PresetManager.classify_point_proximity(
                            distance, preset, min_distance
                        )
                        
                        line_geom = QgsGeometry.fromPolylineXY([
                            QgsPointXY(point_a), QgsPointXY(point_b)
                        ])
                        
                        result = {
                            'type': 'point_proximity',
                            'anomaly': 'point_proximity',
                            'id_a': str(fid),
                            'id_b': str(cid),
                            'id_a_real': self._get_id_value(feat_a, layer),
                            'id_b_real': self._get_id_value(feat_b, layer),
                            'layer_a_id': layer.id(),
                            'layer_b_id': layer.id(),
                            'measure': distance,
                            'area_m2': 0.0,
                            'severity': severity,
                            'geometry_json': line_geom.asJson(),
                            'ratio': 0.0,
                            'ratio_percent': 0.0
                        }
                        
                        results.append(normalize_result(result))
                        proximity_found += 1
                        
                except Exception as e:
                    log_message('warning', f"Point proximity test failed for {fid}/{cid}: {e}")
                    continue
        
        self._emit_log('info', f'   → {proximity_found} proximity issues found')
        return results


class CadastralPointPolygonAnalyzer:
    """
    Cadastral topology analysis between point and polygon layers.
    Checks:
    1. ID matching (orphan points)
    2. Vertex count matching
    3. Point-vertex coordinate precision
    4. Shared vertices between adjacent polygons
    """
    
    def __init__(self, da: QgsDistanceArea, id_fields: Dict[str, str],
                 params: Dict[str, Any], log_callback: Callable = None,
                 cancel_check: Callable = None):
        self.da = da
        self.id_fields = id_fields
        self.params = params
        self.log_callback = log_callback or (lambda l, m: None)
        self.cancel_check = cancel_check or (lambda: False)
    
    def _emit_log(self, level: str, message: str):
        self.log_callback(level, message)
    
    def _get_polygon_vertices(self, geom: QgsGeometry) -> List:
        """Extract vertices from polygon geometry, excluding closing vertex"""
        vertices = []
        if not geom or geom.isEmpty():
            return vertices
        
        geom_type = geom.wkbType()
        try:
            if QgsWkbTypes.isMultiType(geom_type):
                multi = geom.asMultiPolygon()
                if multi:
                    for polygon in multi:
                        if polygon and polygon[0]:
                            ring = polygon[0]
                            vertices.extend(ring[:-1] if len(ring) > 1 else ring)
            else:
                poly = geom.asPolygon()
                if poly and poly[0]:
                    ring = poly[0]
                    vertices = list(ring[:-1] if len(ring) > 1 else ring)
        except Exception as e:
            log_message('warning', f"Error extracting vertices: {e}")
        return vertices
    
    def check_id_matching(self, point_layer: QgsVectorLayer, 
                         polygon_layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """Check 1: Points must have matching polygon IDs"""
        results = []
        
        point_id_field = self.id_fields.get(point_layer.id())
        poly_id_field = self.id_fields.get(polygon_layer.id())
        
        if not point_id_field or not poly_id_field:
            self._emit_log('warning', '   ⚠️ ID fields not configured - skipping ID matching')
            return results
        
        # Collect polygon IDs
        polygon_ids = set()
        for feat in polygon_layer.getFeatures():
            if self.cancel_check():
                return results
            pid = feat[poly_id_field]
            if pid is not None:
                polygon_ids.add(str(pid))
        
        # Check point IDs
        orphan_points = 0
        for feat in point_layer.getFeatures():
            if self.cancel_check():
                return results
            point_id = feat[point_id_field]
            if point_id is None:
                continue
            
            if str(point_id) not in polygon_ids:
                orphan_points += 1
                result = {
                    'type': 'orphan_point',
                    'anomaly': 'orphan_point',
                    'id_a': str(feat.id()),
                    'id_a_real': str(point_id),
                    'id_b': '',
                    'id_b_real': '',
                    'layer_a_id': point_layer.id(),
                    'layer_b_id': '',
                    'measure': 0.0,
                    'area_m2': 0.0,
                    'severity': 'Critical',
                    'geometry_json': feat.geometry().asJson() if feat.hasGeometry() else '',
                    'ratio': 0.0,
                    'ratio_percent': 0.0
                }
                results.append(normalize_result(result))
        
        self._emit_log('info', f'   → {orphan_points} orphan points (no matching polygon)')
        return results
    
    def check_vertex_count(self, point_layer: QgsVectorLayer,
                          polygon_layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """Check 2: Number of points must match polygon vertex count"""
        results = []
        
        point_id_field = self.id_fields.get(point_layer.id())
        poly_id_field = self.id_fields.get(polygon_layer.id())
        
        if not point_id_field or not poly_id_field:
            self._emit_log('warning', '   ⚠️ ID fields not configured - skipping vertex count check')
            return results
        
        # Count points per polygon ID
        points_per_id = {}
        for feat in point_layer.getFeatures():
            if self.cancel_check():
                return results
            pid = feat[point_id_field]
            if pid is not None:
                pid_str = str(pid)
                points_per_id[pid_str] = points_per_id.get(pid_str, 0) + 1
        
        # Check polygon vertex counts
        mismatches = 0
        for feat in polygon_layer.getFeatures():
            if self.cancel_check():
                return results
            poly_id = feat[poly_id_field]
            if poly_id is None:
                continue
            
            poly_id_str = str(poly_id)
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue
            
            vertices = self._get_polygon_vertices(geom)
            expected_count = len(vertices)
            actual_count = points_per_id.get(poly_id_str, 0)
            
            if expected_count != actual_count:
                mismatches += 1
                result = {
                    'type': 'vertex_count_mismatch',
                    'anomaly': 'vertex_count_mismatch',
                    'id_a': str(feat.id()),
                    'id_a_real': poly_id_str,
                    'id_b': f'Expected: {expected_count}, Found: {actual_count}',
                    'id_b_real': '',
                    'layer_a_id': polygon_layer.id(),
                    'layer_b_id': point_layer.id(),
                    'measure': abs(expected_count - actual_count),
                    'area_m2': 0.0,
                    'severity': 'High',
                    'geometry_json': geom.asJson(),
                    'ratio': 0.0,
                    'ratio_percent': 0.0
                }
                results.append(normalize_result(result))
        
        self._emit_log('info', f'   → {mismatches} vertex count mismatches')
        return results
    
    def check_coordinate_precision(self, point_layer: QgsVectorLayer,
                                   polygon_layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """Check 3: Point coordinates must match polygon vertex coordinates"""
        results = []
        
        point_id_field = self.id_fields.get(point_layer.id())
        poly_id_field = self.id_fields.get(polygon_layer.id())
        tolerance = 0.001  # 1mm
        
        if not point_id_field or not poly_id_field:
            self._emit_log('warning', '   ⚠️ ID fields not configured - skipping coordinate check')
            return results
        
        # Index points by polygon ID
        points_by_id = defaultdict(list)
        for feat in point_layer.getFeatures():
            if self.cancel_check():
                return results
            pid = feat[point_id_field]
            if pid is not None and feat.hasGeometry():
                pt = feat.geometry().asPoint()
                points_by_id[str(pid)].append((pt.x(), pt.y(), feat))
        
        # Check polygon vertices
        mismatches_found = 0
        for poly_feat in polygon_layer.getFeatures():
            if self.cancel_check():
                return results
            
            poly_id = str(poly_feat[poly_id_field]) if poly_feat[poly_id_field] else None
            if not poly_id or poly_id not in points_by_id:
                continue
            
            geom = poly_feat.geometry()
            if not geom or geom.isEmpty():
                continue
            
            try:
                vertices = self._get_polygon_vertices(geom)
                vertex_coords = [(v.x(), v.y()) for v in vertices]
            except Exception as e:
                log_message('warning', f"Failed to extract vertices for polygon {poly_id}: {e}")
                continue
            
            for x, y, point_feat in points_by_id[poly_id]:
                matched = any(
                    ((x - vx)**2 + (y - vy)**2)**0.5 <= tolerance
                    for vx, vy in vertex_coords
                )
                
                if not matched:
                    mismatches_found += 1
                    result = {
                        'type': 'point_vertex_mismatch',
                        'anomaly': 'point_vertex_mismatch',
                        'id_a': str(point_feat.id()),
                        'id_a_real': poly_id,
                        'id_b': str(poly_feat.id()),
                        'id_b_real': poly_id,
                        'layer_a_id': point_layer.id(),
                        'layer_b_id': polygon_layer.id(),
                        'measure': 0.0,
                        'area_m2': 0.0,
                        'severity': 'Critical',
                        'geometry_json': point_feat.geometry().asJson(),
                        'ratio': 0.0,
                        'ratio_percent': 0.0
                    }
                    results.append(normalize_result(result))
        
        self._emit_log('info', f'   → {mismatches_found} coordinate mismatches found')
        return results
    
    def check_shared_vertices(self, polygon_layer: QgsVectorLayer,
                             point_layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """Check 4: Adjacent polygons must share vertices at common boundaries"""
        results = []
        poly_id_field = self.id_fields.get(polygon_layer.id())
        tolerance = 0.001
        
        # Build spatial index
        index = QgsSpatialIndex()
        poly_dict = {}
        
        for feat in polygon_layer.getFeatures():
            if self.cancel_check():
                return results
            if feat.hasGeometry() and not feat.geometry().isEmpty():
                index.addFeature(feat)
                poly_dict[feat.id()] = feat
        
        # Check pairs
        checked_pairs = set()
        issues_found = 0
        
        for fid, poly_feat in poly_dict.items():
            if self.cancel_check():
                return results
            
            geom = poly_feat.geometry()
            candidates = index.intersects(geom.boundingBox())
            
            for cid in candidates:
                if cid == fid:
                    continue
                
                pair_key = tuple(sorted([fid, cid]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                neighbor_feat = poly_dict.get(cid)
                if not neighbor_feat:
                    continue
                
                neighbor_geom = neighbor_feat.geometry()
                
                try:
                    if geom.touches(neighbor_geom):
                        boundary = geom.intersection(neighbor_geom)
                        if not boundary or boundary.isEmpty():
                            continue
                        
                        try:
                            if boundary.length() < 0.001:
                                continue
                        except:
                            continue
                        
                        vertices_a = set()
                        for v in self._get_polygon_vertices(geom):
                            vertices_a.add((round(v.x(), 3), round(v.y(), 3)))
                        
                        vertices_b = set()
                        for v in self._get_polygon_vertices(neighbor_geom):
                            vertices_b.add((round(v.x(), 3), round(v.y(), 3)))
                        
                        boundary_points = []
                        if boundary.type() == QgsWkbTypes.LineGeometry:
                            if boundary.asPolyline():
                                boundary_points = list(boundary.asPolyline())
                            elif boundary.asMultiPolyline():
                                for line in boundary.asMultiPolyline():
                                    boundary_points.extend(line)
                        
                        unshared_points = []
                        for bp in boundary_points:
                            in_a = any(abs(bp.x() - va[0]) < tolerance and abs(bp.y() - va[1]) < tolerance 
                                      for va in vertices_a)
                            in_b = any(abs(bp.x() - vb[0]) < tolerance and abs(bp.y() - vb[1]) < tolerance 
                                      for vb in vertices_b)
                            if not (in_a and in_b):
                                unshared_points.append(bp)
                        
                        if unshared_points:
                            issues_found += 1
                            result = {
                                'type': 'shared_vertex_missing',
                                'anomaly': 'shared_vertex_missing',
                                'id_a': str(fid),
                                'id_a_real': str(poly_feat[poly_id_field]) if poly_id_field else str(fid),
                                'id_b': str(cid),
                                'id_b_real': str(neighbor_feat[poly_id_field]) if poly_id_field else str(cid),
                                'layer_a_id': polygon_layer.id(),
                                'layer_b_id': polygon_layer.id(),
                                'measure': len(unshared_points),
                                'area_m2': 0.0,
                                'severity': 'High',
                                'geometry_json': boundary.asJson(),
                                'ratio': 0.0,
                                'ratio_percent': 0.0
                            }
                            results.append(normalize_result(result))
                            
                except Exception as e:
                    log_message('warning', f"Shared vertex check failed for {fid}/{cid}: {e}")
                    continue
        
        self._emit_log('info', f'   → {len(checked_pairs)} pairs checked, {issues_found} issues found')
        return results
