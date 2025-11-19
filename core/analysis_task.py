# -*- coding: utf-8 -*-
"""
KAT Analysis – Analysis Task (QgsTask)

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from qgis.core import QgsTask, QgsDistanceArea, QgsProject, QgsGeometry, QgsFeature, QgsSpatialIndex
from typing import Dict, Any, List, Optional
from .classification import PresetManager
import math

class AnalysisTask(QgsTask):
    """Analysis task executed by QGIS Task Manager with improved logging"""
    
    def __init__(self, description: str, layers: Dict[str, Any], params: Optional[Dict[str, Any]] = None,
                 id_fields: Optional[Dict[str, str]] = None, generate_fid: bool = False,
                 on_progress=None, on_log=None, on_finished=None, on_error=None, parent=None):
        super().__init__(description, QgsTask.CanCancel)
        self.layers = layers or {}
        self.params = params or {}
        self.id_fields = id_fields or {}
        self.generate_fid = generate_fid
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_finished = on_finished
        self.on_error = on_error
        self._results: List[Dict[str, Any]] = []
        self._error_msg: Optional[str] = None
        self._logs: List[tuple] = []

        self.epsilon_area = float(self.params.get('epsilon_area', PresetManager.EPSILON_AREA_DEFAULT))
        self.epsilon_dist = float(self.params.get('epsilon_dist', PresetManager.EPSILON_DIST_DEFAULT))

        self.da = QgsDistanceArea()
        try:
            self.da.setEllipsoid(QgsProject.instance().ellipsoid())
            self.da.setSourceCrs(QgsProject.instance().crs(), QgsProject.instance().transformContext())
        except Exception:
            pass

        profile_name = self.params.get('profile', 'Land/Cadastre (GPS ±2m)')
        self.preset = PresetManager.get_preset(profile_name)

    def _log(self, level: str, message: str) -> None:
        """Log a message"""
        try:
            self._logs.append((level, message))
            if callable(self.on_log):
                self.on_log(level, message)
        except Exception:
            pass

    def _log_progress(self, msg: str) -> None:
        """Log progress message"""
        self._log("info", msg)

    def run(self) -> bool:
        try:
            self._results = []
            poly = self.layers.get("polygon")
            line = self.layers.get("line")
            point = self.layers.get("point")

            selected_count = sum(1 for layer in [poly, line, point] if layer is not None)
            if selected_count == 1:
                if poly:
                    self._log("info", "Analysis: Self-intersections (polygons)")
                    self._results = self._analyze_self_overlaps(poly)
                elif line:
                    self._log("info", "Analysis: Line topology")
                    self._results = self._analyze_line_topology(line)
                elif point:
                    self._log("info", "Analysis: Clustered points/proximity")
                    self._results = self._analyze_point_proximity(point)
            elif selected_count >= 2:
                if point and poly and not line:
                    self._log("info", "Analysis: Points-Polygons (association)")
                    self._results = self._analyze_points_in_polygons(point, poly)
                elif poly and self._count_polygons_in_selection() >= 2:
                    self._log("info", "Analysis: Inter-layer overlaps")
                    self._results = self._analyze_inter_layer_overlaps()
                else:
                    self._log("info", "Layer combination not supported.")
                    self._results = []
            self.setProgress(100)
            return True
        except Exception as e:
            self._error_msg = str(e)
            self._log("error", f"Analysis error: {e}")
            return False

    def finished(self, result: bool) -> None:
        try:
            if callable(self.on_log):
                for level, msg in self._logs:
                    try:
                        self.on_log(level, msg)
                    except Exception:
                        pass
        except Exception:
            pass

        if result:
            if callable(self.on_finished):
                try:
                    self.on_finished(self._results)
                except Exception as e:
                    if callable(self.on_error):
                        self.on_error(f"Callback on_finished failed: {e}")
        else:
            msg = self._error_msg or "Analysis failed."
            if callable(self.on_error):
                self.on_error(msg)

    def cancelled(self) -> None:
        self._log("info", "Analysis cancelled by user.")
        if callable(self.on_error):
            self.on_error("Analysis cancelled.")

    def _count_polygons_in_selection(self) -> int:
        count = 0
        for layer in self.layers.values():
            if layer and hasattr(layer, "geometryType") and layer.geometryType() == 2:
                count += 1
        return count

    def _get_real_id(self, feature, layer):
        try:
            layer_id = layer.id()
            if layer_id in self.id_fields and self.id_fields[layer_id] != "None":
                field_name = self.id_fields[layer_id]
                if field_name in feature.fields().names():
                    return str(feature[field_name])
        except Exception:
            pass
        try:
            return str(feature.id())
        except Exception:
            return ""

    def _safe_area(self, geom):
        try:
            return float(self.da.measureArea(geom))
        except Exception:
            try:
                return float(geom.area())
            except Exception:
                return 0.0

    # ===== ANALYSIS: SELF-INTERSECTIONS (POLYGONS) =====
    def _analyze_self_overlaps(self, layer) -> List[Dict[str, Any]]:
        """Analyze overlaps in ONE polygon layer"""
        res = []
        feats_snap = []
        try:
            for feat in layer.getFeatures():
                if self.isCanceled():
                    return res
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                try:
                    geom_clone = geom.clone()
                except Exception:
                    geom_clone = QgsGeometry(geom)
                feats_snap.append({
                    'fid': feat.id(),
                    'geom': geom_clone,
                    'real_id': self._get_real_id(feat, layer),
                    'area': self._safe_area(geom_clone)
                })
        except Exception as e:
            self._log("error", self.tr("Polygon layer read error: {}").format(e))  # CORRECTION: ajout du niveau
            return res

        total = len(feats_snap)
        for i, feat_a in enumerate(feats_snap):
            if self.isCanceled():
                break
            geom_a = feat_a['geom']
            if geom_a is None or geom_a.isEmpty():
                continue

            for feat_b in feats_snap[i+1:]:
                if self.isCanceled():
                    break
                geom_b = feat_b['geom']
                if geom_b is None or geom_b.isEmpty():
                    continue

                try:
                    intersects = geom_a.intersects(geom_b)
                except Exception:
                    intersects = False

                if not intersects:
                    continue

                try:
                    inter_geom = geom_a.intersection(geom_b)
                except Exception:
                    inter_geom = None

                if inter_geom is None or inter_geom.isEmpty():
                    continue

                area = self._safe_area(inter_geom)
                a1 = feat_a['area']
                a2 = feat_b['area']

                if area < self.epsilon_area:
                    continue

                severity, details = PresetManager.classify_polygon_overlap(area, a1, a2, self.preset, epsilon_area=self.epsilon_area)

                geom_json = None
                try:
                    if inter_geom and not inter_geom.isEmpty():
                        json_bytes = inter_geom.asJson()
                        # asJson() returns bytes, need to decode to string
                        if isinstance(json_bytes, bytes):
                            geom_json = json_bytes.decode('utf-8')
                        else:
                            geom_json = str(json_bytes)
                except Exception as e:
                    self._log("error", self.tr("asJson() self_overlap error: {}").format(e))  # CORRECTION: ajout du niveau

                res.append({
                    "type": "self_overlap",
                    "id_a": str(feat_a['fid']),
                    "id_b": str(feat_b['fid']),
                    "id_a_real": feat_a.get('real_id'),
                    "id_b_real": feat_b.get('real_id'),
                    "layer_a": {'layer_id': layer.id(), 'feature': None},
                    "layer_b": {'layer_id': layer.id(), 'feature': None},
                    "measure": area,
                    "ratio": details.get('ratio', 0.0),
                    "score": details.get('ratio', 0.0),
                    "severity": severity,
                    "geometry_json": geom_json
                })

            try:
                self.setProgress(int(100.0 * (i+1) / max(total, 1)))
            except Exception:
                pass
            self._log_progress(self.tr("Polygon analysis {}/{}").format(i+1, total))

        return res

    # ===== ANALYSIS: INTER-LAYER OVERLAPS =====
    def _analyze_inter_layer_overlaps(self) -> List[Dict[str, Any]]:
        """Analyze overlaps between 2+ polygon layers"""
        res = []
        poly_layers = [l for l in self.layers.values() if l and hasattr(l, "geometryType") and l.geometryType() == 2]
        
        if len(poly_layers) < 2:
            return res

        for layer_idx, layer_a in enumerate(poly_layers):
            for layer_b in poly_layers[layer_idx+1:]:
                if self.isCanceled():
                    return res

                feats_a = []
                try:
                    for f in layer_a.getFeatures():
                        g = f.geometry()
                        if g is None or g.isEmpty():
                            continue
                        try:
                            gclone = g.clone()
                        except Exception:
                            gclone = QgsGeometry(g)
                        feats_a.append({
                            'fid': f.id(),
                            'geom': gclone,
                            'real_id': self._get_real_id(f, layer_a),
                            'area': self._safe_area(gclone)
                        })
                except Exception:
                    continue

                feats_b = []
                try:
                    for f in layer_b.getFeatures():
                        g = f.geometry()
                        if g is None or g.isEmpty():
                            continue
                        try:
                            gclone = g.clone()
                        except Exception:
                            gclone = QgsGeometry(g)
                        feats_b.append({
                            'fid': f.id(),
                            'geom': gclone,
                            'real_id': self._get_real_id(f, layer_b),
                            'area': self._safe_area(gclone)
                        })
                except Exception:
                    continue

                for fa in feats_a:
                    if self.isCanceled():
                        break
                    for fb in feats_b:
                        if self.isCanceled():
                            break
                        try:
                            if fa['geom'].intersects(fb['geom']):
                                inter_geom = fa['geom'].intersection(fb['geom'])
                                if inter_geom and not inter_geom.isEmpty():
                                    area = self._safe_area(inter_geom)
                                    if area >= self.epsilon_area:
                                        severity, details = PresetManager.classify_polygon_overlap(
                                            area, fa['area'], fb['area'], self.preset, epsilon_area=self.epsilon_area
                                        )
                                        geom_json = None
                                        try:
                                            json_bytes = inter_geom.asJson()
                                            if isinstance(json_bytes, bytes):
                                                geom_json = json_bytes.decode('utf-8')
                                            else:
                                                geom_json = str(json_bytes)
                                        except Exception:
                                            pass
                                        res.append({
                                            "type": "inter_layer_overlap",
                                            "id_a": str(fa['fid']),
                                            "id_b": str(fb['fid']),
                                            "id_a_real": fa.get('real_id'),
                                            "id_b_real": fb.get('real_id'),
                                            "layer_a": {'layer_id': layer_a.id(), 'feature': None},
                                            "layer_b": {'layer_id': layer_b.id(), 'feature': None},
                                            "measure": area,
                                            "ratio": details.get('ratio', 0.0),
                                            "score": details.get('ratio', 0.0),
                                            "severity": severity,
                                            "geometry_json": geom_json
                                        })
                        except Exception:
                            pass

        return res

    # ===== ANALYSIS: LINE TOPOLOGY =====
    def _analyze_line_topology(self, layer) -> List[Dict[str, Any]]:
        """Analyze line topology"""
        res = []
        lines = []
        try:
            for feat in layer.getFeatures():
                if self.isCanceled():
                    return res
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                try:
                    gclone = geom.clone()
                except Exception:
                    gclone = QgsGeometry(geom)
                lines.append({
                    'fid': feat.id(),
                    'geom': gclone,
                    'real_id': self._get_real_id(feat, layer)
                })
        except Exception as e:
            self._log(self.tr("Line layer read error: {}").format(e))
            return res

        total = len(lines)
        for i, line in enumerate(lines):
            if self.isCanceled():
                break
            geom = line['geom']
            try:
                if not geom.isSimple():
                    length = self.da.measureLength(geom)
                    severity = PresetManager.classify_line_topology(length, self.preset, epsilon_dist=self.epsilon_dist)
                    geom_json = None
                    try:
                        json_bytes = geom.asJson()
                        if isinstance(json_bytes, bytes):
                            geom_json = json_bytes.decode('utf-8')
                        else:
                            geom_json = str(json_bytes)
                    except Exception:
                        pass
                    res.append({
                        "type": "line_self_intersect",
                        "id_a": str(line['fid']),
                        "id_b": "",
                        "id_a_real": line.get('real_id'),
                        "id_b_real": "",
                        "layer_a": {'layer_id': layer.id(), 'feature': None},
                        "layer_b": {'layer_id': layer.id(), 'feature': None},
                        "measure": length,
                        "ratio": 0.0,
                        "score": 0.0,
                        "severity": severity,
                        "geometry_json": geom_json
                    })
            except Exception:
                pass
            try:
                self.setProgress(int(100.0 * (i+1) / max(total, 1)))
            except Exception:
                pass
            self._log_progress(self.tr("Line analysis {}/{}").format(i+1, total))

        return res

    # ===== ANALYSIS: CLUSTERED POINTS/PROXIMITY =====
    def _analyze_point_proximity(self, layer) -> List[Dict[str, Any]]:
        """Analyze point proximity
        - If generate_fid: group by attribute ID, find intra-group duplicates
        - Else: simple proximity detection
        """
        res = []
        
        generate_fid = self.generate_fid
        id_field = None
        
        for lid, field_name in self.id_fields.items():
            if layer and layer.id() == lid:
                id_field = field_name if field_name != self.tr("None") else None
                break
        
        if generate_fid:
            self._log(self.tr("Point analysis: Grouping by ID field ({}), detecting intra-group duplicates").format(id_field))
        else:
            self._log(self.tr("Point analysis: Simple proximity detection (without grouping)"))
        
        points = []
        try:
            for feat in layer.getFeatures():
                if self.isCanceled():
                    return res
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                try:
                    gclone = geom.clone()
                except Exception:
                    gclone = QgsGeometry(geom)
                
                id_val = self._get_real_id(feat, layer)
                attr_val = None
                if generate_fid and id_field and id_field in [f.name() for f in feat.fields()]:
                    try:
                        attr_val = str(feat[id_field])
                    except Exception:
                        attr_val = None
                
                points.append({
                    'fid': feat.id(),
                    'geom': gclone,
                    'real_id': id_val,
                    'attr_id': attr_val
                })
        except Exception as e:
            self._log(self.tr("Point layer read error: {}").format(e))
            return res

        total = len(points)
        
        if generate_fid and id_field:
            # GROUPING BY ATTRIBUTE ID
            points_by_attr = {}
            for p in points:
                attr = p['attr_id'] or 'NONE'
                if attr not in points_by_attr:
                    points_by_attr[attr] = []
                points_by_attr[attr].append(p)
            
            self._log(self.tr("Points grouped into {} groups by attribute ID").format(len(points_by_attr)))
            
            doublons_found = 0
            for attr, group_points in points_by_attr.items():
                if self.isCanceled():
                    break
                
                if len(group_points) < 2:
                    continue
                
                self._log(self.tr("Group {}: {} points, checking duplicates").format(attr, len(group_points)))
                
                for i, p1 in enumerate(group_points):
                    if self.isCanceled():
                        break
                    for p2 in group_points[i+1:]:
                        if self.isCanceled():
                            break
                        try:
                            d = self.da.distance(p1['geom'], p2['geom'])
                            if d <= 0.001:
                                doublons_found += 1
                                severity = self.tr("Critical")
                                geom_json = None
                                try:
                                    json_bytes = p1['geom'].asJson()
                                    if isinstance(json_bytes, bytes):
                                        geom_json = json_bytes.decode('utf-8')
                                    else:
                                        geom_json = str(json_bytes)
                                except Exception:
                                    pass
                                
                                res.append({
                                    "type": "point_duplicate_group",
                                    "id_a": str(p1['fid']),
                                    "id_b": str(p2['fid']),
                                    "id_a_real": p1.get('real_id'),
                                    "id_b_real": p2.get('real_id'),
                                    "layer_a": {'layer_id': layer.id(), 'feature': None},
                                    "layer_b": {'layer_id': layer.id(), 'feature': None},
                                    "measure": d,
                                    "ratio": 0.0,
                                    "score": 1.0,
                                    "severity": severity,
                                    "geometry_json": geom_json
                                })
                                self._log(self.tr("  Duplicate detected: {}-{} (dist={:.9f}m)").format(p1['real_id'], p2['real_id'], d))
                        except Exception:
                            pass
            
            if doublons_found == 0:
                self._log(self.tr("No duplicates detected (all points are unique per group)"))
            else:
                self._log(self.tr("Duplicates found: {}").format(doublons_found))
        else:
            # WITHOUT GROUPING: simple proximity detection
            self._log(self.tr("Simple proximity check for {} points").format(total))
            
            proximities_found = 0
            for i, p1 in enumerate(points):
                if self.isCanceled():
                    break
                for p2 in points[i+1:]:
                    if self.isCanceled():
                        break
                    try:
                        d = self.da.distance(p1['geom'], p2['geom'])
                        if d >= self.epsilon_dist and d <= 10.0:
                            proximities_found += 1
                            severity = PresetManager.classify_point_proximity(d, self.preset, epsilon_dist=self.epsilon_dist)
                            geom_json = None
                            try:
                                json_bytes = p1['geom'].asJson()
                                if isinstance(json_bytes, bytes):
                                    geom_json = json_bytes.decode('utf-8')
                                else:
                                    geom_json = str(json_bytes)
                            except Exception:
                                pass
                            res.append({
                                "type": "point_proximity",
                                "id_a": str(p1['fid']),
                                "id_b": str(p2['fid']),
                                "id_a_real": p1.get('real_id'),
                                "id_b_real": p2.get('real_id'),
                                "layer_a": {'layer_id': layer.id(), 'feature': None},
                                "layer_b": {'layer_id': layer.id(), 'feature': None},
                                "measure": d,
                                "ratio": 0.0,
                                "score": 0.0,
                                "severity": severity,
                                "geometry_json": geom_json
                            })
                    except Exception:
                        pass
                try:
                    self.setProgress(int(100.0 * (i+1) / max(total, 1)))
                except Exception:
                    pass
                self._log_progress(self.tr("Point analysis {}/{}").format(i+1, total))
            
            if proximities_found == 0:
                self._log(self.tr("No proximities detected (all points are isolated)"))
            else:
                self._log(self.tr("Proximities detected: {}").format(proximities_found))

        return res

    # ===== ANALYSIS: POINTS-POLYGONS =====
    def _analyze_points_in_polygons(self, point_layer, poly_layer) -> List[Dict[str, Any]]:
        """Analyze points -> polygons association
        - Group by attribute ID (user field)
        - Check that point is on polygon vertex (near-zero tolerance)
        """
        res = []
        
        id_field_points = None
        id_field_polys = None
        
        for lid, field_name in self.id_fields.items():
            if point_layer and point_layer.id() == lid:
                id_field_points = field_name if field_name != self.tr("None") else None
            if poly_layer and poly_layer.id() == lid:
                id_field_polys = field_name if field_name != self.tr("None") else None
        
        self._log(self.tr("Points-polygons analysis: grouping by ID (pts:{}, polys:{})").format(id_field_points, id_field_polys))

        points = []
        try:
            for feat in point_layer.getFeatures():
                if self.isCanceled():
                    return res
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                try:
                    gclone = geom.clone()
                except Exception:
                    gclone = QgsGeometry(geom)
                
                attr_val = None
                if id_field_points and id_field_points in [f.name() for f in feat.fields()]:
                    try:
                        attr_val = str(feat[id_field_points])
                    except Exception:
                        pass
                
                points.append({
                    'fid': feat.id(),
                    'geom': gclone,
                    'real_id': self._get_real_id(feat, point_layer),
                    'attr_id': attr_val
                })
        except Exception as e:
            self._log(self.tr("Point layer read error: {}").format(e))
            return res

        polys = []
        polys_by_attr = {}
        index = QgsSpatialIndex()
        try:
            for feat in poly_layer.getFeatures():
                if self.isCanceled():
                    return res
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                try:
                    gclone = geom.clone()
                except Exception:
                    gclone = QgsGeometry(geom)
                
                attr_val = None
                if id_field_polys and id_field_polys in [f.name() for f in feat.fields()]:
                    try:
                        attr_val = str(feat[id_field_polys])
                    except Exception:
                        pass
                
                rec = {
                    'fid': feat.id(),
                    'geom': gclone,
                    'real_id': self._get_real_id(feat, poly_layer),
                    'attr_id': attr_val
                }
                polys.append(rec)
                if attr_val:
                    if attr_val not in polys_by_attr:
                        polys_by_attr[attr_val] = []
                    polys_by_attr[attr_val].append(rec)
                try:
                    index.insertFeature(feat)
                except Exception:
                    pass
        except Exception as e:
            self._log(self.tr("Polygon layer read error: {}").format(e))
            return res

        use_index = True
        try:
            use_index = (index.featureCount() > 0)
        except Exception:
            use_index = False

        self._log(self.tr("Points: {}, Polygons: {}, groups: {}").format(len(points), len(polys), len(polys_by_attr)))

        total = len(points)
        pts_on_vertex = 0
        pts_in_not_vertex = 0
        pts_out = 0
        
        for i, pf in enumerate(points):
            if self.isCanceled():
                break

            pgeom = pf['geom']
            if pgeom is None or pgeom.isEmpty():
                continue

            candidate_polys = []
            match_type = ""
            
            if pf['attr_id'] and pf['attr_id'] in polys_by_attr:
                candidate_polys = polys_by_attr[pf['attr_id']]
                match_type = self.tr("(group {})").format(pf['attr_id'])
            else:
                candidate_polys = polys
                match_type = self.tr("(fallback all)")
            
            matched_poly = None
            is_on_vertex = False
            
            for poly_rec in candidate_polys:
                if self.isCanceled():
                    break
                pg = poly_rec['geom']
                if pg is None or pg.isEmpty():
                    continue
                try:
                    contains = pg.contains(pgeom)
                except Exception:
                    contains = False
                
                if contains or pg.touches(pgeom):
                    try:
                        vertices = pg.vertices()
                        for v in vertices:
                            dist_to_vertex = pgeom.distance(v)
                            if dist_to_vertex < 0.0001:
                                matched_poly = poly_rec
                                is_on_vertex = True
                                break
                    except Exception:
                        pass
                    
                    if not is_on_vertex:
                        matched_poly = poly_rec
                        break
            
            if matched_poly:
                if is_on_vertex:
                    severity = self.tr("Critical")
                    pts_on_vertex += 1
                else:
                    severity = self.tr("High")
                    pts_in_not_vertex += 1
            else:
                severity = self.tr("High")
                pts_out += 1
            
            geom_json = None
            try:
                if pgeom and not pgeom.isEmpty():
                    json_bytes = pgeom.asJson()
                    if isinstance(json_bytes, bytes):
                        geom_json = json_bytes.decode('utf-8')
                    else:
                        geom_json = str(json_bytes)
            except Exception:
                pass

            # Calculate point-polygon distance if not on vertex
            dist = 0.0
            if matched_poly and not is_on_vertex:
                try:
                    dist = pgeom.distance(matched_poly['geom'])
                except Exception:
                    dist = 0.0
            
            res.append({
                "type": "point_in_polygon",
                "id_a": str(pf['fid']),
                "id_b": str(matched_poly['fid']) if matched_poly else "",
                "id_a_real": pf.get('real_id'),
                "id_b_real": matched_poly.get('real_id') if matched_poly else "",
                "layer_a": {'layer_id': point_layer.id(), 'feature': None},
                "layer_b": {'layer_id': poly_layer.id(), 'feature': None},
                "measure": dist,
                "ratio": 1.0 if is_on_vertex else 0.5,
                "score": 1.0 if is_on_vertex else 0.0,
                "severity": severity,
                "geometry_json": geom_json
            })

            try:
                self.setProgress(int(100.0 * (i+1) / max(total, 1)))
            except Exception:
                pass
            self._log_progress(self.tr("Points-polygons analysis {}/{}").format(i+1, total))

        self._log(self.tr("Summary: {} on vertex, {} in poly without vertex, {} outside polygon").format(pts_on_vertex, pts_in_not_vertex, pts_out))

        return res
    
    def tr(self, message):
        """Qt translation fallback (kept for QGIS API compatibility)"""
        from qgis.core import QgsApplication
        return QgsApplication.translate('AnalysisTask', message)
