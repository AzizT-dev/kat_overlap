# -*- coding: utf-8 -*-
"""
KAT Analysis – Classification & Presets (FIXED v2.3.0)
Business profile threshold management with RATIO-FIRST logic

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from .utils import tr


# =================CLASSIFICATION PRESETS DATA====================

CLASSIFICATION_PRESETS = {
    tr("Land Registry/Cadastre (GPS ±2m)"): {
        'description': tr('Cadastre, land parcels, land boundaries'),
        'precision_info': tr('Consumer GPS ±2m'),
        'points': {
            'critical': 0.5,
            'high': 1.5,
            'moderate': 5.0,
            'low': float('inf')
        },
        'polygons_absolute': {
            'low_max': 5,
            'moderate_max': 100,
            'high_max': 500,
            'critical_min': 500
        },
        'polygons_ratio': {
            'low_max': 0.05,
            'moderate_max': 0.20,
            'high_max': 0.50,
            'critical_min': 0.50
        },
        'lines': {
            'tolerance': 0.5,
            'critical': 0.01,
            'high': 0.1,
            'moderate': 0.5
        },
        'examples': {
            'points': tr("0.5m ≈ manual pointing error"),
            'polygons': tr("5m² ≈ 2.5m × 2m (standard GPS precision)")
        }
    },

    tr("Construction/Engineering (GPS RTK ±0.05m)"): {
        'description': tr('Construction sites, implementations, structures'),
        'precision_info': tr('RTK GPS ±0.05m'),
        'points': {
            'critical': 0.05,
            'high': 0.2,
            'moderate': 0.5,
            'low': float('inf')
        },
        'polygons_absolute': {
            'low_max': 0.5,
            'moderate_max': 10,
            'high_max': 50,
            'critical_min': 50
        },
        'polygons_ratio': {
            'low_max': 0.05,
            'moderate_max': 0.20,
            'high_max': 0.50,
            'critical_min': 0.50
        },
        'lines': {
            'tolerance': 0.05,
            'critical': 0.01,
            'high': 0.02,
            'moderate': 0.05
        },
        'examples': {
            'points': tr("0.05m = 5cm (implementation tolerance)"),
            'polygons': tr("0.5m² ≈ 70cm × 70cm (foundation)")
        }
    },

    tr("Topography (Total Station ±0.01m)"): {
        'description': tr('Precise surveys, topography, geodesy'),
        'precision_info': tr('Total station ±0.01m'),
        'points': {
            'critical': 0.01,
            'high': 0.03,
            'moderate': 0.1,
            'low': float('inf')
        },
        'polygons_absolute': {
            'low_max': 1,
            'moderate_max': 50,
            'high_max': 200,
            'critical_min': 200
        },
        'polygons_ratio': {
            'low_max': 0.05,
            'moderate_max': 0.20,
            'high_max': 0.50,
            'critical_min': 0.50
        },
        'lines': {
            'tolerance': 0.01,
            'critical': 0.005,
            'high': 0.01,
            'moderate': 0.05
        },
        'examples': {
            'points': tr("0.01m = 1cm (high precision)"),
            'polygons': tr("1m² = millimeter precision")
        }
    },

    tr("Hydrology (GIS ±10m)"): {
        'description': tr('Watersheds, hydrographic networks'),
        'precision_info': tr('GIS data ±10m'),
        'points': {
            'critical': 2.0,
            'high': 5.0,
            'moderate': 10.0,
            'low': float('inf')
        },
        'polygons_absolute': {
            'low_max': 100,
            'moderate_max': 1000,
            'high_max': 5000,
            'critical_min': 5000
        },
        'polygons_ratio': {
            'low_max': 0.05,
            'moderate_max': 0.20,
            'high_max': 0.50,
            'critical_min': 0.50
        },
        'lines': {
            'tolerance': 2.0,
            'critical': 0.5,
            'high': 1.0,
            'moderate': 2.0
        },
        'examples': {
            'points': tr("2m ≈ acceptable cartographic shift"),
            'polygons': tr("100m² ≈ small retention basin")
        }
    },

    tr("Custom"): {
        'description': tr("User-defined thresholds"),
        'precision_info': tr('Variable according to context'),
        'points': {
            'critical': 0.5,
            'high': 1.5,
            'moderate': 5.0,
            'low': float('inf')
        },
        'polygons_absolute': {
            'low_max': 5,
            'moderate_max': 100,
            'high_max': 500,
            'critical_min': 500
        },
        'polygons_ratio': {
            'low_max': 0.05,
            'moderate_max': 0.20,
            'high_max': 0.50,
            'critical_min': 0.50
        },
        'lines': {
            'tolerance': 0.5,
            'critical': 0.01,
            'high': 0.1,
            'moderate': 0.5
        },
        'examples': {
            'points': tr("Define according to your needs"),
            'polygons': tr("Adapt to project specifics")
        }
    }
}

# ==================PRESET MANAGER========================

class PresetManager:
    """Preset classification manager with RATIO-FIRST logic"""

    # EPSILON values (pre-filter noise)
    EPSILON_AREA_DEFAULT = 0.01      # Minimum area: 1 cm²
    EPSILON_DIST_DEFAULT = 0.001     # Minimum distance: 1 mm
    EPSILON_LENGTH_DEFAULT = 0.01    # Minimum length: 1 cm

    # Small area threshold - below this, absolute area becomes relevant
    SMALL_AREA_THRESHOLD = 1.0       # 1 m² - for tiny entities

    @staticmethod
    def get_preset(profile_name: str):
        """
        Retrieve a preset by its name.
        
        :param profile_name: Profile name (may include precision info in parentheses)
        :return: Preset dictionary
        """
        # Try exact match first
        if profile_name in CLASSIFICATION_PRESETS:
            return CLASSIFICATION_PRESETS[profile_name]
        
        # Try matching base name (before parentheses)
        for key in CLASSIFICATION_PRESETS.keys():
            if key.startswith(profile_name.split('(')[0].strip()):
                return CLASSIFICATION_PRESETS[key]
        
        # Default fallback
        default_key = tr("Land Registry/Cadastre (GPS ±2m)")
        return CLASSIFICATION_PRESETS.get(default_key, list(CLASSIFICATION_PRESETS.values())[0])

    @staticmethod
    def get_profile_names():
        """Return the list of available profile names"""
        return list(CLASSIFICATION_PRESETS.keys())

    @staticmethod
    def classify_point_proximity(distance: float, preset: dict, 
                                 epsilon_dist: float = None) -> str:
        """
        Classify severity according to distance between points.
        
        :param distance: Distance in meters
        :param preset: Classification preset
        :param epsilon_dist: Minimum distance threshold (artifacts filter)
        :return: Severity level string
        """
        eps = epsilon_dist if epsilon_dist is not None else PresetManager.EPSILON_DIST_DEFAULT
        if distance < eps:
            return tr("Low")

        thresholds = preset.get('points', {})
        if distance <= thresholds.get('critical', 0.5):
            return tr("Critical")
        elif distance <= thresholds.get('high', 1.5):
            return tr("High")
        elif distance <= thresholds.get('moderate', 5.0):
            return tr("Moderate")
        else:
            return tr("Low")

    @staticmethod
    def classify_polygon_overlap(area: float, geom1_area: float, geom2_area: float,
                                 preset: dict, epsilon_area: float = None) -> tuple:
        """
        Classify severity of polygon overlap using RATIO-FIRST logic.
        
        PRIORITY 1: Ratio (% of overlap relative to smaller entity)
        PRIORITY 2: Absolute area (only for very small entities)
        
        :param area: Overlap area in m²
        :param geom1_area: Area of first geometry in m²
        :param geom2_area: Area of second geometry in m²
        :param preset: Classification preset
        :param epsilon_area: Minimum area threshold (artifacts filter)
        :return: Tuple (final_severity, details_dict)
        """
        eps = epsilon_area if epsilon_area is not None else PresetManager.EPSILON_AREA_DEFAULT
        
        # STEP 1: Filter artifacts (too small to matter)
        if area < eps:
            return tr("Low"), {
                'area': area,
                'ratio': 0.0,
                'ratio_percent': 0.0,
                'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area else 0,
                'severity_ratio': tr("Low"),
                'severity_absolute': tr("Low"),
                'final_severity': tr("Low"),
                'classification_method': 'epsilon_filter',
                'classification_reason': 'Area below epsilon threshold (noise)'
            }

        # STEP 2: Calculate ratio (PRIORITY 1)
        ratio_value = 0.0
        severity_ratio = tr("Low")
        
        if geom1_area and geom2_area and geom1_area > eps and geom2_area > eps:
            min_area = min(geom1_area, geom2_area)
            if min_area > eps:
                ratio_value = area / min_area
                
                ratio_thresholds = preset.get('polygons_ratio', {})
                
                if ratio_value <= ratio_thresholds.get('low_max', 0.05):
                    severity_ratio = tr("Low")
                elif ratio_value <= ratio_thresholds.get('moderate_max', 0.20):
                    severity_ratio = tr("Moderate")
                elif ratio_value <= ratio_thresholds.get('high_max', 0.50):
                    severity_ratio = tr("High")
                else:
                    severity_ratio = tr("Critical")

        # STEP 3: Calculate absolute severity (PRIORITY 2 - only for small entities)
        severity_absolute = tr("Low")
        classification_method = 'ratio_primary'
        classification_reason = f'Ratio {ratio_value*100:.2f}% is primary criterion'
        
        # Check if BOTH entities are very small
        both_small = (geom1_area and geom2_area and 
                     geom1_area < PresetManager.SMALL_AREA_THRESHOLD and 
                     geom2_area < PresetManager.SMALL_AREA_THRESHOLD)
        
        if both_small:
            # For tiny entities, absolute area also matters
            absolute = preset.get('polygons_absolute', {})
            
            if area <= absolute.get('low_max', 5):
                severity_absolute = tr("Low")
            elif area <= absolute.get('moderate_max', 100):
                severity_absolute = tr("Moderate")
            elif area <= absolute.get('high_max', 500):
                severity_absolute = tr("High")
            else:
                severity_absolute = tr("Critical")
            
            classification_method = 'ratio_and_absolute_hybrid'
            classification_reason = f'Both entities small (<{PresetManager.SMALL_AREA_THRESHOLD}m²). Ratio: {ratio_value*100:.2f}%, Absolute: {area:.2f}m²'
        else:
            # For normal/large entities, ratio is sufficient
            severity_absolute = severity_ratio
        
        # STEP 4: Final severity (RATIO is primary)
        final_severity = severity_ratio
        
        return final_severity, {
            'area': area,
            'ratio': ratio_value,
            'ratio_percent': ratio_value * 100,
            'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area else 0,
            'severity_ratio': severity_ratio,
            'severity_absolute': severity_absolute,
            'final_severity': final_severity,
            'classification_method': classification_method,
            'classification_reason': classification_reason,
            'both_entities_small': both_small
        }

    @staticmethod
    def classify_line_topology(distance_or_length: float, preset: dict, 
                               epsilon: float = None) -> str:
        """
        Classify severity of line topology problem.
        
        :param distance_or_length: Distance/length in meters
        :param preset: Classification preset
        :param epsilon: Minimum threshold (artifacts filter)
        :return: Severity level string
        """
        eps = epsilon if epsilon is not None else PresetManager.EPSILON_LENGTH_DEFAULT
        if distance_or_length < eps:
            return tr("Low")

        thresholds = preset.get('lines', {})
        if distance_or_length <= thresholds.get('critical', 0.01):
            return tr("Critical")
        elif distance_or_length <= thresholds.get('high', 0.1):
            return tr("High")
        elif distance_or_length <= thresholds.get('moderate', 0.5):
            return tr("Moderate")
        else:
            return tr("Low")

    @staticmethod
    def format_threshold_info(preset: dict, geometry_type: str) -> str:
        """
        Format threshold information for display in UI.
        
        :param preset: Classification preset
        :param geometry_type: 'point', 'polygon', or 'line'
        :return: HTML-formatted string
        """
        info = []

        if geometry_type == 'point':
            thresholds = preset.get('points', {})
            info.append(tr("<b>Points - Proximity:</b>"))
            info.append(tr("Critical ≤ {}m").format(thresholds.get('critical', 0.5)))
            info.append(tr("High ≤ {}m").format(thresholds.get('high', 1.5)))
            info.append(tr("Moderate ≤ {}m").format(thresholds.get('moderate', 5.0)))
            if 'examples' in preset and 'points' in preset['examples']:
                info.append(tr("<i>{}</i>").format(preset['examples']['points']))

        elif geometry_type == 'polygon':
            ratio = preset.get('polygons_ratio', {})
            info.append(tr("<b>Polygons - Overlaps (RATIO-FIRST):</b>"))
            info.append(tr("<b>Ratio thresholds (% of smaller entity):</b>"))
            info.append(tr("  Low ≤ {:.0f}%").format(ratio.get('low_max', 0.05)*100))
            info.append(tr("  Moderate ≤ {:.0f}%").format(ratio.get('moderate_max', 0.20)*100))
            info.append(tr("  High ≤ {:.0f}%").format(ratio.get('high_max', 0.50)*100))
            info.append(tr("  Critical > {:.0f}%").format(ratio.get('high_max', 0.50)*100))
            info.append(tr("<i>Impact métier: pourcentage de chevauchement relatif</i>"))
            if 'examples' in preset and 'polygons' in preset['examples']:
                info.append(tr("<i>{}</i>").format(preset['examples']['polygons']))

        elif geometry_type == 'line':
            thresholds = preset.get('lines', {})
            info.append(tr("<b>Lines - Topology:</b>"))
            info.append(tr("Tolerance: {}m").format(thresholds.get('tolerance', 0.5)))
            info.append(tr("Critical ≤ {}m").format(thresholds.get('critical', 0.01)))
            info.append(tr("High ≤ {}m").format(thresholds.get('high', 0.1)))
            info.append(tr("Moderate ≤ {}m").format(thresholds.get('moderate', 0.5)))

        return "<br>".join(info)