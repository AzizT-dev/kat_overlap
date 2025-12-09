# -*- coding: utf-8 -*-
"""
KAT Analysis – Polygon Analysis Module
Self-overlaps and inter-layer overlap detection using OGC-compliant overlaps()

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any, Callable, Optional
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsDistanceArea,
    QgsWkbTypes, QgsSpatialIndex
)
from .utils import log_message, normalize_result
from .classification import PresetManager


class PolygonAnalyzer:
    """
    Polygon overlap analysis using OGC-compliant overlaps() method.
    
    Key difference from intersects():
    - overlaps() returns TRUE only for real surface overlaps
    - Adjacent polygons that only touch boundaries are NOT counted
    """
    
    def __init__(self, da: QgsDistanceArea, id_fields: Dict[str, str],
                 params: Dict[str, Any], log_callback: Callable = None,
                 cancel_check: Callable = None):
        """
        Initialize polygon analyzer.
        
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
        self.results = []
    
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
    
    def _safe_area(self, geom: QgsGeometry) -> float:
        """Calculate area safely"""
        try:
            if geom and not geom.isEmpty():
                return self.da.measureArea(geom)
        except:
            pass
        return 0.0
    
    def analyze_self_overlaps(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze polygon self-overlaps using spatial index.
        
        Uses overlaps() instead of intersects() for OGC compliance:
        - overlaps() = TRUE only if intersection is a surface
        - Prevents false positives from adjacent parcels sharing boundaries
        
        :param layer: Polygon layer to analyze
        :return: List of overlap results
        """
        self.results = []
        preset = self._get_preset()
        min_area = self.params.get('min_overlap_area', PresetManager.EPSILON_AREA_DEFAULT)
        
        # Build spatial index
        index = QgsSpatialIndex()
        features_dict = {}
        
        for feat in layer.getFeatures():
            if self.cancel_check():
                return self.results
            if feat.hasGeometry() and not feat.geometry().isEmpty():
                index.addFeature(feat)
                features_dict[feat.id()] = feat
        
        # Process features
        processed_pairs = set()
        overlaps_found = 0
        
        for fid, feat_a in features_dict.items():
            if self.cancel_check():
                return self.results
            
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
                    # Use overlaps() instead of intersects()
                    if geom_a.overlaps(geom_b):
                        intersection = geom_a.intersection(geom_b)
                        
                        if intersection and not intersection.isEmpty():
                            # Filter: only surfaces count as overlaps
                            if intersection.type() != QgsWkbTypes.PolygonGeometry:
                                continue
                            
                            overlap_area = self._safe_area(intersection)
                            
                            if overlap_area >= min_area:
                                area_a = self._safe_area(geom_a)
                                area_b = self._safe_area(geom_b)
                                
                                severity, details = PresetManager.classify_polygon_overlap(
                                    overlap_area, area_a, area_b, preset, min_area
                                )
                                
                                result = {
                                    'type': 'polygon_overlap',
                                    'anomaly': 'polygon_overlap',
                                    'id_a': str(fid),
                                    'id_b': str(cid),
                                    'id_a_real': self._get_id_value(feat_a, layer),
                                    'id_b_real': self._get_id_value(feat_b, layer),
                                    'layer_a_id': layer.id(),
                                    'layer_b_id': layer.id(),
                                    'measure': overlap_area,
                                    'area_m2': overlap_area,
                                    'severity': severity,
                                    'geometry_json': intersection.asJson(),
                                    **details
                                }
                                
                                self.results.append(normalize_result(result))
                                overlaps_found += 1
                                
                except Exception as e:
                    log_message('warning', f"Overlap test failed for {fid}/{cid}: {e}")
                    continue
        
        self._emit_log('info', f'   → {overlaps_found} overlaps found in {len(processed_pairs)} pairs checked')
        return self.results
    
    def analyze_inter_layer_overlaps(self, layer: QgsVectorLayer) -> List[Dict[str, Any]]:
        """
        Analyze overlaps between features from different source layers (merged layer case).
        Uses __source_layer_id field to identify origin.
        
        :param layer: Merged polygon layer with __source_layer_id field
        :return: List of inter-layer overlap results
        """
        results = []
        
        if '__source_layer_id' not in [f.name() for f in layer.fields()]:
            return results  # Not a merged layer
        
        preset = self._get_preset()
        min_area = self.params.get('min_overlap_area', PresetManager.EPSILON_AREA_DEFAULT)
        
        # Group features by source layer
        by_source = {}
        for feat in layer.getFeatures():
            if self.cancel_check():
                return results
            source_id = feat['__source_layer_id']
            if source_id not in by_source:
                by_source[source_id] = []
            by_source[source_id].append(feat)
        
        source_ids = list(by_source.keys())
        overlaps_found = 0
        
        # Compare each pair of source layers
        for i in range(len(source_ids)):
            for j in range(i + 1, len(source_ids)):
                if self.cancel_check():
                    return results
                
                source_a = source_ids[i]
                source_b = source_ids[j]
                
                # Build spatial index for source_b
                index_b = QgsSpatialIndex()
                feats_b = {f.id(): f for f in by_source[source_b] if f.hasGeometry()}
                for feat in feats_b.values():
                    index_b.addFeature(feat)
                
                # Query with features from source_a
                for feat_a in by_source[source_a]:
                    if self.cancel_check():
                        return results
                    
                    if not feat_a.hasGeometry():
                        continue
                    
                    geom_a = feat_a.geometry()
                    candidates = index_b.intersects(geom_a.boundingBox())
                    
                    for cid in candidates:
                        feat_b = feats_b.get(cid)
                        if not feat_b:
                            continue
                        
                        geom_b = feat_b.geometry()
                        
                        try:
                            if geom_a.overlaps(geom_b):
                                intersection = geom_a.intersection(geom_b)
                                
                                if intersection and not intersection.isEmpty():
                                    if intersection.type() != QgsWkbTypes.PolygonGeometry:
                                        continue
                                    
                                    overlap_area = self._safe_area(intersection)
                                    
                                    if overlap_area >= min_area:
                                        area_a = self._safe_area(geom_a)
                                        area_b = self._safe_area(geom_b)
                                        
                                        severity, details = PresetManager.classify_polygon_overlap(
                                            overlap_area, area_a, area_b, preset, min_area
                                        )
                                        
                                        result = {
                                            'type': 'inter_layer_overlap',
                                            'anomaly': 'inter_layer_overlap',
                                            'id_a': str(feat_a.id()),
                                            'id_b': str(feat_b.id()),
                                            'id_a_real': self._get_id_value(feat_a, layer),
                                            'id_b_real': self._get_id_value(feat_b, layer),
                                            'layer_a_id': source_a,
                                            'layer_b_id': source_b,
                                            'measure': overlap_area,
                                            'area_m2': overlap_area,
                                            'severity': severity,
                                            'geometry_json': intersection.asJson(),
                                            **details
                                        }
                                        
                                        results.append(normalize_result(result))
                                        overlaps_found += 1
                                        
                        except Exception as e:
                            log_message('warning', f"Inter-layer test failed: {e}")
                            continue
        
        self._emit_log('info', f'   → {overlaps_found} inter-layer overlaps found')
        return results
    
    def get_polygon_vertices(self, geom: QgsGeometry) -> List:
        """
        Extract vertices from polygon geometry, excluding closing vertex.
        
        :param geom: Polygon geometry
        :return: List of vertices
        """
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
                            if len(ring) > 1:
                                vertices.extend(ring[:-1])
                            else:
                                vertices.extend(ring)
            else:
                poly = geom.asPolygon()
                if poly and poly[0]:
                    ring = poly[0]
                    if len(ring) > 1:
                        vertices = list(ring[:-1])
                    else:
                        vertices = list(ring)
        except Exception as e:
            log_message('warning', f"Error extracting vertices: {e}")
        
        return vertices
