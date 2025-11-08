# 🧩 KAT Analyse – Overlap area (Multi-Types) for QGIS

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](https://github.com/AzizT-dev/kat_overlap/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-%E2%89%A53.22-brightgreen.svg)](https://qgis.org)
[![Platform](https://img.shields.io/badge/platform-QGIS%20Plugin-yellow.svg)](https://plugins.qgis.org/)
[![Issues](https://img.shields.io/github/issues/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/issues)
[![Last Commit](https://img.shields.io/github/last-commit/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/commits/main)

---

**KAT Analyse – Overlap area** est un plugin QGIS de **contrôle qualité spatiale universel** avec **correction automatique intégrée**.  
Il détecte, mesure, classe **et corrige** les **anomalies géométriques et topologiques** pour **tous les types de géométries vectorielles** : points, lignes et polygones.

L'outil s'adapte intelligemment au type de données analysées et est conçu pour répondre aux besoins des projets de cartographie, cadastre, gestion foncière, réseaux, aménagement du territoire et analyse environnementale.

---

## 🌟 Nouveautés v2.3 (Correction Automatique)

### 🔧 Système de correction automatique
- ✅ **Points** : Suppression automatique des doublons
- ✅ **Lignes** : Suppression des lignes problématiques
- ✅ **Polygones** : Réparation automatique via l'outil QGIS "Réparer les géométries"
- ✅ **Point/Polygone** : Mode interactif avec dialogue de choix (prévu v2.4)

### 🎨 Interface améliorée
- ✅ **Header cliquable** : Sélectionner/désélectionner toutes les lignes d'un clic
- ✅ **Bouton Zoom** : Zoom intelligent sur sélection simple ou multiple
- ✅ **Bouton Corriger** : Création automatique de couche corrigée
- ✅ **Colonne Action** : Choix Conserver/Supprimer pour chaque anomalie
- ✅ **Indicateur dynamique** : Affichage en temps réel du nombre de résultats sélectionnés
- ✅ **Filtres simplifiés** : Options de gravité plus claires et intuitives

### ⚡ Export optimisé
- ✅ **Export sélection** : Exporter uniquement les résultats sélectionnés (TXT/XLSX)
- ✅ **Export couche corrigée** : Sauvegarder directement la couche avec corrections appliquées
- ✅ **Clarification** : Distinction claire entre couche de résultats et couche corrigée

### 🐛 Corrections critiques
- ✅ Erreur `_apply_filters` corrigée
- ✅ Indicateur de résultats maintenant fonctionnel
- ✅ Pas de création de couches auxiliaires inutiles
- ✅ Noms de couches sans duplication

---

## 🚀 Fonctionnalités principales

### Analyse mono-couche
- 🔹 **Points** : Doublons et points trop proches avec distance exacte
- 🔹 **Lignes** : Superpositions, croisements sans nœud, extrémités non jointives
- 🔹 **Polygones** : Chevauchements avec surface et pourcentage

### Analyse multi-couches
- 🔹 **Point / Polygone** : Vérification d'appartenance (points internes vs hors zone)
- 🔹 **Polygone / Polygone** : Chevauchements inter-couches
- 🔹 **Support prévu** : Point/Ligne, Ligne/Polygone (structure prête)

### 🆕 Correction automatique (v2.3)
- 🔹 **Sélection interactive** : Marquer les anomalies à corriger avec "Supprimer"
- 🔹 **Création automatique** : Génération d'une couche corrigée en un clic
- 🔹 **Prévisualisation** : Voir les corrections avant de les appliquer
- 🔹 **Traçabilité** : Couche originale préservée, corrections dans nouvelle couche

### Fonctionnalités avancées
- 🔹 **Classification automatique** selon la gravité (Faible → Critique)
- 🔹 **Détection robuste** via index spatial (R-tree)
- 🔹 **Rapport interactif** avec filtres par gravité et sélection multiple
- 🔹 **Export flexible** : TXT, XLSX avec formatage conditionnel
- 🔹 **Couche temporaire stylisée** avec symbologie graduée par gravité
- 🔹 **Gestion automatique** des géométries invalides
- 🔹 **Support multi-CRS** avec reprojection dynamique (UTM, source, personnalisé)
- 🔹 **Threading optimisé** pour grandes volumétries
- 🔹 **Zoom interactif** sur une ou plusieurs anomalies

---

## 🎓 Profils d'utilisation

### 🛣️ Profil "Routes & Réseaux"
**Données** : Points de levés, lignes de réseaux  
**Mode** : Strict (détection exhaustive)  
**Usage** : Routes, réseaux électriques/eau, topographie, inventaires

**Configuration type** :
```
Mode : Une seule couche
Type : Points
Détection : Mode strict
Proximité : 1.0 m
Correction : Suppression des doublons marqués
```

### 🏘️ Profil "Parcelles & Cadastre"
**Données** : Sommets de parcelles, polygones fonciers  
**Mode** : Groupé (tolérance aux adjacences)  
**Usage** : Cadastre, certification foncière, zonage, délimitations

**Configuration type** :
```
Mode : Une seule couche
Type : Points (sommets)
Détection : Mode groupé par ID
Proximité : 0.001 m
→ Ignore les points communs entre parcelles adjacentes
→ Correction sélective des vrais doublons
```

### 🗺️ Profil "Cartographie générale"
**Données** : Données multi-sources  
**Mode** : Multi-couches  
**Usage** : Contrôle qualité, validation topologique, intégration de données

**Configuration type** :
```
Mode : Multi-couches
Types : Point + Polygone
→ Vérification d'appartenance des points aux zones
→ Correction interactive avec choix utilisateur
```

---

## 🧱 Architecture du plugin (v2.3)

```
kat_overlap/
├── __init__.py
├── kat_overlap.py              # Point d'entrée du plugin
├── metadata.txt                # Métadonnées QGIS
│
├── ui/
│   ├── __init__.py
│   └── overlap_dialog.py       # Interface principale (v2.3 - 2110 lignes)
│
├── core/
│   ├── __init__.py
│   ├── analysis_worker.py      # Worker pour traitement multi-thread
│   ├── geometry_analyzer.py    # Logique métier d'analyse des géométries
│   └── layer_manager.py        # Gestion et préparation des couches (v2.3)
│
├── utils/
│   ├── __init__.py
│   ├── exporters.py            # Export TXT/XLSX/CSV/JSON (v2.3)
│   ├── formatters.py           # Mise en forme des résultats
│   └── validators.py           # Validation des géométries
│
├── i18n/
│   ├── kat_overlap_en.qm       # Traductions compilées
│   ├── kat_overlap_es.qm
│   └── kat_overlap_fr.qm
│
└── docs/                       # Documentation
    ├── banner.png
    ├── screenshots/
    └── user_guide.pdf
```

---

## 📦 Installation

### 🟢 Méthode 1 — via le gestionnaire d'extensions QGIS
1. Ouvrir QGIS → **Extensions → Installer et gérer les extensions**
2. Rechercher **KAT Analyse** ou **KAT Overlap**
3. Cliquer sur **Installer**

### 🟣 Méthode 2 — Installation manuelle via GitHub
1. Télécharger ou cloner le dépôt :
   ```bash
   git clone https://github.com/AzizT-dev/kat_overlap.git
   ```

2. Zipper le dossier `kat_overlap/`

3. Dans QGIS :  
   **Extensions → Installer depuis un ZIP...**

4. Sélectionner le fichier ZIP et valider

5. Redémarrer QGIS

---

## ⚙️ Guide d'utilisation rapide

### Analyse de points avec correction automatique (v2.3)
1. **Mode** : Une seule couche
2. **Couche** : Sélectionner la couche de points
3. **Champ ID** : Choisir le champ identifiant
4. **Mode de détection** :
   - *Strict* : Compare tous les points (routes, réseaux)
   - *Groupé* : Compare uniquement au sein d'un même ID (parcelles)
5. **Proximité** : Définir la distance minimale (ex: 1.0 m)
6. **Lancer l'analyse**
7. **🆕 Dans les résultats** :
   - Cocher les lignes à corriger (ou cliquer sur ☐ dans l'en-tête)
   - Sélectionner "Supprimer" dans la colonne Action
   - Cliquer sur **🔧 Corriger**
   - → Une nouvelle couche `nom_couche_corrigé` est créée automatiquement

### Analyse de polygones avec réparation automatique (v2.3)
1. **Mode** : Une seule couche ou Multi-couches
2. **Couche(s)** : Sélectionner la/les couche(s) polygonale(s)
3. **Surface minimale** : Définir le seuil (ex: 0.000001 m²)
4. **Lancer l'analyse**
5. **🆕 Dans les résultats** :
   - Marquer les chevauchements à corriger avec "Supprimer"
   - Cliquer sur **🔧 Corriger**
   - → Utilise l'outil QGIS "Réparer les géométries"
   - → Crée une couche `nom_couche_corrigé` automatiquement

### 🆕 Utilisation de l'interface améliorée (v2.3)

#### Sélection rapide
- **Clic sur ☐ dans l'en-tête** → Sélectionne toutes les lignes
- **Clic sur ☑ dans l'en-tête** → Désélectionne toutes les lignes
- **Cocher manuellement** → Sélection individuelle

#### Zoom intelligent
- **Sélectionner une ligne** → Clic **🔍 Zoom** → Zoom sur cette anomalie
- **Sélectionner plusieurs lignes** → Clic **🔍 Zoom** → Zoom étendu englobant tout

#### Export optimisé
- **Cocher les lignes à exporter** → Clic **Enregistrer la sélection**
- → N'exporte que les lignes cochées (pas tout le tableau)

---

## 📊 Interprétation des résultats

### Classification de gravité

| Gravité | Couleur | Points | Lignes | Polygones |
|---------|---------|--------|--------|-----------|
| 🔴 **Critique** | Rouge | Distance < 10% seuil | Superposition | Chevauchement > 50% |
| 🟠 **Élevée** | Orange | Distance < 30% seuil | Croisement sans nœud | Chevauchement > 20% |
| 🟡 **Modérée** | Jaune | Distance < 60% seuil | Ligne non jointive | Chevauchement > 5% |
| 🟢 **Faible** | Vert | Distance ≥ 60% seuil | - | Chevauchement < 5% |

### 🆕 Colonne Action (v2.3)

Chaque ligne du tableau dispose d'une colonne "Action" avec deux choix :

| Option | Comportement | Usage |
|--------|--------------|-------|
| **Conserver** | Ne rien faire | Anomalie acceptée ou à traiter manuellement |
| **Supprimer** | Marquer pour correction | Active le bouton 🔧 Corriger |

**Workflow typique** :
1. Analyser les résultats
2. Filtrer par gravité (ex: "Critique")
3. Cocher les lignes pertinentes
4. Sélectionner "Supprimer" pour celles à corriger
5. Cliquer **🔧 Corriger**
6. Vérifier la nouvelle couche `_corrigé`

---

## 🧮 Dépendances

| Librairie | Rôle | Installation |
|-----------|------|--------------|
| `openpyxl` | Export Excel (XLSX) | `pip install openpyxl` |
| `PyQt5` (inclus) | Interface utilisateur | Fourni avec QGIS |
| `qgis.core` / `qgis.gui` | API QGIS | Fourni avec QGIS |
| `processing` (v2.3) | Corrections géométriques | Fourni avec QGIS |

**Configuration requise** :
- **QGIS minimum** : 3.22
- **QGIS recommandé** : 3.28 ou 3.34 LTR
- **Python** : ≥ 3.9

---

## 📊 Exemples d'application

| Contexte | Type de données | Objectif | Mode recommandé | 🆕 Correction |
|----------|----------------|----------|-----------------|---------------|
| Cadastre | Points (sommets) | Détecter vrais doublons | Groupé par ID parcelle | Auto |
| Routes | Lignes | Valider topologie | Une couche, tolérance 0.01m | Auto |
| Réseaux | Points (équipements) | Détecter doublons | Strict, proximité 1m | Auto |
| Parcelles | Polygones | Identifier chevauchements | Une couche, surface 0.01m² | Auto QGIS |
| Échantillonnage | Point + Polygone | Vérifier appartenance | Multi-couches | Interactive |
| SIG multi-sources | Tous types | Contrôle qualité complet | Plusieurs analyses | Mixte |

---

## 📸 Captures d'écran

### Interface v2.3
| Panneau principal | Filtres et actions | Correction automatique |
|-------------------|-------------------|------------------------|
| ![ui_v23](docs/screenshots/ui_v23.png) | ![filters](docs/screenshots/filters_v23.png) | ![correction](docs/screenshots/correction.png) |

### Fonctionnalités
| Header cliquable | Zoom multi-sélection | Couche corrigée |
|-----------------|---------------------|-----------------|
| ![header](docs/screenshots/header_click.png) | ![zoom](docs/screenshots/zoom_multi.png) | ![corrected](docs/screenshots/corrected_layer.png) |

### Types d'analyses
| Résultats Points | Résultats Lignes | Résultats Polygones |
|------------------|------------------|---------------------|
| ![points](docs/screenshots/points.png) | ![lines](docs/screenshots/lines.png) | ![polygons](docs/screenshots/polygons.png) |

*(Ajouter vos captures dans `/docs/screenshots/`)*

---

## 🎯 Avantages compétitifs

### vs GRASS v.clean
✅ Interface intuitive  
✅ Pas de dépendance externe  
✅ Classification automatique  
✅ Support multi-types natif  
✅ **🆕 Correction en un clic**

### vs Topology Checker
✅ Analyse inter-couches  
✅ Rapport exportable  
✅ Filtrage dynamique  
✅ Modes contextuels (strict/groupé)  
✅ **🆕 Workflow correction intégré**

### vs Processing Algorithms
✅ Workflow intégré  
✅ Visualisation immédiate  
✅ Export formaté  
✅ Zoom interactif sur anomalies  
✅ **🆕 Sélection intelligente et correction**

---

## 🧑‍💻 Auteur

**Aziz T. — KAT Explorer GIS**  
🌐 [https://github.com/AzizT-dev](https://github.com/AzizT-dev)  
📧 aziz.explorer@gmail.com

---

## ⚖️ Licence

Ce projet est distribué sous la **licence GNU General Public License v3.0 (GPL-3.0)**.  
Vous êtes libre d'utiliser, modifier et redistribuer le code tant que la même licence est conservée.

📄 Voir le fichier [`LICENSE`](./LICENSE) pour le texte complet.

---

## 🧾 Journal des versions

| Version | Date | Changements majeurs |
|---------|------|---------------------|
| **2.3.0** | 2025-11-08 | 🔧 **Correction automatique**<br>✅ Système de correction intégré<br>✅ Interface améliorée (header cliquable, boutons Zoom/Corriger)<br>✅ Colonne Action avec choix Conserver/Supprimer<br>✅ Export sélection uniquement<br>✅ Filtres simplifiés<br>✅ 4 bugs critiques corrigés<br>✅ 8 nouvelles fonctionnalités |
| **2.2.0** | 2025-11-08 | 🐛 **Corrections critiques**<br>✅ Nom de couche sans duplication<br>✅ Pas de couches auxiliaires créées<br>✅ Indicateur de résultats fonctionnel |
| **2.1.0** | 2025-11-05 | ⚡ **Optimisations**<br>✅ Performance améliorée<br>✅ Gestion mémoire optimisée<br>✅ Support géométries invalides |
| **2.0.0** | 2025-11-04 | 🎨 **Refactorisation majeure**<br>✅ Architecture modulaire<br>✅ Threading optimisé<br>✅ Export multi-formats |
| **1.0.0** | 2025-11-03 | 🎉 **Version initiale Multi-Types**<br>✅ Support Points, Lignes, Polygones<br>✅ Modes strict et groupé pour points<br>✅ Analyse topologique des lignes<br>✅ Multi-couches avec ID distincts<br>✅ Classification contextuelle<br>✅ Export Excel robuste |

---

## 🗺️ Feuille de route

### ✅ Version 2.3 (Actuelle - Novembre 2025)
- [x] Système de correction automatique
- [x] Header cliquable
- [x] Boutons Zoom et Corriger
- [x] Colonne Action interactive
- [x] Export sélection
- [x] Interface améliorée

### 🔄 Version 2.4 (Prévue Décembre 2025)
- [ ] Dialogue interactif pour Point/Polygone
- [ ] Historique des corrections
- [ ] Annulation/Rétablissement
- [ ] Prévisualisation avant correction
- [ ] Export rapport avec cartes

### 🚀 Version 3.0 (Prévue Q1 2026)
- [ ] Mode batch (traiter plusieurs couches)
- [ ] Correction avancée avec snapping
- [ ] Statistiques de qualité globales
- [ ] API REST pour automatisation
- [ ] Intégration PostGIS
- [ ] Rapport PDF avec cartes intégrées

---

## 💬 Retours et contributions

Vous pouvez :
- 🐛 Signaler un bug via [GitHub Issues](https://github.com/AzizT-dev/kat_overlap/issues)
- 💡 Proposer des améliorations
- 🌍 Contribuer aux traductions (FR / EN / ES)
- 📖 Améliorer la documentation
- ⭐ Partager vos retours d'expérience
- 🔧 Soumettre des Pull Requests

**Processus de contribution** :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📚 Documentation complète

- 📘 [Guide utilisateur complet](docs/user_guide.pdf)
- 🎓 [Guide de configuration universelle](docs/universal_config_guide.md)
- 🔧 [Guide développeur](docs/developer_guide.md)
- 🐛 [FAQ & Troubleshooting](docs/faq.md)
- 🆕 [Guide de correction automatique v2.3](docs/correction_guide.md)
- 🆕 [Exemples de workflow](docs/workflow_examples.md)

---

## 🔖 Mots-clés (tags)

`qgis` · `gis` · `spatial` · `overlap` · `intersection` · `topology` · `quality-control` · `vector` · `geometry` · `points` · `lines` · `polygons` · `cadastre` · `networks` · `validation` · `multi-types` · `correction` · `automation` · `data-quality` · `kat-explorer-gis`

---

## 🙏 Remerciements

Merci à la communauté QGIS pour l'API robuste et la documentation excellente.  
Merci aux testeurs beta pour leurs retours précieux sur les cas d'usage réels.  
Merci aux utilisateurs qui ont signalé les bugs et suggéré les améliorations de la v2.3.

---

## 📊 Statistiques du projet

![GitHub stars](https://img.shields.io/github/stars/AzizT-dev/kat_overlap?style=social)
![GitHub forks](https://img.shields.io/github/forks/AzizT-dev/kat_overlap?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/AzizT-dev/kat_overlap?style=social)

![Code size](https://img.shields.io/github/languages/code-size/AzizT-dev/kat_overlap)
![Lines of code](https://img.shields.io/tokei/lines/github/AzizT-dev/kat_overlap)

---

**⭐ Si ce plugin vous est utile, n'oubliez pas de mettre une étoile sur GitHub !**

**🔧 Nouveau dans la v2.3 ? Testez la correction automatique et partagez vos retours !**

---

<div align="center">
  
### 🚀 Développé avec ❤️ par KAT Explorer GIS
  
</div>
