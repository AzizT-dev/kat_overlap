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
    tr("Foncier/Cadastre (GPS ±2m)"): {
        'description': tr('Cadastre, land parcels, land boundaries'),
        'precision_info': tr('Consumer GPS ±2m'),
        'points': {
            'critique': 0.5,    # ≤ 0.5m → Critical
            'elevee': 1.5,      # ≤ 1.5m → High
            'moderee': 5.0,     # ≤ 5m → Moderate
            'faible': float('inf')  # > 5m → Low
        },
        'polygones_absolu': {
            'faible_max': 5,      # 0-5 m² → Low
            'moderee_max': 100,   # 5-100 m² → Moderate
            'elevee_max': 500,    # 100-500 m² → High
            'critique_min': 500   # > 500 m² → Critical
        },
        'polygones_ratio': {
            'faible_max': 0.05,    # ≤ 5% → Low
            'moderee_max': 0.20,   # ≤ 20% → Moderate
            'elevee_max': 0.50,    # ≤ 50% → High
            'critique_min': 0.50   # > 50% → Critical
        },
        'lignes': {
            'tolerance': 0.5,  # Topological tolerance in meters
            'critique': 0.01,
            'elevee': 0.1,
            'moderee': 0.5
        },
        'exemples': {
            'points': tr("0.5m ≈ manual pointing error"),
            'polygones': tr("5m² ≈ 2.5m × 2m (standard GPS precision)")
        }
    },

    tr("BTP/Construction (GPS RTK ±0.05m)"): {
        'description': tr('Construction sites, implementations, structures'),
        'precision_info': tr('RTK GPS ±0.05m'),
        'points': {
            'critique': 0.05,
            'elevee': 0.2,
            'moderee': 0.5,
            'faible': float('inf')
        },
        'polygones_absolu': {
            'faible_max': 0.5,
            'moderee_max': 10,
            'elevee_max': 50,
            'critique_min': 50
        },
        'polygones_ratio': {
            'faible_max': 0.05,
            'moderee_max': 0.20,
            'elevee_max': 0.50,
            'critique_min': 0.50
        },
        'lignes': {
            'tolerance': 0.05,
            'critique': 0.01,
            'elevee': 0.02,
            'moderee': 0.05
        },
        'exemples': {
            'points': tr("0.05m = 5cm (implementation tolerance)"),
            'polygones': tr("0.5m² ≈ 70cm × 70cm (foundation)")
        }
    },

    tr("Topographie (Station ±0.01m)"): {
        'description': tr('Precise surveys, topography, geodesy'),
        'precision_info': tr('Total station ±0.01m'),
        'points': {
            'critique': 0.01,
            'elevee': 0.03,
            'moderee': 0.1,
            'faible': float('inf')
        },
        'polygones_absolu': {
            'faible_max': 1,
            'moderee_max': 50,
            'elevee_max': 200,
            'critique_min': 200
        },
        'polygones_ratio': {
            'faible_max': 0.05,
            'moderee_max': 0.20,
            'elevee_max': 0.50,
            'critique_min': 0.50
        },
        'lignes': {
            'tolerance': 0.01,
            'critique': 0.005,
            'elevee': 0.01,
            'moderee': 0.05
        },
        'exemples': {
            'points': tr("0.01m = 1cm (high precision)"),
            'polygones': tr("1m² = millimeter precision")
        }
    },

    tr("Hydrologie (SIG ±10m)"): {
        'description': tr('Watersheds, hydrographic networks'),
        'precision_info': tr('GIS data ±10m'),
        'points': {
            'critique': 2.0,
            'elevee': 5.0,
            'moderee': 10.0,
            'faible': float('inf')
        },
        'polygones_absolu': {
            'faible_max': 100,
            'moderee_max': 1000,
            'elevee_max': 5000,
            'critique_min': 5000
        },
        'polygones_ratio': {
            'faible_max': 0.05,
            'moderee_max': 0.20,
            'elevee_max': 0.50,
            'critique_min': 0.50
        },
        'lignes': {
            'tolerance': 2.0,
            'critique': 0.5,
            'elevee': 1.0,
            'moderee': 2.0
        },
        'exemples': {
            'points': tr("2m ≈ acceptable cartographic shift"),
            'polygones': tr("100m² ≈ small retention basin")
        }
    },

    tr("Personnalisé"): {
        'description': tr("User-defined thresholds"),
        'precision_info': tr('Variable according to context'),
        'points': {
            'critique': 0.5,
            'elevee': 1.5,
            'moderee': 5.0,
            'faible': float('inf')
        },
        'polygones_absolu': {
            'faible_max': 5,
            'moderee_max': 100,
            'elevee_max': 500,
            'critique_min': 500
        },
        'polygones_ratio': {
            'faible_max': 0.05,
            'moderee_max': 0.20,
            'elevee_max': 0.50,
            'critique_min': 0.50
        },
        'lignes': {
            'tolerance': 0.5,
            'critique': 0.01,
            'elevee': 0.1,
            'moderee': 0.5
        },
        'exemples': {
            'points': tr("Define according to your needs"),
            'polygones': tr("Adapt to project specifics")
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

        return CLASSIFICATION_PRESETS.get(clean_name, CLASSIFICATION_PRESETS[tr("Foncier/Cadastre (GPS ±2m)")])

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
            return tr("Faible")

        thresholds = preset.get('points', {})
        if distance <= thresholds.get('critique', 0.5):
            return tr("Critique")
        elif distance <= thresholds.get('elevee', 1.5):
            return tr("Élevée")
        elif distance <= thresholds.get('moderee', 5.0):
            return tr("Modérée")
        else:
            return tr("Faible")

    @staticmethod
    def classify_polygon_overlap(area, geom1_area, geom2_area, preset, epsilon_area=None):
        """
        Classify severity of polygon overlap.
        Ignore artifacts < epsilon_area.
        Use hybrid logic: absolute + ratio.
        """
        eps = epsilon_area if epsilon_area is not None else PresetManager.EPSILON_AREA_DEFAULT
        if area < eps:
            return tr("Faible"), {
                'area': area,
                'ratio': 0.0,
                'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area else 0,
                'severity_absolu': tr("Faible"),
                'severity_ratio': tr("Faible"),
                'classification_method': 'hybride'
            }

        absolu = preset.get('polygones_absolu', {})
        ratio_thresholds = preset.get('polygones_ratio', {})

        # Absolute classification
        if area <= absolu.get('faible_max', 5):
            severity_absolu = tr("Faible")
        elif area <= absolu.get('moderee_max', 100):
            severity_absolu = tr("Modérée")
        elif area <= absolu.get('elevee_max', 500):
            severity_absolu = tr("Élevée")
        else:
            severity_absolu = tr("Critique")

        # Ratio classification
        severity_ratio = tr("Faible")
        ratio_value = 0.0
        if geom1_area is not None and geom2_area is not None and geom1_area > 0 and geom2_area > 0:
            min_area = min(geom1_area, geom2_area)
            ratio_value = area / max(min_area, eps)
            if ratio_value <= ratio_thresholds.get('faible_max', 0.05):
                severity_ratio = tr("Faible")
            elif ratio_value <= ratio_thresholds.get('moderee_max', 0.20):
                severity_ratio = tr("Modérée")
            elif ratio_value <= ratio_thresholds.get('elevee_max', 0.50):
                severity_ratio = tr("Élevée")
            else:
                severity_ratio = tr("Critique")

        severity_levels = {tr("Faible"): 0, tr("Modérée"): 1, tr("Élevée"): 2, tr("Critique"): 3}
        final_severity = max([severity_absolu, severity_ratio],
                             key=lambda x: severity_levels.get(x, 0))

        return final_severity, {
            'area': area,
            'ratio': ratio_value,
            'ratio_percent': ratio_value * 100,
            'min_source_area': min(geom1_area, geom2_area) if geom1_area and geom2_area and geom1_area > 0 and geom2_area > 0 else 0,
            'severity_absolu': severity_absolu,
            'severity_ratio': severity_ratio,
            'classification_method': 'hybride'
        }

    @staticmethod
    def classify_line_topology(distance, preset, epsilon_dist=None):
        """
        Classify severity of line topology problem.
        Ignore artifacts < epsilon_dist.
        """
        eps = epsilon_dist if epsilon_dist is not None else PresetManager.EPSILON_DIST_DEFAULT
        if distance < eps:
            return tr("Faible")

        thresholds = preset.get('lignes', {})
        if distance <= thresholds.get('critique', 0.01):
            return tr("Critique")
        elif distance <= thresholds.get('elevee', 0.1):
            return tr("Élevée")
        elif distance <= thresholds.get('moderee', 0.5):
            return tr("Modérée")
        else:
            return tr("Faible")

    @staticmethod
    def format_threshold_info(preset, geometry_type):
        """
        Format threshold information for display.
        """
        info = []

        if geometry_type == 'point':
            thresholds = preset.get('points', {})
            info.append(tr("<b>Points - Proximity:</b>"))
            info.append(tr("Critical ≤ {}m").format(thresholds.get('critique', 0.5)))
            info.append(tr("High ≤ {}m").format(thresholds.get('elevee', 1.5)))
            info.append(tr("Moderate ≤ {}m").format(thresholds.get('moderee', 5.0)))
            if 'exemples' in preset and 'points' in preset['exemples']:
                info.append(tr("<i>{}</i>").format(preset['exemples']['points']))

        elif geometry_type == 'polygon':
            absolu = preset.get('polygones_absolu', {})
            ratio = preset.get('polygones_ratio', {})
            info.append(tr("<b>Polygons - Overlaps:</b>"))
            info.append(tr("<b>Absolute thresholds:</b>"))
            info.append(tr("  Low ≤ {}m²").format(absolu.get('faible_max', 5)))
            info.append(tr("  Moderate ≤ {}m²").format(absolu.get('moderee_max', 100)))
            info.append(tr("  High ≤ {}m²").format(absolu.get('elevee_max', 500)))
            info.append(tr("  Critical > {}m²").format(absolu.get('elevee_max', 500)))
            info.append(tr("<b>Ratio thresholds:</b>"))
            info.append(tr("  Low ≤ {:.0f}%").format(ratio.get('faible_max', 0.05)*100))
            info.append(tr("  Moderate ≤ {:.0f}%").format(ratio.get('moderee_max', 0.20)*100))
            info.append(tr("  High ≤ {:.0f}%").format(ratio.get('elevee_max', 0.50)*100))
            if 'exemples' in preset and 'polygones' in preset['exemples']:
                info.append(tr("<i>{}</i>").format(preset['exemples']['polygones']))

        elif geometry_type == 'line':
            thresholds = preset.get('lignes', {})
            info.append(tr("<b>Lines - Topology:</b>"))
            info.append(tr("Tolerance: {}m").format(thresholds.get('tolerance', 0.5)))
            info.append(tr("Critical ≤ {}m").format(thresholds.get('critique', 0.01)))
            info.append(tr("High ≤ {}m").format(thresholds.get('elevee', 0.1)))
            info.append(tr("Moderate ≤ {}m").format(thresholds.get('moderee', 0.5)))

        return "<br>".join(info)