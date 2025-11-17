# Changelog - EASA Parser

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [1.1.0] - 2025-11-14

### ✨ Nouvelles Fonctionnalités

#### Table des Matières
- **`get_table_of_contents(pattern=None)`**: Extrait la liste de tous les paragraphes principaux
  - Retourne référence, titre, index et catégorie pour chaque paragraphe
  - Support du filtrage par pattern regex
  - Dédoublonnage automatique
  - Performance optimisée (~2-3s pour 439 paragraphes)

- **`get_categories()`**: Retourne la distribution des paragraphes par catégorie
  - Compte automatique par catégorie
  - Résultat trié alphabétiquement
  - Utile pour l'exploration du document

### 📚 Documentation
- Ajout de `TABLE_OF_CONTENTS_GUIDE.md` - Guide complet de la fonctionnalité TOC
- Mise à jour de `QUICKSTART.md` avec les nouvelles fonctionnalités
- Ajout de ce `CHANGELOG.md`

### 🧪 Tests et Exemples
- **`test_toc.py`**: Suite de tests complète pour la TOC
  - Test de la table complète
  - Test du filtrage
  - Test des catégories
  - Test d'extraction par lots
  - Test d'export JSON
  - Test d'export de la TOC
  
- **`example_toc.py`**: Exemple simple d'utilisation
  - Workflow complet: TOC → Extraction → RAG
  - Export JSON
  - Préparation pour embeddings

### 📊 Résultats
Sur le document "Easy Access Rules for Air Operations - February 2025":
- **439 paragraphes principaux** identifiés
- **37 catégories** détectées
- **17 paragraphes ORO.FTL** (exemple)
- **85,804 paragraphes XML** au total

### 🎯 Cas d'Usage
La table des matières permet maintenant de:
1. Explorer le document sans charger tout le contenu
2. Filtrer par catégorie (ex: ORO.FTL, ORO.GEN)
3. Extraire par lots de manière efficace
4. Préparer un pipeline RAG optimisé

### 💡 Exemple d'Utilisation

```python
from easa_parser import EASAParser

# Initialiser
parser = EASAParser("regulations.xml")

# Obtenir la table des matières
toc = parser.get_table_of_contents(pattern=r"ORO\.FTL\.[0-9]+")

# Extraire chaque paragraphe
for item in toc:
    paragraph = parser.extract_paragraph(item['reference'])
    # Traiter...
```

---

## [1.0.0] - 2025-11-13

### ✨ Fonctionnalités Initiales

#### Parser XML
- **`EASAParser`**: Classe principale pour parser les documents EASA
  - Support du format OOXML
  - Extraction de paragraphes complets
  - Support des AMC (Acceptable Means of Compliance)
  - Support des GM (Guidance Material)
  - Extraction des métadonnées (régulation, dates)

#### Modèle de Données
- **`Paragraph`**: Dataclass pour représenter un paragraphe
  - Référence, titre, contenu
  - Type (MAIN, AMC, GM, SUBPARAGRAPH, CONTENT)
  - Sous-paragraphes hiérarchiques
  - Métadonnées
  - Méthodes: `to_dict()`, `get_full_text()`

- **`ParagraphType`**: Enum pour les types de paragraphes

#### Méthodes d'Extraction
- **`extract_paragraph(ref, include_amc_gm=True)`**: Extrait un paragraphe complet
- **`search_paragraphs(pattern)`**: Recherche par regex
- **`find_paragraph_index(reference)`**: Trouve l'index d'un paragraphe
- **`get_paragraph_summary(paragraph)`**: Génère un résumé

#### Fonctionnalités RAG
- Export JSON via `to_dict()`
- Texte complet via `get_full_text()`
- Métadonnées structurées
- Support des sous-éléments hiérarchiques

### 📚 Documentation
- `README_PARSER.md` - Documentation complète
- `QUICKSTART.md` - Guide de démarrage rapide
- `PROJECT_STRUCTURE.md` - Structure du projet
- `SUMMARY.md` - Résumé du projet

### 🧪 Tests et Exemples
- `test_parser.py` - Suite de tests complète (6 tests)
- `example_usage.py` - Exemple d'utilisation simple
- `poc.py` - Proof of concept initial

### 📦 Structure
- Package Python avec `__init__.py`
- `requirements.txt` pour les dépendances
- Support Python 3.8+

### 🎯 Validation
Tests réussis sur:
- Extraction de ORO.FTL.110 (10 sous-paragraphes + 4 AMC/GM)
- Recherche par pattern
- Export JSON
- Génération de texte complet (3,859 caractères)
- Extraction sans AMC/GM

---

## Légende

- ✨ Nouvelles fonctionnalités
- 🐛 Corrections de bugs
- 📚 Documentation
- 🧪 Tests
- 🎯 Améliorations
- ⚡ Performance
- 🔒 Sécurité
- 📦 Dépendances
- 🔧 Configuration

