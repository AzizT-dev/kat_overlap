# -*- coding: utf-8 -*-
"""
KAT Analysis – Utilities
ID resolution, file operations, logging helpers

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

import os
import traceback
from typing import Optional, Any, Tuple, Dict
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, 
    QgsFeatureRequest, Qgis, QgsMessageLog
)
from qgis.PyQt.QtCore import QCoreApplication

LOG_TAG = "KATOverlap"


# ==================TRANSLATION & LOGGING====================

def tr(message: str, context: str = "KATOverlap") -> str:
    """Get translation for a string using Qt translation API"""
    return QCoreApplication.translate(context, message)


def log_message(level: str, message: str, exception: Optional[Exception] = None):
    """
    Centralized logging with exception handling
    
    :param level: 'info', 'warning', 'error', 'critical'
    :param message: Log message
    :param exception: Optional exception to log traceback
    """
    qgis_level = {
        'info': Qgis.Info,
        'warning': Qgis.Warning,
        'error': Qgis.Critical,
        'critical': Qgis.Critical
    }.get(level.lower(), Qgis.Info)
    
    try:
        QgsMessageLog.logMessage(message, LOG_TAG, qgis_level)
        
        if exception and qgis_level == Qgis.Critical:
            tb = traceback.format_exc()
            QgsMessageLog.logMessage(
                f"Traceback:\n{tb}", 
                LOG_TAG, 
                Qgis.Critical
            )
    except Exception as e:
        print(f"[{LOG_TAG}] Logging failed: {e}")
        print(f"[{LOG_TAG}] Original message: {message}")


# ==================FILE UTILITIES===================

def ensure_parent_dir(path: str) -> None:
    """Create parent directories if they don't exist"""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            log_message('error', f"Failed to create directory {parent}: {e}")


def get_safe_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize filename by removing invalid characters
    
    :param name: Original filename
    :param max_length: Maximum filename length
    :return: Safe filename
    """
    import re
    # Remove invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Limit length
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe


# ==================ID RESOLVER====================

class IDResolver:
    """
    Resolves result IDs (raw_id or LayerName:fid format) to layer and feature.
    Thread-safe and deterministic.
    """
    
    @staticmethod
    def resolve_result_id_value(raw_id: Any) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse raw_id to extract layer name and FID.
        
        Format: "LayerName:123" or just "123"
        
        :param raw_id: Raw ID value (string or int)
        :return: Tuple (layer_name, fid) or (None, fid) if no layer prefix
        """
        if raw_id is None:
            return None, None
        
        raw_str = str(raw_id).strip()
        if not raw_str:
            return None, None
        
        # Check for "LayerName:fid" format
        if ":" in raw_str:
            parts = raw_str.split(":", 1)
            if len(parts) == 2:
                layer_name = parts[0].strip()
                try:
                    fid = int(parts[1].strip())
                    return layer_name, fid
                except ValueError:
                    log_message('warning', f"Invalid FID in ID: {raw_str}")
                    return layer_name, None
        
        # Try to parse as FID only
        try:
            fid = int(raw_str)
            return None, fid
        except ValueError:
            return raw_str, None
    
    @staticmethod
    def resolve_to_layer_and_fid(
        raw_id: Any, 
        selected_layer_ids: set = None
    ) -> Tuple[Optional[QgsVectorLayer], Optional[int]]:
        """
        Resolve raw_id to QgsVectorLayer and FID.
        
        :param raw_id: Raw ID value
        :param selected_layer_ids: Set of selected layer IDs (fallback search)
        :return: Tuple (layer, fid) or (None, None) if not found
        """
        layer_name, fid = IDResolver.resolve_result_id_value(raw_id)
        
        if layer_name:
            # Search in project layers by name
            for lid, lyr in QgsProject.instance().mapLayers().items():
                if isinstance(lyr, QgsVectorLayer) and lyr.name() == layer_name:
                    return lyr, fid
            log_message('warning', f"Layer not found: {layer_name}")
            return None, fid
        
        elif fid is not None:
            # If only FID, search in selected layers
            if selected_layer_ids:
                for lid in selected_layer_ids:
                    layer = QgsProject.instance().mapLayer(lid)
                    if layer:
                        return layer, fid
            return None, fid
        
        return None, None
    
    @staticmethod
    def resolve_to_feature(
        raw_id: Any, 
        selected_layer_ids: set = None,
        attr_name: str = None
    ) -> Tuple[Optional[QgsVectorLayer], Optional[QgsFeature]]:
        """
        Resolve raw_id to layer and feature.
        
        :param raw_id: Raw ID value
        :param selected_layer_ids: Set of selected layer IDs
        :param attr_name: Attribute field name to search (if None, uses FID)
        :return: Tuple (layer, feature) or (None, None) if not found
        """
        layer, fid_or_val = IDResolver.resolve_to_layer_and_fid(
            raw_id, selected_layer_ids
        )
        
        if not layer or fid_or_val is None:
            return None, None
        
        # If attr_name provided, search by attribute
        if attr_name and attr_name in [f.name() for f in layer.fields()]:
            try:
                # Use proper SQL escaping
                expr = f'"{attr_name}" = \'{str(fid_or_val).replace("\'", "\'\'")}\''
                request = QgsFeatureRequest().setFilterExpression(expr)
                features = list(layer.getFeatures(request))
                if features:
                    return layer, features[0]
            except Exception as e:
                log_message('error', f"Attribute search failed: {e}", e)
            return layer, None
        
        # Otherwise search by FID
        try:
            feat = layer.getFeature(fid_or_val)
            if feat.isValid():
                return layer, feat
        except Exception as e:
            log_message('error', f"FID lookup failed: {e}", e)
        
        return layer, None


# ===========================================================================
# TEMP LAYER TRACKING
# ===========================================================================

class TempLayerTracker:
    """
    Tracks temporary layers created during analysis for proper cleanup.
    Thread-safe singleton pattern.
    """
    
    _instance = None
    _tracked_layers = set()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def track_layer(cls, layer_id: str):
        """Add a layer ID to tracking"""
        cls._tracked_layers.add(layer_id)
        log_message('info', f"Tracking temp layer: {layer_id}")
    
    @classmethod
    def cleanup_all(cls):
        """Remove all tracked temporary layers"""
        count = 0
        for layer_id in list(cls._tracked_layers):
            try:
                layer = QgsProject.instance().mapLayer(layer_id)
                if layer:
                    QgsProject.instance().removeMapLayer(layer_id)
                    count += 1
            except Exception as e:
                log_message('warning', f"Failed to remove layer {layer_id}: {e}")
        
        cls._tracked_layers.clear()
        if count > 0:
            log_message('info', f"Cleaned up {count} temporary layers")
    
    @classmethod
    def is_tracked(cls, layer_id: str) -> bool:
        """Check if a layer is tracked"""
        return layer_id in cls._tracked_layers
    
    @classmethod
    def untrack_layer(cls, layer_id: str):
        """Remove a layer from tracking"""
        cls._tracked_layers.discard(layer_id)


# =================RESULT DTO SCHEMA=====================

RESULT_SCHEMA = {
    'type': str,           # Anomaly type
    'anomaly': str,        # Alias for type
    'id_a': str,          # ID feature A
    'id_b': str,          # ID feature B
    'id_a_real': str,     # Real ID (from attribute)
    'id_b_real': str,     # Real ID (from attribute)
    'layer_a_id': str,    # Layer ID for feature A
    'layer_b_id': str,    # Layer ID for feature B
    'measure': float,     # Generic measure (distance/area)
    'area_m2': float,     # Area in m² (for overlaps)
    'ratio': float,       # Ratio (0-1)
    'ratio_percent': float,  # Ratio as percentage
    'severity': str,      # Critical/High/Moderate/Low
    'geometry_json': str, # GeoJSON geometry
    'geometry_wkt': str,  # WKT geometry (optional)
}


def validate_result(result: Dict[str, Any]) -> bool:
    """
    Validate a result dictionary against schema.
    
    :param result: Result dictionary to validate
    :return: True if valid, False otherwise
    """
    required_keys = {'type', 'id_a', 'id_b', 'measure', 'severity'}
    
    if not all(key in result for key in required_keys):
        missing = required_keys - set(result.keys())
        log_message('warning', f"Result missing keys: {missing}")
        return False
    
    return True


def normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a result dictionary to ensure all expected keys exist.
    
    :param result: Raw result dictionary
    :return: Normalized result dictionary
    """
    normalized = result.copy()
    
    # Ensure anomaly/type consistency
    if 'anomaly' not in normalized and 'type' in normalized:
        normalized['anomaly'] = normalized['type']
    elif 'type' not in normalized and 'anomaly' in normalized:
        normalized['type'] = normalized['anomaly']
    
    # Ensure id_a_real/id_b_real
    if 'id_a_real' not in normalized:
        normalized['id_a_real'] = normalized.get('id_a', '')
    if 'id_b_real' not in normalized:
        normalized['id_b_real'] = normalized.get('id_b', '')
    
    # Ensure ratio_percent
    if 'ratio_percent' not in normalized and 'ratio' in normalized:
        try:
            normalized['ratio_percent'] = float(normalized['ratio']) * 100.0
        except (ValueError, TypeError):
            normalized['ratio_percent'] = 0.0
    
    # Set defaults for missing values
    defaults = {
        'measure': 0.0,
        'area_m2': 0.0,
        'ratio': 0.0,
        'ratio_percent': 0.0,
        'severity': 'Low',
    }
    
    for key, default_val in defaults.items():
        if key not in normalized or normalized[key] is None:
            normalized[key] = default_val
    
    return normalized
