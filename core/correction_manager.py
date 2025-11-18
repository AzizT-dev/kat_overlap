# -*- coding: utf-8 -*-
"""
KAT Analysis – Correction Manager  
Apply geometry corrections and deletions based on action column

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from typing import List, Dict, Any
from qgis.core import QgsProject
from core.layer_manager import LayerCorrector


class CorrectionManager:
    """
    Manages correction operations: deletions and trimming based on user actions.
    """
    
    @staticmethod
    def apply_corrections_from_table(dialog):
        """
        Apply corrections using Action column values from results table.
        
        Parameters:
        - dialog: UI dialog reference containing results_table, _original_results, etc.
        """
        if not hasattr(dialog, '_original_results') or not dialog._original_results:
            if hasattr(dialog, '_log_message'):
                dialog._log_message("warning", self.tr("No results available for correction."))
            return
        
        deletes_by_layer = {}
        overlaps_to_trim = []
        
        # Scan results and collect corrections
        for i, res in enumerate(dialog._original_results):
            if i >= dialog.results_table.rowCount():
                continue
            
            # Get action from combo
            combo = dialog.results_table.cellWidget(i, 7)
            action = combo.currentText() if combo else self.tr("Valider")
            
            if action != self.tr("Supprimer"):
                continue
            
            anomaly = res.get("anomaly", res.get("type", ""))
            
            # Handle point duplicates/proximity -> direct deletion
            if anomaly in ("doublon", "point_proximity", "point_duplicate"):
                la = res.get("layer_a") or {}
                lid = la.get("layer_id")
                id_val = res.get("id_a_real") or res.get("id_a")
                deletes_by_layer.setdefault(lid, set()).add(str(id_val))
            
            # Handle overlaps -> trim geometry
            elif anomaly in ("polygon_overlap", "inter_layer_polygon_overlap", "line_overlap"):
                overlaps_to_trim.append(res)
            
            # Default -> deletion
            else:
                la = res.get("layer_a") or {}
                lid = la.get("layer_id")
                id_val = res.get("id_a_real") or res.get("id_a")
                deletes_by_layer.setdefault(lid, set()).add(str(id_val))
        
        # Apply deletions
        for lid, vals in deletes_by_layer.items():
            layer = QgsProject.instance().mapLayer(lid)
            if not layer:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("warning", self.tr("Layer not found: {}").format(lid))
                continue
            
            id_field = dialog.id_fields.get(lid) if hasattr(dialog, 'id_fields') else None
            lc = LayerCorrector(layer, id_field)
            ok, msg = lc.apply_corrections_by_values_or_fids(list(vals))
            
            if ok:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("info", self.tr("Corrections applied on {}: {} deleted.").format(layer.name(), len(vals)))
            else:
                if hasattr(dialog, '_log_message'):
                    dialog._log_message("error", self.tr("Correction error {}: {}").format(layer.name(), msg))
        
        # Apply trimming for overlaps
        if overlaps_to_trim:
            per_layer_geom_to_remove = {}
            
            # Collect intersection geometries per layer
            for r in overlaps_to_trim:
                ga = r.get("layer_a", {}).get("feature")
                gb = r.get("layer_b", {}).get("feature")
                
                try:
                    if ga and gb:
                        inter = ga.geometry().intersection(gb.geometry())
                        if inter and not inter.isEmpty():
                            la = r.get("layer_a", {}).get("layer_id")
                            lb = r.get("layer_b", {}).get("layer_id")
                            per_layer_geom_to_remove.setdefault(la, []).append(inter)
                            per_layer_geom_to_remove.setdefault(lb, []).append(inter)
                except Exception:
                    continue
            
            # Apply trimming per layer
            for lid, geoms in per_layer_geom_to_remove.items():
                layer = QgsProject.instance().mapLayer(lid)
                if not layer:
                    continue
                
                # Combine all geometries to trim
                union_geom = None
                for g in geoms:
                    try:
                        if union_geom is None:
                            union_geom = g.clone()
                        else:
                            union_geom = union_geom.combine(g)
                    except Exception:
                        continue
                
                if union_geom is None:
                    continue
                
                id_field = dialog.id_fields.get(lid) if hasattr(dialog, 'id_fields') else None
                lc = LayerCorrector(layer, id_field)
                ok, msg = lc.apply_trimming_by_geometry(union_geom)
                
                if ok:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("info", self.tr("Trim applied on {}.").format(layer.name()))
                else:
                    if hasattr(dialog, '_log_message'):
                        dialog._log_message("error", self.tr("Trim error {}: {}").format(layer.name(), msg))
        
        if hasattr(dialog, '_log_message'):
            dialog._log_message("info", self.tr("Corrections completed. Restart analysis to verify."))