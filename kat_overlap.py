# -*- coding: utf-8 -*-

"""
KAT Overlap - Classe principale
Gestion du plugin dans QGIS


Author: Aziz T.
Copyright: (C) 2025 KaT - Tous droits réservés
License: GPLv3
Version: 1.0.0
"""

import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings

class KATOverlap:
    """Plugin principal QGIS pour l'analyse des chevauchements"""

    def __init__(self, iface):
        """Constructeur
        
        :param iface: Interface QGIS
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        self.action = None
        self.dialog = None
        self.translator = None
        
        self.load_translations()

    def load_translations(self):
        """Charge les traductions au niveau du plugin"""
        try:
            # Chemin vers i18n
            i18n_dir = os.path.join(self.plugin_dir, 'i18n')
            
            # Obtenir la locale
            locale = QSettings().value('locale/userLocale', 'en')
            if isinstance(locale, str):
                locale = locale.split('_')[0]  # 'fr_FR' → 'fr'
            
            print(self.tr("🌍 Plugin - Chargement traduction: {}").format(locale))
            
            translation_file = f'kat_overlap_{locale}.qm'
            translation_path = os.path.join(i18n_dir, translation_file)
            
            print(self.tr("📁 Plugin - Chemin: {}").format(translation_path))
            print(self.tr("📁 Plugin - Existe: {}").format(os.path.exists(translation_path)))
            
            if os.path.exists(translation_path):
                self.translator = QTranslator()
                if self.translator.load(translation_path):
                    QCoreApplication.installTranslator(self.translator)
                    print(self.tr("✅ Plugin - Traduction {} chargée!").format(locale))
                else:
                    print(self.tr("❌ Plugin - Échec chargement .qm"))
            else:
                print(self.tr("⚠️  Plugin - Fichier non trouvé: {}").format(translation_file))
                
        except Exception as e:
            print(self.tr("❌ Plugin - Erreur traductions: {}").format(e))

    def initGui(self):
        """Créer les entrées de menu et icônes de barre d'outils"""
        
        # Utiliser QCoreApplication.translate pour tous les textes
        plugin_name = QCoreApplication.translate("KATOverlap", "KAT Overlap Analyzer")
        whats_this = QCoreApplication.translate("KATOverlap", "Analyse des chevauchements géométriques entre polygones")
        status_tip = QCoreApplication.translate("KATOverlap", "Détecter et analyser les zones de chevauchement")
        tool_tip = QCoreApplication.translate("KATOverlap", "KAT Analyse – Overlap area (Multi-Types)")
        
        # Chemin vers l'icône
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        # Créer l'icône
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # Icône par défaut si le fichier n'existe pas
            icon = QIcon()
        
        # Créer l'action avec icône
        self.action = QAction(
            icon,
            plugin_name,
            self.iface.mainWindow()
        )
        
        # Définir les textes d'aide
        self.action.setWhatsThis(whats_this)
        self.action.setStatusTip(status_tip)
        self.action.setToolTip(tool_tip)
        
        # Connecter l'action à la méthode run
        self.action.triggered.connect(self.run)
        
        # Ajouter au menu Extensions > Vector
        self.iface.addPluginToVectorMenu("&KAT Tools", self.action)
        self.iface.addVectorToolBarIcon(self.action)

    def unload(self):
        """Retirer le plugin du menu et de la barre d'outils"""
        
        # Retirer du menu
        self.iface.removePluginVectorMenu("&KAT Tools", self.action)
        
        # Retirer de la barre d'outils
        self.iface.removeVectorToolBarIcon(self.action)
        
        # Désinstaller le traducteur
        if self.translator:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None
        
        # Fermer le dialogue s'il est ouvert
        if self.dialog:
            self.dialog.close()
            self.dialog = None
        
        # Nettoyer l'action
        self.action = None

    def run(self):
        # import relatif
        from .kat_overlap_ui import ModernKatOverlapUI
        if not self.dialog:
            self.dialog = ModernKatOverlapUI(self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        
        We implement this ourselves since we do not inherit QObject.
        """
        return QCoreApplication.translate('KATOverlap', message)