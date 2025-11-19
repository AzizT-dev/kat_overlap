# 🧩 KAT Analyse – Overlap Area (Multi-Types) for QGIS

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/AzizT-dev/kat_overlap/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-%E2%89%A53.22-brightgreen.svg)](https://qgis.org)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-brightgreen.svg)](https://www.python.org/dev/peps/pep-0008/)

---

**KAT Analyse – Overlap Area** est un plugin QGIS universel de **contrôle qualité géométrique et topologique** avec **fusion multi-couches intégrée**.

Il détecte, mesure, classe et corrige les anomalies pour **tous les types de géométries vectorielles** : **points**, **lignes** et **polygones**, aussi bien en **mode mono-couche** qu'en **mode multi-couches** (jusqu'à 4 couches).

L'outil s'adapte aux besoins de : **cadastre**, **réseaux**, **cartographie**, **topographie**, **gestion foncière** et **analyse environnementale**.

---

## 🌟 Points forts

✨ **Analyse multi-types native**  
- Points (doublons, proximité)
- Lignes (topologie, intersections)
- Polygones (chevauchements, auto-intersections)
- **Point + Polygone** (appartenance / containment inter-couches)

🔄 **Fusion multi-couches automatique**  
- Jusqu'à 4 couches du même type fusionnées automatiquement
- Support : Point-Point, Ligne-Ligne, Polygone-Polygone
- Champ `__source_layer_id` pour traçabilité complète
- Analyse unique sur données fusionnées

🎨 **Interface intuitive et ergonomique**  
- Sélection rapide (header cliquable)
- Zoom interactif sur anomalies
- Filtrage dynamique par gravité
- Export sélection uniquement

🔧 **Correction intégrée**  
- Suppression intelligente des doublons
- Réparation géométrique QGIS
- Traçabilité complète des modifications

📊 **Classification intelligente**  
- Profils métier contextuels (Cadastre, BTP, Topographie, Hydrologie)
- Calculs de surface et ratio
- Mesures de proximité exactes

🚀 **Performance optimisée**  
- Index spatial R-tree
- Threading pour grandes volumétries
- Gestion mémoire efficace

---

## 📦 Installation

### Méthode 1 : Via le gestionnaire QGIS (recommandé)
```
Extensions → Installer et gérer les extensions
↓
Rechercher "KAT Overlap"
↓
Installer
↓
Redémarrer QGIS
```

### Méthode 2 : Installation manuelle ⚠️
```bash

> **Remarque :** Le ZIP téléchargé directement depuis GitHub (`kat_overlap-main.zip`) **ne peut pas** être installé tel quel dans QGIS. Il faut le préparer correctement.

1. **Télécharger le ZIP depuis GitHub**  
   - Cliquez sur **Code → Download ZIP** pour obtenir `kat_overlap-main.zip`.

2. **Préparer le ZIP pour QGIS**  
   - Décompressez `kat_overlap-main.zip`. Cela crée un dossier `kat_overlap-main` contenant **un second dossier `kat_overlap-main`** avec tous les fichiers du plugin.  
   - Renommez ce second dossier `kat_overlap-main` en `kat_overlap`.  
   - Recompressez **uniquement ce dossier** en `kat_overlap.zip`.

3. **Installer dans QGIS**  
   - Ouvrez QGIS → **Extensions → Installer depuis un ZIP**.  
   - Sélectionnez le fichier `kat_overlap.zip` préparé.

✅ Le plugin devrait maintenant apparaître dans la liste des extensions installées.

```

### Prérequis
- **QGIS** ≥ 3.22 (recommandé 3.28 ou 3.34 LTR)
- **Python** ≥ 3.9
- **openpyxl** : `pip install openpyxl` (optionnel, pour export Excel)

---

## 🚀 Démarrage rapide

### Exemple 1 : Détecter doublons dans une couche de points
```
1. Ouvrir KAT Analyse (menu Extensions)
2. Sélectionner votre couche de points
3. Choisir le champ ID
4. Définir proximité : 0.5 m
5. Cliquer "▶️ Lancer l'analyse"
6. Dans les résultats : cocher les doublons à supprimer
7. Cliquer "🛠 Corriger" → nouvelle couche créée automatiquement
```

### Exemple 2 : Identifier chevauchements polygones
```
1. Sélectionner votre couche polygone
2. Mode : "Une seule couche"
3. Surface minimale : 0.01 m²
4. Lancer l'analyse
5. Filtrer par gravité "Critique"
6. Export des résultats
```

### Exemple 3 : Fusionner 4 couches de parcelles
```
1. Sélectionner 4 couches polygones (Parcelle_2020, 2021, 2022, 2023)
2. Même structure tabulaire ? → Oui ✅
3. Lancer l'analyse
4. Plugin fusionne automatiquement
5. Détecte anomalies dans les 4 couches
6. Résultats avec __source_layer_id (identifie la source)
```

---

## 📂 Structure du projet

```
📁 kat_overlap/
├── 📄 icon.png                    # Icône du plugin (32×32)
├── 📄 metadata.txt                # Métadonnées QGIS
├── 📄 README.md                   # Documentation
├── 📄 __init__.py                 # Initialisation du plugin
├── 📜 kat_overlap.py              # Point d'entrée principal
├── 🎨 kat_overlap_ui.py           # Interface utilisateur moderne
│
├── 📁 core/                       # Cœur fonctionnel
│   ├── __init__.py
│   ├── 📊 analysis_task.py        # Moteur d'analyse (QGIS Task)
│   ├── 🏷️  classification.py      # Profils métier + classification
│   ├── 🛠️  correction_manager.py  # Gestion des corrections
│   ├── 🔧 layer_helpers.py        # Aide à la sélection des couches
│   ├── 🏗️  layer_manager.py       # Gestion + fusion couches
│   ├── 📋 results_table_manager.py # Gestion du tableau de résultats
│   ├── 🗑️  temp_layer_manager.py  # Gestion des couches temporaires
│   ├── 📤 ui_export_manager.py    # Gestion de l'export depuis l'UI
│   └── 👁️  visualization.py       # Visualisation des résultats
│
├── 📁 utils/                      # Utilitaires
│   ├── __init__.py
│   ├── 📤 file_utils.py           # Export CSV/TXT
│   ├── 🔍 id_resolver.py          # Résolution des identifiants
│   ├── 📊 result_exporter.py      # Export GPKG/SHP/XLSX/GeoJSON
│   └── 🎯 result_layer_utils.py   # Utilitaires couches résultats
│
├── 📁 ui/                         # Interface utilisateur
│   ├── __init__.py
│   └── 🎨 theme.py                # Gestion des thèmes UI
│
└── 📁 i18n/                       # Fichiers de traduction
    ├── kat_overlap_fr.qm          # Français compilé
    ├── kat_overlap_en.qm          # Anglais compilé  
    ├── kat_overlap_es.qm          # Espagnol compilé
    └── kat_overlap_ar.qm          # Arabe compilé
```

## 🧬 Architecture interne

### Flux de traitement
```
UI (kat_overlap_ui.py)
    ↓
run_analysis() → get_selected_layers()
    ↓
[NEW] Fusion multi-couches si N couches du même type
    ↓
AnalysisTask (analysis_task.py)
    ├─ _analyze_self_overlaps()       # Points / Lignes / Polygones mono-couche
    ├─ _analyze_inter_layer_overlaps()  # Multi-couches (Poly+Poly, Point+Point, etc)
    └─ _analyze_points_in_polygons()   # Point + Polygone
    ↓
classification.py → PresetManager
    ├─ classify_point_proximity()      # Gravité points
    ├─ classify_polygon_overlap()      # Gravité polygones
    └─ classify_line_topology()        # Gravité lignes
    ↓
Résultats → Tableau + Couche résultats
    ↓
[NEW] Correction automatique via layer_manager.py
    ├─ Points : delete features
    ├─ Lignes : delete features
    └─ Polygones : QGIS "Repair geometries"
```

### Fusion multi-couches
```
N couches sélectionnées (même type)
    ↓
get_selected_layers()
    ↓
Grouper par type géométrique
    ↓
check_layers_compatibility() → Même structure tabulaire?
    ↓
merge_layers_to_temp()
    ├─ Créer couche mémoire
    ├─ Copier tous les attributs
    ├─ Ajouter champ __source_layer_id (traçabilité)
    └─ Fusionner features
    ↓
Traitement comme 1 fichier interne
    ↓
Résultats avec identification source
```

---

## 🔄 Modes d'analyse disponibles

### Mode INTERNE (1 couche)

| Type | Analyse | Détection |
|------|---------|-----------|
| **Points** | Doublons | Distance exacte |
| **Points** | Proximité | Distance < seuil |
| **Lignes** | Topologie | Intersections, extrémités |
| **Polygones** | Chevauchements | Surface + ratio |

### Mode INTER-COUCHES (2+ couches - v1.0)

| Types | Analyse | Détection | Couches |
|-------|---------|-----------|---------|
| **Point + Polygone** | Appartenance / Containment | Points internes vs externes | 2+ couches (1 point + 1+ poly) |
| **Polygone + Polygone** | Recouvrement inter-couches | Surface + ratio | Jusqu'à 4 polygones |
| **Point + Point** | Doublons inter-couches | Distance exacte/proximité | Jusqu'à 4 points |
| **Ligne + Ligne** | Topologie inter-couches | Intersections, croisements | Jusqu'à 4 lignes |

---

## 🔗 Fusion Multi-Couches

### Qu'est-ce que c'est ?

La fusion multi-couches permet de **traiter automatiquement jusqu'à 4 couches du même type** comme une seule couche logique, sans refactorisation du moteur d'analyse.

### Cas d'usage typiques

```
Sélectionner :
├─ Parcelle_Année2020
├─ Parcelle_Année2021
├─ Parcelle_Année2022
└─ Parcelle_Année2023

↓ Fusion automatique en "merged_polygon_4"

Résultats avec __source_layer_id :
├─ Anomalie 1 : Source = Parcelle_Année2020
├─ Anomalie 2 : Source = Parcelle_Année2021
├─ Anomalie 3 : Source = Parcelle_Année2022
└─ Anomalie 4 : Source = Parcelle_Année2023
```

### Fonctionnement technique

| Étape | Action |
|-------|--------|
| 1️⃣ **Sélection** | Utilisateur coche 4 couches du même type |
| 2️⃣ **Vérification** | Plugin vérifie compatibilité (structure tabulaire) |
| 3️⃣ **Fusion** | Création couche temp `merged_[type]_4` en mémoire |
| 4️⃣ **Traçabilité** | Ajout champ `__source_layer_id` = layer_id original |
| 5️⃣ **Analyse** | Traitement comme 1 fichier interne |
| 6️⃣ **Nettoyage** | Suppression couche temp à la fermeture |

### Champ `__source_layer_id`

Chaque entité fusionnée conserve l'ID de sa couche source :

```python
# Structure après fusion
merged_polygon_4 :
  - Feature 1: attributs_origine + __source_layer_id = "layer_uuid_2020"
  - Feature 2: attributs_origine + __source_layer_id = "layer_uuid_2021"
  - Feature 3: attributs_origine + __source_layer_id = "layer_uuid_2020"
  - Feature 4: attributs_origine + __source_layer_id = "layer_uuid_2022"

Résultat :
  - Anomalie détectée entre Feature 1 et 3
  - Affichage : "Overlapping features from same source (2020)"
  - __source_layer_id permet identification / tri
```

### Limitations & Fallback

| Situation | Comportement |
|-----------|--------------|
| **2-4 couches** | ✅ Fusion automatique |
| **1 couche** | ✅ Traitement direct (pas de fusion) |
| **5+ couches** | ❌ Limitation : max 4 acceptées |
| **Structures différentes** | ⚠️ Fallback : utilise 1ère couche |
| **Types géométriques mixtes** | ❌ Rejet : seulement même type |

### Prérequis pour fusion

✅ **Même type géométrique** : Tous Point OU tous Ligne OU tous Polygone  
✅ **Même structure** : Même champs (noms + types) dans tous les fichiers  
✅ **Géométries valides** : Évite les géométries vides/nulles

---

## 📊 Classification de gravité

Chaque anomalie est classée selon le profil métier sélectionné :

| Gravité | Sévérité | Points | Lignes | Polygones |
|---------|----------|--------|--------|-----------|
| 🔴 **Critique** | Majeure | Distance < 5% seuil | Chevauchement | Recouvrement > 50% |
| 🟠 **Élevée** | Significative | Distance < 15% seuil | Croisement non nœud | Recouvrement > 20% |
| 🟡 **Modérée** | Mineure | Distance < 50% seuil | Ligne cassée | Recouvrement > 5% |
| 🟢 **Faible** | Acceptable | Distance ≥ 50% seuil | Topologie ok | Recouvrement < 5% |

---

## 🎓 Profils métier

### 1️⃣ Cadastre & Foncier
```
Contexte: Parcelles + sommets
Mode: Points groupés par ID parcelle
Tolérance: 0.001 m (1 mm)
Profil: Foncier/Cadastre (±2m GPS)
Objectif: Détecter vrais doublons, ignorer points partagés
```

### 2️⃣ BTP & Routes
```
Contexte: Levés GPS, réseaux
Mode: Points strict
Tolérance: 0.5 m
Profil: BTP/Construction (±0.05m RTK)
Objectif: Contrôle qualité implantation
```

### 3️⃣ Topographie
```
Contexte: Station totale, MNT
Mode: Lignes + points
Tolérance: 0.01 m
Profil: Topographie (±0.01m Station)
Objectif: Validations topologiques
```

### 4️⃣ Hydrologie
```
Contexte: Bassins versants, réseaux
Mode: Polygones multi-couches
Tolérance: 10 m
Profil: Hydrologie (±10m SIG)
Objectif: Chevauchements acceptables?
```

---

## 📤 Options d'export

### Format CSV/TXT
```python
# Exporte uniquement lignes cochées
export_checked_table_rows_to_csv(
    table=results_table,
    csv_path="anomalies.csv",
    delimiter=";"
)
```

### Format GPKG/SHP/GeoJSON
```python
# Exporte couche résultats complète
export_layer_to_file(
    layer=result_layer,
    out_path="results.gpkg",
    driver_name="GPKG"
)
```

### Format XLSX (Excel)
```python
# Exporte attributs uniquement (pas géométrie)
export_layer_to_xlsx(
    layer=result_layer,
    xlsx_path="report.xlsx"
)
```

---

## 🧪 Tests & Validation

### Test 1 : Analyse mono-couche (1 polygone)
```
✓ Sélectionner 1 couche polygone
✓ Lancer analyse
✓ Résultats contiennent auto-chevauchements
```

### Test 2 : Fusion 2-4 couches
```
✓ Sélectionner 4 couches polygones (même structure)
✓ Lancer analyse
✓ Log : "✅ Fusion polygon: X entités (4 couches)"
✓ Résultats avec __source_layer_id
```

### Test 3 : Compatibilité
```
✓ Sélectionner 2 polygones (structures différentes)
✓ Lancer analyse
✓ Log : "❌ Incompatibilité polygon: noms de champs différents"
✓ Fallback : traitement avec 1ère couche uniquement
```

### Test 4 : Nettoyage à la fermeture
```
✓ Lancer analyse 4 couches
✓ Fermer le plugin
✓ Vérifier : couches "merged_*" supprimées de QGIS
```

---

## 🐛 Débogage & Troubleshooting

### Problème : "Impossible de créer couche temporaire"
```
Cause: CRS invalide ou type géométrique non supporté
Solution:
1. Vérifier CRS de la couche
2. Vérifier type géométrique (Point/Line/Polygon)
3. Vérifier qu'aucune couche n'a structure incompatible
```

### Problème : "Aucune ligne cochée à exporter"
```
Cause: Aucune ligne n'est cochée dans le tableau
Solution:
1. Cliquer sur ☐ dans l'en-tête pour cocher tout
2. Ou cocher manuellement les lignes
3. Relancer l'export
```

### Problème : Couches temporaires non supprimées
```
Cause: closeEvent() non appelé correctement
Solution:
1. Fermer le plugin via l'interface
2. Vérifier pas de crash Python
3. Nettoyer manuellement via QGIS
```

### Problème : Fusion échoue avec "Incompatibilité"
```
Cause: Couches ont des champs différents
Solution:
1. Vérifier layer.fields().names() identique
2. Vérifier types de champs identiques
3. Ajouter champs manquants aux couches
4. Relancer analyse
```

---

## 🧾 Dépendances

| Librairie | Rôle | Installation | Requis |
|-----------|------|--------------|--------|
| `qgis.core` | API QGIS | Fourni | ✅ Oui |
| `qgis.gui` | Interface QGIS | Fourni | ✅ Oui |
| `PyQt5` | GUI Framework | Fourni | ✅ Oui |
| `openpyxl` | Export Excel | `pip install openpyxl` | ❌ Non |
| `processing` | Réparation géométries | Fourni | ✅ Oui |

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
| **1.0.0** | 2025-11-18 | 🎉 **Version initiale**<br>✅ Support Points, Lignes, Polygones<br>✅ Modes strict et groupé pour points<br>✅ Analyse topologique des lignes<br>✅ Multi-couches avec ID distincts<br>✅ Classification contextuelle<br>✅ Export Excel robuste<br>✅ **Fusion multi-couches (NEW)**<br>✅ **Correction intégrée (NEW)**<br>✅ **Interface moderne (NEW)** |

---

## 💬 Retours et contributions

Vous pouvez :
- 🐛 Signaler un bug via [GitHub Issues](https://github.com/AzizT-dev/kat_overlap/issues)
- 💡 Proposer des améliorations
- 🌍 Contribuer aux traductions (FR / EN / ES / AR)
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

- 📘 [Guide utilisateur](docs/user_guide.md)
- 🎓 [Guide de configuration](docs/config_guide.md)
- 🔧 [Guide développeur](docs/developer_guide.md)
- 🐛 [FAQ & Troubleshooting](docs/faq.md)

---

## 🙏 Remerciements

Merci à la communauté QGIS pour l'API robuste et la documentation excellente.  
Merci aux testeurs beta pour leurs retours précieux.  
Merci aux utilisateurs pour leurs suggestions d'amélioration.

---

## 📊 Statistiques du projet

![GitHub stars](https://img.shields.io/github/stars/AzizT-dev/kat_overlap?style=social)
![GitHub forks](https://img.shields.io/github/forks/AzizT-dev/kat_overlap?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/AzizT-dev/kat_overlap?style=social)

---

**⭐ Si ce plugin vous est utile, n'oubliez pas de mettre une étoile sur GitHub !**

---

<div align="center">
  
### Développé par KAT Explorer GIS

**v1.0.0 - Novembre 2025**

</div>
