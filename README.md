# 🧩 KAT Analyse – Overlap area (Multi-Types) for QGIS

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/AzizT-dev/kat_overlap/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-%E2%89%A53.22-brightgreen.svg)](https://qgis.org)
[![Platform](https://img.shields.io/badge/platform-QGIS%20Plugin-yellow.svg)](https://plugins.qgis.org/)
[![Issues](https://img.shields.io/github/issues/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/issues)
[![Last Commit](https://img.shields.io/github/last-commit/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/commits/main)

---

**KAT Analyse – Overlap area** est un plugin QGIS de **contrôle qualité spatiale universel**.  
Il détecte, mesure et classe les **anomalies géométriques et topologiques** pour **tous les types de géométries vectorielles** : points, lignes et polygones.

L'outil s'adapte intelligemment au type de données analysées et est conçu pour répondre aux besoins des projets de cartographie, cadastre, gestion foncière, réseaux, aménagement du territoire et analyse environnementale.

---

## 🌟 Nouveautés v1.0 (Multi-Types)

### 🎯 Support multi-géométries
- ✅ **Points** : Détection de doublons et analyse de proximité
- ✅ **Lignes** : Vérification topologique (superpositions, croisements, connexions)
- ✅ **Polygones** : Détection de chevauchements (intra et inter-couches)

### 🧠 Adaptation intelligente
- Interface qui s'adapte automatiquement au type de géométrie
- Classification contextuelle de la gravité selon le type d'analyse
- Modes de détection spécialisés selon le contexte métier

### 🔧 Configuration par profil utilisateur
- **Mode strict** : Détection exhaustive (réseaux, routes, topographie)
- **Mode groupé** : Tolérance aux adjacences (parcelles, cadastre, zonage)

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

### Fonctionnalités avancées
- 🔹 **Classification automatique** selon la gravité (Faible → Critique)
- 🔹 **Détection robuste** via index spatial (R-tree)
- 🔹 **Rapport interactif** avec filtres par gravité et sélection
- 🔹 **Export flexible** : TXT, XLSX avec formatage conditionnel
- 🔹 **Couche temporaire stylisée** avec symbologie graduée par gravité
- 🔹 **Gestion automatique** des géométries invalides
- 🔹 **Support multi-CRS** avec reprojection dynamique (UTM, source, personnalisé)
- 🔹 **Threading optimisé** pour grandes volumétries
- 🔹 **Zoom interactif** sur les anomalies détectées

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
```

---

## 🧱 Structure du plugin

```
kat_overlap/
├── __init__.py
├── kat_overlap.py              # Point d'entrée
├── kat_overlap_core.py         # Logique métier (analyses)
├── kat_overlap_ui.py           # Interface utilisateur
├── metadata.txt                # Métadonnées QGIS
├── icon.png                    # Icône du plugin
├── i18n/                       # Traductions
│   ├── kat_overlap_fr.qm
│   ├── kat_overlap_en.qm
│   └── kat_overlap_es.qm
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

### Analyse de points (doublons)
1. **Mode** : Une seule couche
2. **Couche** : Sélectionner la couche de points
3. **Champ ID** : Choisir le champ identifiant
4. **Mode de détection** :
   - *Strict* : Compare tous les points (routes, réseaux)
   - *Groupé* : Compare uniquement au sein d'un même ID (parcelles)
5. **Proximité** : Définir la distance minimale (ex: 1.0 m)
6. **Lancer l'analyse**

### Analyse de lignes (topologie)
1. **Mode** : Une seule couche
2. **Couche** : Sélectionner la couche de lignes
3. **Tolérance topologique** : Définir le seuil (ex: 0.01 m)
4. **Lancer l'analyse**
5. **Résultats** : Doublons, croisements sans nœud, lignes non jointives

### Analyse de polygones (chevauchements)
1. **Mode** : Une seule couche ou Multi-couches
2. **Couche(s)** : Sélectionner la/les couche(s) polygonale(s)
3. **Surface minimale** : Définir le seuil (ex: 0.000001 m²)
4. **Lancer l'analyse**
5. **Résultats** : Chevauchements avec surface et gravité

### Analyse Point/Polygone (appartenance)
1. **Mode** : Multi-couches
2. **Sélectionner** : Couche de points + Couche de polygones
3. **Champs ID** : Définir l'ID pour CHAQUE couche
4. **Lancer l'analyse**
5. **Résultats** : Points internes vs points hors zone

---

## 📊 Interprétation des résultats

### Classification de gravité

| Gravité | Couleur | Points | Lignes | Polygones |
|---------|---------|--------|--------|-----------|
| 🔴 **Critique** | Rouge | Distance < 10% seuil | Superposition | Chevauchement > 50% |
| 🟠 **Élevée** | Orange | Distance < 30% seuil | Croisement sans nœud | Chevauchement > 20% |
| 🟡 **Modérée** | Jaune | Distance < 60% seuil | Ligne non jointive | Chevauchement > 5% |
| 🟢 **Faible** | Vert | Distance ≥ 60% seuil | - | Chevauchement < 5% |

### Types de résultats selon l'analyse

**Points (mode strict)** :
```
ID1          | ID2          | Distance (m) | Gravité
-------------|--------------|--------------|----------
Point_001    | Point_002    | 0.05         | Critique
Point_010    | Point_011    | 0.85         | Modérée
```

**Points (mode groupé)** :
```
ID Parcelle  | Point 1      | Point 2      | Distance (m) | Gravité
-------------|--------------|--------------|--------------|----------
28-097-001   | Sommet_A     | Sommet_A_dup | 0.0001       | Critique
→ Doublons DANS la même parcelle uniquement
→ Points communs entre parcelles adjacentes : IGNORÉS
```

**Lignes** :
```
ID1          | ID2          | Type croisement       | Gravité
-------------|--------------|----------------------|----------
Route_001    | Route_002    | Croisement sans nœud | Élevée
Route_005    | Route_005_cp | Doublon/Superposition| Critique
```

**Polygones** :
```
ID1          | ID2          | Surface (m²) | Gravité
-------------|--------------|--------------|----------
Parcelle_A   | Parcelle_B   | 125.458      | Élevée
Zone_01      | Zone_02      | 0.005        | Faible
```

---

## 🧮 Dépendances

| Librairie | Rôle | Installation |
|-----------|------|--------------|
| `openpyxl` | Export Excel (XLSX) | `pip install openpyxl` |
| `PyQt5` (inclus) | Interface utilisateur | Fourni avec QGIS |
| `qgis.core` / `qgis.gui` | API QGIS | Fourni avec QGIS |

**Configuration requise** :
- **QGIS minimum** : 3.22
- **QGIS recommandé** : 3.28 ou 3.34 LTR
- **Python** : ≥ 3.9

---

## 📊 Exemples d'application

| Contexte | Type de données | Objectif | Mode recommandé |
|----------|----------------|----------|-----------------|
| Cadastre | Points (sommets) | Détecter vrais doublons | Groupé par ID parcelle |
| Routes | Lignes | Valider topologie | Une couche, tolérance 0.01m |
| Réseaux | Points (équipements) | Détecter doublons | Strict, proximité 1m |
| Parcelles | Polygones | Identifier chevauchements | Une couche, surface 0.01m² |
| Échantillonnage | Point + Polygone | Vérifier appartenance | Multi-couches |
| SIG multi-sources | Tous types | Contrôle qualité complet | Plusieurs analyses |

---

## 📸 Captures d'écran

| Interface principale | Résultats Points | Résultats Lignes |
|---------------------|------------------|------------------|
| ![ui](docs/screenshots/ui.png) | ![points](docs/screenshots/points.png) | ![lines](docs/screenshots/lines.png) |

| Résultats Polygones | Export Excel | Couche temporaire |
|--------------------|--------------|-------------------|
| ![polygons](docs/screenshots/polygons.png) | ![excel](docs/screenshots/excel.png) | ![layer](docs/screenshots/layer.png) |

*(Ajouter vos captures dans `/docs/screenshots/`)*

---

## 🎯 Avantages compétitifs

### vs GRASS v.clean
✅ Interface intuitive  
✅ Pas de dépendance externe  
✅ Classification automatique  
✅ Support multi-types natif  

### vs Topology Checker
✅ Analyse inter-couches  
✅ Rapport exportable  
✅ Filtrage dynamique  
✅ Modes contextuels (strict/groupé)  

### vs Processing Algorithms
✅ Workflow intégré  
✅ Visualisation immédiate  
✅ Export formaté  
✅ Zoom interactif sur anomalies  

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
| **1.0.0** | 2025-11-03 | 🎉 **Version initiale Multi-Types**<br>✅ Support Points, Lignes, Polygones<br>✅ Modes strict et groupé pour points<br>✅ Analyse topologique des lignes<br>✅ Multi-couches avec ID distincts<br>✅ Classification contextuelle<br>✅ Export Excel robuste<br>✅ Documentation complète |

---

## 🗺️ Feuille de route

### ✅ Version 1.0 (Actuelle)
- [x] Support multi-types (Points, Lignes, Polygones)
- [x] Mode strict/groupé pour points
- [x] Analyse topologique lignes
- [x] Point/Polygone multi-couches
- [x] Export TXT/XLSX

### 🔄 Version 1.1 (Prévue Q1 2026)
- [ ] Compléter analyse Point/Ligne
- [ ] Compléter analyse Ligne/Polygone
- [ ] Préréglages par profil utilisateur
- [ ] Export multi-onglets Excel
- [ ] Correction automatique des doublons simples

### 🚀 Version 2.0 (Prévue Q2 2026)
- [ ] Mode batch (traiter plusieurs couches)
- [ ] Rapport PDF avec cartes
- [ ] Statistiques avancées
- [ ] API REST pour automatisation
- [ ] Intégration PostGIS

---

## 💬 Retours et contributions

Vous pouvez :
- 🐛 Signaler un bug via [GitHub Issues](https://github.com/AzizT-dev/kat_overlap/issues)
- 💡 Proposer des améliorations
- 🌍 Contribuer aux traductions (FR / EN / ES)
- 📖 Améliorer la documentation
- ⭐ Partager vos retours d'expérience

---

## 📚 Documentation complète

- 📘 [Guide utilisateur complet](docs/user_guide.pdf)
- 🎓 [Guide de configuration universelle](docs/universal_config_guide.md)
- 🔧 [Guide développeur](docs/developer_guide.md)
- 🐛 [FAQ & Troubleshooting](docs/faq.md)

---

## 🔖 Mots-clés (tags)

`qgis` · `gis` · `spatial` · `overlap` · `intersection` · `topology` · `quality-control` · `vector` · `geometry` · `points` · `lines` · `polygons` · `cadastre` · `networks` · `validation` · `multi-types` · `kat-explorer-gis`

---

## 🙏 Remerciements

Merci à la communauté QGIS pour l'API robuste et la documentation excellente.  
Merci aux testeurs beta pour leurs retours précieux sur les cas d'usage réels.

---

**⭐ Si ce plugin vous est utile, n'oubliez pas de mettre une étoile sur GitHub !**
