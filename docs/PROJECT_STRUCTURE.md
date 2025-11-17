# 📁 Structure du Projet EASACompliance

```
EASACompliance/
├── 📦 easacompliance/           # Package Python principal
│   ├── __init__.py              # Exports publics du package
│   ├── parser.py                # Parser EASA v2 (structure XML)
│   ├── embeddings.py            # Gestionnaire d'embeddings
│   └── scripts/                 # Scripts exécutables du package
│       ├── build_embeddings.py  # Construction de la base d'embeddings
│       └── search_regulations.py # Recherche dans la base
│
├── 📚 docs/                     # Documentation
│   ├── QUICKSTART.md            # Guide de démarrage rapide
│   ├── EMBEDDINGS_GUIDE.md      # Guide des embeddings
│   ├── PROJECT_STRUCTURE.md     # Ce fichier
│   ├── CHANGELOG.md             # Historique des changements
│   ├── REFONTE_PARSER_RAPPORT.md # Rapport parser v2
│   └── RAPPORT_CORRECTION_AMC_GM.md # Rapport correction AMC/GM
│
├── 🔧 tools/                    # Outils de développement
│   └── diagnostics/             # Scripts de diagnostic
│       ├── README.md            # Documentation des outils
│       ├── diagnostic_types.py  # Analyse TypeOfContent XML
│       ├── diagnostic_db.py     # Analyse base d'embeddings
│       ├── diagnostic_references.py # Vérification extraction
│       ├── diagnostic_source_titles.py # Exemples source-title
│       ├── diagnostic_no_reference.py # Topics sans référence
│       └── diagnostic_compare.py # Comparaison de bases
│
├── 🧪 tests/                    # Tests unitaires
│   ├── __init__.py
│   └── test_embeddings.py
│
├── 📊 data/                     # Schémas et données
│   └── EASA-eRules-XML-Export-Schema-1.0.0.xsd
│
├── 📄 Configuration
│   ├── pyproject.toml           # Configuration du package
│   ├── requirements.txt         # Dépendances (legacy)
│   ├── uv.lock                  # Lock file uv
│   └── README.md                # Documentation principale
│
└── 📁 Données de travail (non versionnées)
    ├── easa_complete.db         # Base d'embeddings complète
    ├── Easy Access Rules...xml  # Fichier XML EASA
    └── *.zip                    # Archives téléchargées
```

## 📦 Package Principal (`easacompliance/`)

### Modules Core

- **`parser.py`** : Parser EASA v2
  - Classe `EASAParser` : Parser basé sur la structure XML officielle
  - Classe `Topic` : Représentation d'un topic réglementaire
  - Enum `TopicType` : Types de contenu (IR, AMC, GM, CS, etc.)

- **`embeddings.py`** : Système d'embeddings
  - Classe `EmbeddingsManager` : Gestion de la base vectorielle
  - Classe `SearchResult` : Résultat de recherche
  - Support SQLite avec vectors

### Scripts Exécutables (`scripts/`)

- **`build_embeddings.py`** : Construction de la base
  ```bash
  uv run python easacompliance/scripts/build_embeddings.py \
    --xml "regulations.xml" \
    --db "embeddings.db" \
    --clear
  ```

- **`search_regulations.py`** : Recherche interactive
  ```bash
  uv run python easacompliance/scripts/search_regulations.py \
    --db "embeddings.db"
  ```

## 🔧 Outils de Diagnostic (`tools/diagnostics/`)

Scripts de développement pour analyser et déboguer :

- **`diagnostic_types.py`** : Analyse TypeOfContent dans XML
- **`diagnostic_db.py`** : Analyse base d'embeddings
- **`diagnostic_references.py`** : Vérification extraction références
- **`diagnostic_source_titles.py`** : Exemples source-title
- **`diagnostic_no_reference.py`** : Topics sans référence
- **`diagnostic_compare.py`** : Comparaison de bases

Voir `tools/diagnostics/README.md` pour plus de détails.

## 📚 Documentation (`docs/`)

- **`QUICKSTART.md`** : Guide de démarrage rapide
- **`EMBEDDINGS_GUIDE.md`** : Guide détaillé des embeddings
- **`PROJECT_STRUCTURE.md`** : Structure du projet (ce fichier)
- **`CHANGELOG.md`** : Historique des versions
- **`REFONTE_PARSER_RAPPORT.md`** : Rapport technique parser v2
- **`RAPPORT_CORRECTION_AMC_GM.md`** : Correction parsing AMC/GM

## 🧪 Tests (`tests/`)

Tests unitaires du package :
- `test_embeddings.py` : Tests du système d'embeddings

```bash
# Lancer les tests
uv run pytest
```

## 📊 Données (`data/`)

- **`EASA-eRules-XML-Export-Schema-1.0.0.xsd`** : Schéma XML officiel EASA

## ⚙️ Configuration

### `pyproject.toml`
Configuration principale du package :
- Métadonnées du projet
- Dépendances
- Entry points pour les scripts
- Configuration des outils (ruff, black, etc.)

### `uv.lock`
Lock file généré par `uv` pour garantir la reproductibilité.

### `requirements.txt` (legacy)
Fichier de dépendances legacy, remplacé par `pyproject.toml`.

## 🚀 Utilisation

### Installation en Mode Développement

```bash
# Cloner le projet
git clone <repository>
cd EASACompliance

# Installer avec uv
uv sync

# Installer en mode éditable
uv pip install -e .
```

### Construire une Base d'Embeddings

```bash
# Base complète
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_complete.db \
  --clear

# Avec filtres
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "regulations.xml" \
  --db easa_filtered.db \
  --types IR AMC GM_IR \
  --subject "Part-ORO" \
  --clear
```

### Rechercher dans la Base

```bash
# Mode interactif
uv run python easacompliance/scripts/search_regulations.py \
  --db easa_complete.db

# Requête unique
uv run python easacompliance/scripts/search_regulations.py \
  --db easa_complete.db \
  --query "flight time limitations" \
  --top-k 5
```

### Diagnostic

```bash
# Analyser un XML
python tools/diagnostics/diagnostic_types.py "regulations.xml"

# Analyser une base
python tools/diagnostics/diagnostic_db.py "embeddings.db"

# Comparer deux bases
python tools/diagnostics/diagnostic_compare.py "old.db" "new.db"
```

## 📝 Conventions

### Nommage

- **Modules** : snake_case (ex: `embeddings.py`)
- **Classes** : PascalCase (ex: `EASAParser`)
- **Fonctions** : snake_case (ex: `build_embeddings_database`)
- **Constantes** : UPPER_CASE (ex: `NS_ER`)

### Organisation

- **Code principal** : `easacompliance/`
- **Scripts exécutables** : `easacompliance/scripts/`
- **Tests** : `tests/`
- **Documentation** : `docs/`
- **Outils de dev** : `tools/`
- **Données** : `data/` (schémas) ou racine (bases/XML)

### Git

- **Versionner** : Code source, docs, tests, schémas
- **Ignorer** : `*.db`, `*.xml` (fichiers de données), `__pycache__`, `.venv/`

## 🔄 Workflow de Développement

1. **Faire des modifications** dans `easacompliance/`
2. **Tester** avec `uv run pytest`
3. **Valider** avec les scripts de diagnostic
4. **Documenter** dans `docs/`
5. **Commit** avec un message clair

## 📖 Ressources

- **Parser v2** : Voir `docs/REFONTE_PARSER_RAPPORT.md`
- **Embeddings** : Voir `docs/EMBEDDINGS_GUIDE.md`
- **Correction AMC/GM** : Voir `docs/RAPPORT_CORRECTION_AMC_GM.md`
- **Schéma XML** : Voir `data/EASA-eRules-XML-Export-Schema-1.0.0.xsd`

---

**Version** : 2.0.0  
**Dernière mise à jour** : 2025-11-15
