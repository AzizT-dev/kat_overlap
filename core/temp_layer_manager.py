# -*- coding: utf-8 -*-
"""
KAT Analysis – Temp Layer Manager  
Temporary layer cleanup utilities
"""

from qgis.core import QgsProject, QgsApplication

def tr(message):
    """Translation helper"""
    return QgsApplication.translate('TempLayerManager', message)


class TempLayerManager:
    """
    Manages temporary layer cleanup operations.
    """
    
    @staticmethod
    def cleanup_temp_layers(dialog):
        """
        Remove all temporary merged layers created during analysis.
        """
        try:
            for layer_name_prefix in ['merged_polygon', 'merged_line', 'merged_point']:
                for lid, layer in list(QgsProject.instance().mapLayers().items()):
                    try:
                        if layer.name().startswith(layer_name_prefix):
                            QgsProject.instance().removeMapLayer(layer.id())
                            if hasattr(dialog, '_log_message'):
                                dialog._log_message("info", tr("🗑️ Temp layer deleted: {}").format(layer.name()))
                    except Exception:
                        pass
        except Exception:
            pass
    
    @staticmethod
    def cleanup_rubber_bands(dialog):
        """
        Remove all rubber bands from map canvas.
        """
        try:
            if hasattr(dialog, '_current_rubber_bands'):
                for rb in dialog._current_rubber_bands:
                    try:
                        dialog.iface.mapCanvas().scene().removeItem(rb)
                    except Exception:
                        pass
                dialog._current_rubber_bands.clear()
        except Exception:
            pass
