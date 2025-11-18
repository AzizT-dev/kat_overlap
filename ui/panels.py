# -*- coding: utf-8 -*-
"""
KAT Analysis – UI Panels  
UI panel creation functions

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QCheckBox, QButtonGroup, QGroupBox
)
from PyQt5.QtCore import Qt
from qgis.gui import QgsProjectionSelectionWidget


class UIPanels:
    """
    Factory methods for creating UI panels and widgets.
    """
    
    @staticmethod
    def create_crs_group(dialog) -> QGroupBox:
        """
        Create CRS selection group box.
        
        Parameters:
        - dialog: Parent dialog
        
        Returns:
        - QGroupBox with CRS selection widgets
        """
        crs_group = QGroupBox(dialog.tr("Système de coordonnées de sortie"))
        crs_layout = QVBoxLayout()
        
        dialog.radio_crs_source = QRadioButton(dialog.tr("Conserver le CRS de la couche source"))
        dialog.radio_crs_custom = QRadioButton(dialog.tr("Choisir un EPSG personnalisé"))
        dialog.radio_crs_source.setChecked(True)
        
        bgrp = QButtonGroup()
        bgrp.addButton(dialog.radio_crs_source)
        bgrp.addButton(dialog.radio_crs_custom)
        
        dialog.radio_crs_custom.toggled.connect(
            lambda checked: dialog.crs_selector.setEnabled(checked)
        )
        
        crs_layout.addWidget(dialog.radio_crs_source)
        crs_layout.addWidget(dialog.radio_crs_custom)
        
        dialog.crs_selector = QgsProjectionSelectionWidget()
        dialog.crs_selector.setEnabled(False)
        crs_layout.addWidget(dialog.crs_selector)
        
        crs_group.setLayout(crs_layout)
        return crs_group
    
    @staticmethod
    def create_options_group(dialog) -> QGroupBox:
        """
        Create options group box.
        
        Parameters:
        - dialog: Parent dialog
        
        Returns:
        - QGroupBox with option checkboxes
        """
        options_group = QGroupBox(dialog.tr("Options"))
        options_layout = QVBoxLayout()
        
        dialog.create_layer_checkbox = QCheckBox(dialog.tr("Créer une couche de résultats"))
        dialog.create_layer_checkbox.setChecked(True)
        options_layout.addWidget(dialog.create_layer_checkbox)
        
        dialog.generate_fid_checkbox = QCheckBox(dialog.tr("Générer un Fid (pour Points)"))
        dialog.generate_fid_checkbox.setToolTip(
            dialog.tr("Générer un identifiant unique par point pour éviter faux doublons "
            "(points issus de sommets partagés).")
        )
        options_layout.addWidget(dialog.generate_fid_checkbox)
        
        options_group.setLayout(options_layout)
        return options_group