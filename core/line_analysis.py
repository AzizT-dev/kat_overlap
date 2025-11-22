# -*- coding: utf-8 -*-
"""
KAT Analysis – Line Analysis Module
Self-intersections, overlaps, and dangles detection for line geometries

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Callable
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsDistanceArea,
    QgsWkbTypes, QgsSpatialIndex, QgsPointXY
)
from .utils import log_message, normalize_result
from .classification import PresetManager


class LineAnalyzer:
    """
    Line topology analysis including:
    - Self-intersections (lines crossing themselves)
    - Overlaps (lines sharing segments)
    - Dangles (unconnected endpoints)
    """
    
    def __init__(self, da: QgsDistanceArea, id_fields: Dict[str, str],
                 params: Dict[str, Any], log_callback: Callable = None,
                 cancel_check: Callable = None):
        """
        Initialize line analyzer.
        
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
    
    def analyze_self_intersections(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze lines that intersect themselves.
        A self-intersecting line crosses over itself.
        
        :param layer: Line layer to analyze
        :return: List of self-intersection results
        """
        results = []
        issues_found = 0
        
        for feat in layer.getFeatures():
            if self.cancel_check():
                return results
            
            if not feat.hasGeometry():
                continue
            
            geom = feat.geometry()
            if geom.isEmpty():
                continue
            
            try:
                # Check if line is simple (no self-intersection)
                if not geom.isSimple():
                    intersection_points = []
                    
                    if geom.isMultipart():
                        lines = geom.asMultiPolyline()
                        for line in lines:
                            self._find_self_intersections(line, intersection_points)
                    else:
                        line = geom.asPolyline()
                        self._find_self_intersections(line, intersection_points)
                    
                    if intersection_points:
                        point_geom = QgsGeometry.fromPointXY(intersection_points[0])
                        
                        result = {
                            'type': 'line_self_intersection',
                            'anomaly': 'line_self_intersection',
                            'id_a': str(feat.id()),
                            'id_b': str(feat.id()),
                            'id_a_real': self._get_id_value(feat, layer),
                            'id_b_real': self._get_id_value(feat, layer),
                            'layer_a_id': layer.id(),
                            'layer_b_id': layer.id(),
                            'measure': len(intersection_points),
                            'area_m2': 0.0,
                            'severity': 'High',
                            'geometry_json': point_geom.asJson(),
                            'ratio': 0.0,
                            'ratio_percent': 0.0
                        }
                        
                        results.append(normalize_result(result))
                        issues_found += 1
                        
            except Exception as e:
                log_message('warning', f"Line self-intersection check failed for {feat.id()}: {e}")
                continue
        
        self._emit_log('info', f'   → {issues_found} self-intersecting lines found')
        return results
    
    def _find_self_intersections(self, line: List, intersections: List):
        """
        Find self-intersection points in a line.
        
        :param line: List of points forming the line
        :param intersections: List to append found intersections
        """
        if len(line) < 4:
            return
        
        for i in range(len(line) - 1):
            for j in range(i + 2, len(line) - 1):
                if j == i + 1:
                    continue
                
                p1, p2 = line[i], line[i + 1]
                p3, p4 = line[j], line[j + 1]
                
                intersection = self._segment_intersection(p1, p2, p3, p4)
                if intersection:
                    intersections.append(intersection)
    
    def _segment_intersection(self, p1, p2, p3, p4):
        """
        Find intersection point of two line segments.
        
        :return: QgsPointXY if segments intersect, None otherwise
        """
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        x3, y3 = p3.x(), p3.y()
        x4, y4 = p4.x(), p4.y()
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 < t < 1 and 0 < u < 1:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return QgsPointXY(ix, iy)
        
        return None
    
    def analyze_overlaps(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze lines that overlap (share segments).
        Uses overlaps() for OGC compliance.
        
        :param layer: Line layer to analyze
        :return: List of overlap results
        """
        results = []
        preset = self._get_preset()
        min_length = PresetManager.EPSILON_LENGTH_DEFAULT
        
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
        overlaps_found = 0
        
        for fid, feat_a in features_dict.items():
            if self.cancel_check():
                return results
            
            geom_a = feat_a.geometry()
            bbox = geom_a.boundingBox()
            
            candidate_ids = index.intersects(bbox)
            
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
                
                try:
                    if geom_a.overlaps(geom_b):
                        intersection = geom_a.intersection(geom_b)
                        
                        if intersection and not intersection.isEmpty():
                            # Only count line intersections (not points)
                            if intersection.type() != QgsWkbTypes.LineGeometry:
                                continue
                            
                            length = intersection.length()
                            if length < min_length:
                                continue
                            
                            severity = PresetManager.classify_line_topology(
                                length, preset, min_length
                            )
                            
                            result = {
                                'type': 'line_overlap',
                                'anomaly': 'line_overlap',
                                'id_a': str(fid),
                                'id_b': str(cid),
                                'id_a_real': self._get_id_value(feat_a, layer),
                                'id_b_real': self._get_id_value(feat_b, layer),
                                'layer_a_id': layer.id(),
                                'layer_b_id': layer.id(),
                                'measure': length,
                                'area_m2': 0.0,
                                'severity': severity,
                                'geometry_json': intersection.asJson(),
                                'ratio': 0.0,
                                'ratio_percent': 0.0
                            }
                            
                            results.append(normalize_result(result))
                            overlaps_found += 1
                            
                except Exception as e:
                    log_message('warning', f"Line overlap test failed for {fid}/{cid}: {e}")
                    continue
        
        self._emit_log('info', f'   → {overlaps_found} line overlaps found')
        return results
    
    def analyze_dangles(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze line dangles (endpoints not connected to other lines).
        
        :param layer: Line layer to analyze
        :return: List of dangle results
        """
        results = []
        
        # Collect all endpoints
        endpoints = {}  # {(x, y): [(feat_id, 'start'/'end', point), ...]}
        
        for feat in layer.getFeatures():
            if self.cancel_check():
                return results
            
            if not feat.hasGeometry():
                continue
            
            geom = feat.geometry()
            if geom.isEmpty():
                continue
            
            try:
                if geom.isMultipart():
                    for line in geom.asMultiPolyline():
                        if line:
                            self._add_endpoints(endpoints, feat.id(), line)
                else:
                    line = geom.asPolyline()
                    if line:
                        self._add_endpoints(endpoints, feat.id(), line)
                        
            except Exception as e:
                log_message('warning', f"Dangle check failed for {feat.id()}: {e}")
                continue
        
        # Find dangles (endpoints with only one connection)
        dangles_found = 0
        reported_features = set()
        
        for coord, connections in endpoints.items():
            if self.cancel_check():
                return results
            
            if len(connections) == 1:
                feat_id, pos, point = connections[0]
                
                if feat_id in reported_features:
                    continue
                reported_features.add(feat_id)
                
                point_geom = QgsGeometry.fromPointXY(QgsPointXY(point))
                
                result = {
                    'type': 'line_dangle',
                    'anomaly': 'line_dangle',
                    'id_a': str(feat_id),
                    'id_b': '',
                    'id_a_real': str(feat_id),
                    'id_b_real': '',
                    'layer_a_id': layer.id(),
                    'layer_b_id': '',
                    'measure': 1,
                    'area_m2': 0.0,
                    'severity': 'Moderate',
                    'geometry_json': point_geom.asJson(),
                    'ratio': 0.0,
                    'ratio_percent': 0.0
                }
                
                results.append(normalize_result(result))
                dangles_found += 1
        
        self._emit_log('info', f'   → {dangles_found} dangles found')
        return results
    
    def _add_endpoints(self, endpoints: Dict, feat_id: int, line: List):
        """Add line endpoints to the endpoints dictionary"""
        start = (round(line[0].x(), 3), round(line[0].y(), 3))
        end = (round(line[-1].x(), 3), round(line[-1].y(), 3))
        
        if start not in endpoints:
            endpoints[start] = []
        endpoints[start].append((feat_id, 'start', line[0]))
        
        if end not in endpoints:
            endpoints[end] = []
        endpoints[end].append((feat_id, 'end', line[-1]))
