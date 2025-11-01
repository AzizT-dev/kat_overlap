# 🧩 KAT Overlap for QGIS

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/AzizT-dev/kat_overlap/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-%E2%89%A53.22-brightgreen.svg)](https://qgis.org)
[![Platform](https://img.shields.io/badge/platform-QGIS%20Plugin-yellow.svg)](https://plugins.qgis.org/)
[![Issues](https://img.shields.io/github/issues/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/issues)
[![Last Commit](https://img.shields.io/github/last-commit/AzizT-dev/kat_overlap.svg)](https://github.com/AzizT-dev/kat_overlap/commits/main)

---

**KAT Overlap** est un plugin QGIS de **contrôle qualité spatiale**.  
Il détecte, mesure et classe les zones de **chevauchement géométrique** entre entités vectorielles, que ce soit **dans une même couche** ou **entre plusieurs couches**.  

L’outil est conçu pour répondre aux besoins des projets de cartographie, de gestion foncière, d’aménagement du territoire et d’analyse environnementale.

---

## 🚀 Fonctionnalités principales

- 🔹 Analyse **mono-couche** et **multi-couches**
- 🔹 Détection robuste des chevauchements via **index spatial** (R-tree)
- 🔹 **Classification automatique** selon la gravité (faible → critique)
- 🔹 **Rapport interactif** avec filtres, recherche et export (TXT / XLSX)
- 🔹 Création d’une **couche mémoire stylisée** représentant les zones d’intersection
- 🔹 Gestion automatique des **géométries invalides**
- 🔹 Support **multi-CRS** avec reprojection dynamique (UTM, polaire, etc.)
- 🔹 Interface fluide et intuitive, sans dépendance à GRASS ou SAGA
- 🔹 Exécution optimisée avec **threading** pour les grands volumes de données

---

## 🧱 Structure du plugin

```

kat_overlap/
├── **init**.py
├── kat_overlap_improved_def2.py
├── metadata.txt
├── icon.png
├── resources.qrc
├── forms/
├── i18n/
└── docs/
├── banner.png
└── screenshots/

````

---

## 📦 Installation

### 🟢 Méthode 1 — via le gestionnaire d’extensions QGIS (après validation)
1. Ouvrir QGIS → **Extensions → Installer et gérer les extensions**
2. Rechercher **KAT Overlap**
3. Cliquer sur **Installer**

### 🟣 Méthode 2 — via GitHub
1. Télécharger ou cloner le dépôt :
   ```bash
   git clone https://github.com/AzizT-dev/kat_overlap.git
````

2. Zipper le dossier `kat_overlap/`
3. Dans QGIS :
   *Extensions → Installer depuis un ZIP...*
4. Sélectionner le fichier ZIP et valider.

---

## ⚙️ Utilisation

1. Sélectionnez une ou plusieurs **couches polygonales**.
2. Choisissez le **champ d’identifiant** et la **tolérance minimale** d’aire.
3. Sélectionnez le **mode d’analyse** (*intra-couche* ou *inter-couches*).
4. Cliquez sur **Lancer l’analyse**.
5. Explorez les résultats dans le tableau interactif, ou exportez le rapport.

### Résultats disponibles :

* Liste des entités chevauchantes
* Surface du chevauchement
* Classe de gravité
* Centroides et géométries résultantes
* Lien direct de **zoom sur conflit**

---

## 🧮 Dépendances

| Librairie                 | Rôle                  | Installation           |
| ------------------------- | --------------------- | ---------------------- |
| `openpyxl`                | Export Excel (XLSX)   | `pip install openpyxl` |
| `PyQt5` (inclus via QGIS) | Interface utilisateur | -                      |
| `qgis.core` / `qgis.gui`  | API QGIS              | déjà inclus            |

* **QGIS minimum requis :** 3.22
* **Version recommandée :** 3.28 ou 3.34 LTR
* **Python requis :** ≥ 3.9

---

## 📊 Exemple d’application

| Contexte                      | Objectif                                     | Résultat                  |
| ----------------------------- | -------------------------------------------- | ------------------------- |
| Données cadastrales           | Détecter des parcelles superposées           | Rapport + couche stylisée |
| Cartographie environnementale | Identifier des zones d’habitat chevauchantes | Export analytique         |
| Données topographiques        | Corriger des doublons de polygones           | Nettoyage géométrique     |

---

## 📸 Captures d’écran

| Interface principale           | Résultats d’analyse                      |
| ------------------------------ | ---------------------------------------- |
| ![ui](docs/screenshots/ui.png) | ![results](docs/screenshots/results.png) |

*(ajouter vos captures dans `/docs/screenshots/`)*

---

## 🧑‍💻 Auteur

**Aziz T. — KAT Explorer GIS**
🌐 [https://github.com/AzizT-dev](https://github.com/AzizT-dev)

---

## ⚖️ Licence

Ce projet est distribué sous la **licence GNU General Public License v3.0 (GPL-3.0)**.
Vous êtes libre d’utiliser, modifier et redistribuer le code tant que la même licence est conservée.

📄 Voir le fichier [`LICENSE`](./LICENSE) pour le texte complet.

---

## 🧾 Journal des versions

| Version   | Date       | Changements                                                                   |
| --------- | ---------- | ----------------------------------------------------------------------------- |
| **2.0.0** | 2025-10-31 | Optimisation du threading, classification automatique, amélioration interface |
| **1.0.0** | 2024-12-10 | Première version stable interne (KaT Platform)                                |

---

## 💬 Retours et contributions

Vous pouvez :

* Signaler un bug ou une anomalie via [GitHub Issues](https://github.com/AzizT-dev/kat_overlap/issues)
* Proposer des améliorations ou traductions (FR / EN)
* Partager vos retours via la section Discussions (si activée)

---

## 🔖 Mots-clés (tags GitHub)

`qgis` · `gis` · `spatial` · `overlap` · `intersection` · `vector` · `quality` · `geometry` · `kat explorer gis`

```
