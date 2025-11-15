# 🧩 KAT Analyse – Overlap Area (Multi-Types) for QGIS

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](https://github.com/AzizT-dev/kat_overlap/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-%E2%89%A53.22-brightgreen.svg)](https://qgis.org)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-brightgreen.svg)](https://www.python.org/dev/peps/pep-0008/)

---

**KAT Analyse – Overlap Area** est un plugin QGIS universel de **contrôle qualité géométrique** avec **correction automatique intégrée**.

Il détecte, mesure, classe **et corrige** les anomalies **topologiques et géométriques** pour **tous les types de géométries vectorielles** : **points**, **lignes** et **polygones**.

L'outil s'adapte aux besoins de : **cadastre**, **réseaux**, **cartographie**, **topographie**, **gestion foncière** et **analyse environnementale**.

---

## 🌟 Points forts

✨ **Analyse multi-types native**  
- Points (doublons, proximité)
- Lignes (topologie, intersections)
- Polygones (chevauchements, auto-intersections)

🔧 **Correction automatique intégrée (v2.3)**  
- Suppression intelligente des doublons
- Réparation géométrique QGIS
- Traçabilité complète des modifications

🎨 **Interface intuitive et ergonomique**  
- Sélection rapide (header cliquable)
- Zoom interactif sur anomalies
- Filtrage dynamique par gravité
- Export sélection uniquement

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

### Méthode 2 : Installation manuelle
```bash
# 1. Cloner le dépôt
git clone https://github.com/AzizT-dev/kat_overlap.git

# 2. Zipper le dossier
zip -r kat_overlap.zip kat_overlap/

# 3. Dans QGIS :
# Extensions → Installer depuis un ZIP → Sélectionner kat_overlap.zip
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
7. Cliquer "🔧 Corriger" → nouvelle couche créée automatiquement
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

### Exemple 3 : Valider topologie de lignes
```
1. Sélectionner la couche lignes
2. Mode : "Une seule couche"
3. Tolérance : 0.1 m
4. Analyse lance automatiquement
5. Zoom sur les intersections détectées
```

---

## 📂 Structure du projet

```
kat_overlap/
├── 📄 icon.png                    # Icône du plugin (32×32)
├── 📄 metadata.txt                # Métadonnées QGIS
├── 📄 README.md                   # Cette documentation
├── 📄 __init__.py                 # Initialisation
├── 📜 kat_overlap.py              # Point d'entrée principal
├── 🎨 kat_overlap_ui.py           # Interface utilisateur (2110+ lignes)
│
├── 📁 core/
│   ├── __init__.py
│   ├── 📊 analysis_task.py        # Moteur d'analyse (QGIS Task)
│   ├── 🏷️  classification.py      # Profils métier + classification
│   └── 🏗️  layer_manager.py       # Gestion + fusion couches (v2.3)
│
├── 📁 utils/
│   ├── __init__.py
│   ├── 📤 file_utils.py           # Export CSV/TXT
│   └── 📊 result_exporter.py      # Export GPKG/SHP/XLSX/GeoJSON
│
└── 📁 i18n/
    ├── kat_overlap_fr.qm          # Français compilé
    ├── kat_overlap_fr.ts          # Français source
    ├── kat_overlap_en.qm          # Anglais compilé
    ├── kat_overlap_en.ts          # Anglais source
    ├── kat_overlap_es.qm          # Espagnol compilé
    └── kat_overlap_es.ts          # Espagnol source
```

---

## 🧬 Architecture interne

### Flux de traitement
```
UI (kat_overlap_ui.py)
    ↓
run_analysis() → get_selected_layers()
    ↓
[NOUVEAU v2.3] Fusion multi-couches si N couches du même type
    ↓
AnalysisTask (analysis_task.py)
    ├─ _analyze_self_overlaps()       # Points / Lignes / Polygones
    ├─ _analyze_inter_layer_overlaps()  # Multi-couches
    └─ _analyze_points_in_polygons()   # Point/Polygone
    ↓
classification.py → PresetManager
    ├─ classify_point_proximity()      # Gravité points
    ├─ classify_polygon_overlap()      # Gravité polygones
    └─ classify_line_topology()        # Gravité lignes
    ↓
Résultats → Tableau + Couche résultats
    ↓
[NOUVEAU v2.3] Correction automatique via layer_manager.py
    ├─ Points : delete features
    ├─ Lignes : delete features
    └─ Polygones : QGIS "Repair geometries"
```

### Fusion multi-couches (v2.3)
```
N couches sélectionnées
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

### Mode INTER-COUCHES (2+ couches)

| Types | Analyse | Détection |
|-------|---------|-----------|
| **Poly + Poly** | Recouvrement | Surface + ratio |
| **Point + Poly** | Appartenance | Containment |
| **Point + Ligne** | Proximité | Distance (v2.4) |
| **Ligne + Poly** | Intersection | Topologie (v2.4) |

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

## 🎯 Profils métier

### 1️⃣ Cadastre & Foncier
```
Contexte: Parcelles + sommets
Mode: Points groupés par ID parcelle
Tolérance: 0.001 m (1 mm)
Profil: Foncier/Cadastre (±2m GPS)
Objectif: Détecter vrais doublons, ignorer points partagés
Correction: Suppression points en doublon
```

### 2️⃣ BTP & Routes
```
Contexte: Levés GPS, réseaux
Mode: Points strict
Tolérance: 0.5 m
Profil: BTP/Construction (±0.05m RTK)
Objectif: Contrôle qualité implantation
Correction: Fusion ou suppression automatique
```

### 3️⃣ Topographie
```
Contexte: Station totale, MNT
Mode: Lignes + points
Tolérance: 0.01 m
Profil: Topographie (±0.01m Station)
Objectif: Validations topologiques
Correction: Réparation QGIS
```

### 4️⃣ Hydrologie
```
Contexte: Bassins versants, réseaux
Mode: Polygones multi-couches
Tolérance: 10 m
Profil: Hydrologie (±10m SIG)
Objectif: Chevauchements acceptables?
Correction: Décision interactive
```

---

## 🔧 Nouvelles fonctionnalités v2.3

### ✨ Correction automatique
- ✅ Système de correction intégré en 1 clic
- ✅ Colonne "Action" : Conserver / Supprimer
- ✅ Génération automatique couche corrigée
- ✅ Traçabilité complète (couche source préservée)

### 🎨 Interface améliorée
- ✅ **Header cliquable** : Sélectionner/désélectionner tout
- ✅ **Bouton Zoom** : Zoom intelligent sur sélection
- ✅ **Bouton Corriger** : Lance correction automatique
- ✅ **Filtres simplifiés** : Options gravité claires
- ✅ **Export sélection** : Exporte uniquement lignes cochées

### 🚀 Fusion multi-couches (automatique)
- ✅ Détection N couches du même type
- ✅ Vérification compatibilité (structure tabulaire)
- ✅ Fusion transparente en couche temp
- ✅ Champ `__source_layer_id` pour traçabilité
- ✅ Nettoyage automatique à la fermeture

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

### Test 1 : Régression (1 couche)
```
✓ Sélectionner 1 polygone
✓ Lancer analyse
✓ Résultats attendus = avant v2.3
```

### Test 2 : Fusion 2-4 couches
```
✓ Sélectionner 4 polygones (même structure)
✓ Lancer analyse
✓ Log : "✅ Fusion polygon: X entités (4 couches)"
✓ Résultats avec __source_layer_id
```

### Test 3 : Correction automatique
```
✓ Analyser résultats
✓ Cocher lignes à corriger
✓ Sélectionner "Supprimer" dans Action
✓ Cliquer "🔧 Corriger"
✓ Nouvelle couche "_corrigé" créée
✓ Vérifier absence d'anomalies
```

### Test 4 : Fermeture plugin
```
✓ Lancer analyse 4 couches
✓ Fermer le plugin
✓ Vérifier : couches "merged_*" supprimées
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

## 📊 Dépendances

| Librairie | Rôle | Installation | Requis |
|-----------|------|--------------|--------|
| `qgis.core` | API QGIS | Fourni | ✅ Oui |
| `qgis.gui` | Interface QGIS | Fourni | ✅ Oui |
| `PyQt5` | GUI Framework | Fourni | ✅ Oui |
| `openpyxl` | Export Excel | `pip install openpyxl` | ❌ Non |
| `processing` | Réparation géométries | Fourni | ✅ Oui |

---

## 🎓 Documentation complète

| Document | Contenu |
|----------|---------|
| **[User Guide](docs/user_guide.pdf)** | Guide utilisateur complet |
| **[Config Guide](docs/universal_config_guide.md)** | Configuration par profil |
| **[Developer Guide](docs/developer_guide.md)** | Architecture + API |
| **[Correction Guide](docs/correction_guide_v23.md)** | 🆕 Correction automatique |
| **[Workflow Examples](docs/workflow_examples.md)** | Cas d'usage pratiques |
| **[FAQ](docs/faq.md)** | Questions fréquentes |

---

## 🗺️ Feuille de route

### ✅ v2.3 (Novembre 2025)
- [x] Correction automatique
- [x] Interface améliorée (header, boutons)
- [x] Fusion multi-couches
- [x] Export sélection

### 🔄 v2.4 (Décembre 2025)
- [ ] Dialogue interactif Point/Polygone
- [ ] Historique corrections
- [ ] Annulation/Rétablissement
- [ ] Prévisualisation avant correction

### 🚀 v3.0 (Q1 2026)
- [ ] Mode batch
- [ ] Correction avancée (snapping)
- [ ] Statistiques qualité globales
- [ ] PostGIS integration
- [ ] Rapport PDF avec cartes

---

## 👨‍💻 Contribution

Les contributions sont bienvenues ! 🙏

### Pour contribuer :
1. Fork le dépôt
2. Créer une branche (`git checkout -b feature/MyFeature`)
3. Commit (`git commit -m 'Add MyFeature'`)
4. Push (`git push origin feature/MyFeature`)
5. Ouvrir une Pull Request

### À améliorer :
- 🌍 Traductions (FR/EN/ES)
- 🐛 Signaler des bugs
- 💡 Suggestions d'améliorations
- 📖 Améliorer documentation
- ⭐ Retours d'expérience

---

## ⚖️ Licence

Distribué sous **GPL-3.0**.  
Libre d'utilisation, modification et redistribution.

📄 Voir [LICENSE](./LICENSE)

---

## 📧 Contact & Support

**Auteur** : Aziz T. — KAT Explorer GIS  
**Email** : aziz.explorer@gmail.com  
**GitHub** : [@AzizT-dev](https://github.com/AzizT-dev)

---

## 🙏 Remerciements

- Communauté QGIS pour l'API robuste
- Testeurs beta pour retours précieux
- Utilisateurs signalant bugs et suggestions

---

## 📈 Statistiques

![Stars](https://img.shields.io/github/stars/AzizT-dev/kat_overlap?style=social)
![Forks](https://img.shields.io/github/forks/AzizT-dev/kat_overlap?style=social)
![Issues](https://img.shields.io/github/issues/AzizT-dev/kat_overlap)
![Last Commit](https://img.shields.io/github/last-commit/AzizT-dev/kat_overlap)

---

<div align="center">
  
### ⭐ Si ce plugin vous est utile, n'oubliez pas une étoile ! ⭐

### 🚀 Testez la v2.3 et partagez vos retours !

**Développé avec ❤️ par KAT Explorer GIS**

</div>
