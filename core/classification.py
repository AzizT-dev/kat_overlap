# -*- coding: utf-8 -*-
"""
KAT Analysis – Classification & Presets
Business profile threshold management + EPSILON filters

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from qgis.core import QgsApplication

def tr(message):
    """Get the translation for a string using Qt translation API."""
    return QgsApplication.translate('Classification', message)

# ============================================================================
# CLASSIFICATION PRESETS DATA
# ============================================================================

CLASSIFICATION_PRESETS = {
    tr("Land Registry/Cadastre (GPS ±2m)"): {
        'description': tr('Cadastre, land parcels, land boundaries'),
        'precision_info': tr('Consumer GPS ±2m'),
        'points': {
            'critical': 0.5,    # ≤ 0.5m → Critical
            'high': 1.5,        # ≤ 1.5m → High
            'moderate': 5.0,    # ≤ 5m → Moderate
            'low': float('inf') # > 5m → Low
        },
        'polygons_absolute': {
            'low_max': 5,       # 0-5 m² → Low
            'moderate_max': 100,# 5-100 m² → Moderate
            'high_max': 500,    # 100-500 m² → High
            'critical_min': 500 # > 500 m² → Critical
        },
        'polygons_ratio': {
            'low_max': 0.05,    # ≤ 5% → Low
            'moderate_max': 0.20,# ≤ 20% → Moderate
            'high_max': 0.50,   # ≤ 50% → High
            'critical_min': 0.50 # > 50% → Critical
        },
        'lines': {
            'tolerance': 0.5,   # Topological tolerance in meters
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


# ============================================================================
# PRESET MANAGER (Classification Logic)
# ============================================================================

class PresetManager:
    """Preset classification manager with EPSILON filters"""

    # Default values to filter artifacts
    EPSILON_AREA_DEFAULT = 1e-6      # Minimum area m²
    EPSILON_DIST_DEFAULT = 1e-6      # Minimum distance m

    @staticmethod
    def get_preset(profile_name):
        """
        Retrieve a preset by its name.
        If not found, return the default preset.
        """
        clean_name = profile_name
        for key in CLASSIFICATION_PRESETS.keys():
            if key.startswith(profile_name.split('(')[0].strip()):
                clean_name = key
                break

        return CLASSIFICATION_PRESETS.get(clean_name, CLASSIFICATION_PRESETS[tr("Land Registry/Cadastre (GPS ±2m)")])

    @staticmethod
    def get_profile_names():
        """Return the list of available profile names."""
        return list(CLASSIFICATION_PRESETS.keys())

    @staticmethod
    def classify_point_proximity(distance, preset, epsilon_dist=None):
        """
        Classify severity according to distance between points.
        Ignore artifacts < epsilon_dist.
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
    def classify_polygon_overlap(area, geom1_area, geom2_area, preset, epsilon_area=None):
        """
        Classify severity of polygon overlap.
        Ignore artifacts < epsilon_area.
        Use hybrid logic: absolute + ratio.
        """
        eps = epsilon_area if epsilon_area is not None else PresetManager.EPSILON_AREA_DEFAULT
        if area < eps:
            return tr("Low"), {
                'area': area,
                'ratio': 0.0,
                'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area else 0,
                'severity_absolute': tr("Low"),
                'severity_ratio': tr("Low"),
                'classification_method': 'hybrid'
            }

        absolute = preset.get('polygons_absolute', {})
        ratio_thresholds = preset.get('polygons_ratio', {})

        # Absolute classification
        if area <= absolute.get('low_max', 5):
            severity_absolute = tr("Low")
        elif area <= absolute.get('moderate_max', 100):
            severity_absolute = tr("Moderate")
        elif area <= absolute.get('high_max', 500):
            severity_absolute = tr("High")
        else:
            severity_absolute = tr("Critical")

        # Ratio classification
        severity_ratio = tr("Low")
        ratio_value = 0.0
        if geom1_area is not None and geom2_area is not None and geom1_area > 0 and geom2_area > 0:
            min_area = min(geom1_area, geom2_area)
            ratio_value = area / max(min_area, eps)
            if ratio_value <= ratio_thresholds.get('low_max', 0.05):
                severity_ratio = tr("Low")
            elif ratio_value <= ratio_thresholds.get('moderate_max', 0.20):
                severity_ratio = tr("Moderate")
            elif ratio_value <= ratio_thresholds.get('high_max', 0.50):
                severity_ratio = tr("High")
            else:
                severity_ratio = tr("Critical")

        severity_levels = {tr("Low"): 0, tr("Moderate"): 1, tr("High"): 2, tr("Critical"): 3}
        final_severity = max([severity_absolute, severity_ratio],
                             key=lambda x: severity_levels.get(x, 0))

        return final_severity, {
            'area': area,
            'ratio': ratio_value,
            'ratio_percent': ratio_value * 100,
            'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area and geom1_area > 0 and geom2_area > 0 else 0,
            'severity_absolute': severity_absolute,
            'severity_ratio': severity_ratio,
            'classification_method': 'hybrid'
        }

    @staticmethod
    def classify_line_topology(distance, preset, epsilon_dist=None):
        """
        Classify severity of line topology problem.
        Ignore artifacts < epsilon_dist.
        """
        eps = epsilon_dist if epsilon_dist is not None else PresetManager.EPSILON_DIST_DEFAULT
        if distance < eps:
            return tr("Low")

        thresholds = preset.get('lines', {})
        if distance <= thresholds.get('critical', 0.01):
            return tr("Critical")
        elif distance <= thresholds.get('high', 0.1):
            return tr("High")
        elif distance <= thresholds.get('moderate', 0.5):
            return tr("Moderate")
        else:
            return tr("Low")

    @staticmethod
    def format_threshold_info(preset, geometry_type):
        """
        Format threshold information for display.
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
            absolute = preset.get('polygons_absolute', {})
            ratio = preset.get('polygons_ratio', {})
            info.append(tr("<b>Polygons - Overlaps:</b>"))
            info.append(tr("<b>Absolute thresholds:</b>"))
            info.append(tr("  Low ≤ {}m²").format(absolute.get('low_max', 5)))
            info.append(tr("  Moderate ≤ {}m²").format(absolute.get('moderate_max', 100)))
            info.append(tr("  High ≤ {}m²").format(absolute.get('high_max', 500)))
            info.append(tr("  Critical > {}m²").format(absolute.get('high_max', 500)))
            info.append(tr("<b>Ratio thresholds:</b>"))
            info.append(tr("  Low ≤ {:.0f}%").format(ratio.get('low_max', 0.05)*100))
            info.append(tr("  Moderate ≤ {:.0f}%").format(ratio.get('moderate_max', 0.20)*100))
            info.append(tr("  High ≤ {:.0f}%").format(ratio.get('high_max', 0.50)*100))
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