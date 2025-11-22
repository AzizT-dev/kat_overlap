# -*- coding: utf-8 -*-
"""
KAT Overlap - Main plugin class
QGIS plugin for overlap analysis

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 2.0.0
"""

import os, sys
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings
from qgis.core import QgsMessageLog, Qgis

# Plugin path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

class KATOverlap:
    """Main QGIS plugin class for overlap analysis"""

    def __init__(self, iface):
        """Constructor
        
        :param iface: QGIS interface
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        self.action = None
        self.dialog = None
        self.translator = None
        
        self.load_translations()

    def load_translations(self):
        """Load plugin translations"""
        i18n_dir = os.path.join(self.plugin_dir, 'i18n')
        locale = QSettings().value('locale/userLocale', 'en')
        if isinstance(locale, str):
            locale = locale.split('_')[0]

        translation_file = f'kat_overlap_{locale}.qm'
        translation_path = os.path.join(i18n_dir, translation_file)
        
        try:
            if os.path.exists(translation_path):
                self.translator = QTranslator()
                if self.translator.load(translation_path):
                    QCoreApplication.installTranslator(self.translator)
                else:
                    QgsMessageLog.logMessage(
                        f"Failed to load translation file: {translation_path}",
                        "KATOverlap",
                        level=Qgis.Warning
                    )
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error loading translations: {e}",
                "KATOverlap",
                level=Qgis.Critical
            )

    def initGui(self):
        """Create menu entries and toolbar icons"""
        
        plugin_name = QCoreApplication.translate("KATOverlap", "KAT Overlap Analyzer")
        whats_this = QCoreApplication.translate("KATOverlap", "Analyze polygon overlap areas")
        status_tip = QCoreApplication.translate("KATOverlap", "Detect and analyze overlapping zones")
        tool_tip = QCoreApplication.translate("KATOverlap", "KAT Analysis – Overlap area (Multi-Types)")
        
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        self.action = QAction(icon, plugin_name, self.iface.mainWindow())
        self.action.setWhatsThis(whats_this)
        self.action.setStatusTip(status_tip)
        self.action.setToolTip(tool_tip)
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToVectorMenu("&KAT Tools", self.action)
        self.iface.addVectorToolBarIcon(self.action)

    def unload(self):
        """Remove plugin from menu and toolbar"""
        if self.action:
            self.iface.removePluginVectorMenu("&KAT Tools", self.action)
            self.iface.removeVectorToolBarIcon(self.action)
            self.action = None

        if self.translator:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None

        if self.dialog:
            self.dialog.close()
            self.dialog = None

    def run(self):
        """Launch the dialog"""
        from .ui.kat_overlap_ui import ModernKatOverlapUI
        if not self.dialog:
            self.dialog = ModernKatOverlapUI(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def tr(self, message):
        """Return translation for a string using Qt translation API"""
        return QCoreApplication.translate('KATOverlap', message)
