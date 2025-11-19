# -*- coding: utf-8 -*-
"""
KAT Analysis – ID Resolver
Utilities for resolving result IDs to layers and features

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import Tuple, Optional, Any
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsFeatureRequest


class IDResolver:
    """
    Resolves result IDs (raw_id or LayerName:fid format) to layer and feature.
    """
    
    @staticmethod
    def resolve_result_id_value(raw_id: Any) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse raw_id to extract layer name and FID.
        
        Format: "LayerName:123" or just "123"
        
        Parameters:
        - raw_id: Raw ID value (string or int)
        
        Returns:
        - Tuple (layer_name, fid) or (None, fid) if no layer prefix
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
                    return layer_name, None
        
        # Try to parse as FID only
        try:
            fid = int(raw_str)
            return None, fid
        except ValueError:
            return raw_str, None
    
    @staticmethod
    def resolve_result_to_layer_and_fid(dialog, raw_id: Any) -> Tuple[Optional[QgsVectorLayer], Optional[int]]:
        """
        Resolve raw_id to QgsVectorLayer and FID.
        
        Parameters:
        - dialog: UI dialog reference (for accessing selected_layers, layer_widgets)
        - raw_id: Raw ID value
        
        Returns:
        - Tuple (layer, fid) or (None, None) if not found
        """
        layer_name, fid = IDResolver.resolve_result_id_value(raw_id)
        
        if layer_name:
            # Search in project layers by name
            for lid, lyr in QgsProject.instance().mapLayers().items():
                if isinstance(lyr, QgsVectorLayer) and lyr.name() == layer_name:
                    return lyr, fid
            return None, fid
        
        elif fid is not None:
            # If only FID, search in selected layers
            if hasattr(dialog, 'selected_layers'):
                for lid in dialog.selected_layers:
                    layer = QgsProject.instance().mapLayer(lid)
                    if layer:
                        return layer, fid
            return None, fid
        
        return None, None
    
    @staticmethod
    def resolve_result_to_layer_and_attr(dialog, raw_id: Any, attr_name: str = None) -> Tuple[Optional[QgsVectorLayer], Optional[Any]]:
        """
        Resolve raw_id to layer and search by attribute value.
        
        Parameters:
        - dialog: UI dialog reference
        - raw_id: Raw ID value
        - attr_name: Attribute field name to search (if None, uses FID)
        
        Returns:
        - Tuple (layer, feature) or (None, None) if not found
        """
        layer, fid_or_val = IDResolver.resolve_result_to_layer_and_fid(dialog, raw_id)
        
        if not layer or fid_or_val is None:
            return None, None
        
        # If attr_name provided, search by attribute
        if attr_name and attr_name in [f.name() for f in layer.fields()]:
            request = QgsFeatureRequest().setFilterExpression(f'"{attr_name}" = \'{fid_or_val}\'')
            features = list(layer.getFeatures(request))
            if features:
                return layer, features[0]
            return layer, None
        
        # Otherwise search by FID
        try:
            feat = layer.getFeature(fid_or_val)
            if feat.isValid():
                return layer, feat
        except Exception:
            pass
        
        return layer, None