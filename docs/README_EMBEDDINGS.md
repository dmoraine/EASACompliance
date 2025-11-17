# 🤖 Système d'Embeddings EASA - README

## Vue d'ensemble

Le système d'embeddings EASA permet de **rechercher sémantiquement** dans la réglementation aéronautique et de **valider automatiquement la compliance** de manuels opérationnels.

### Fonctionnalités Principales

✅ **Recherche sémantique** - Trouvez les paragraphes pertinents par similarité de sens  
✅ **Validation de compliance** - Vérifiez automatiquement si un manuel respecte la réglementation  
✅ **Base vectorielle SQLite** - Stockage efficace et recherche rapide  
✅ **Modèles pré-entraînés** - Utilisez sentence-transformers (BERT, etc.)  
✅ **API Python simple** - Intégration facile dans vos applications  

## 🚀 Démarrage Rapide (5 minutes)

### 1. Installation

```bash
# Installer les dépendances
pip install sentence-transformers torch numpy tqdm
```

### 2. Construire la base d'embeddings

```bash
# Option simple: une catégorie (ORO.FTL - 17 paragraphes, ~30 secondes)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --category "ORO.FTL" \
    --db "easa_ftl.db"
```

**Résultat attendu:**
```
✅ Parser initialisé: 85804 paragraphes trouvés
✅ 17 paragraphes à traiter
✅ 17 paragraphes extraits
✅ 17 paragraphes ajoutés
✅ BASE D'EMBEDDINGS CONSTRUITE AVEC SUCCÈS
```

### 3. Rechercher

```bash
# Mode interactif
python search_regulations.py --db easa_ftl.db --interactive

# Ou requête unique
python search_regulations.py \
    --db easa_ftl.db \
    --query "flight time limitations for crew members"
```

**Résultat:**
```
✅ 3 résultats:

1. ORO.FTL.205 - Flight time and duty periods
   Score: 0.782
   
2. ORO.FTL.210 - Flight duty period
   Score: 0.745
```

### 4. Valider un manuel

```bash
# Créer un fichier avec un extrait de manuel
echo "Flight crew members shall not exceed maximum flight duty periods" > manual.txt

# Valider
python search_regulations.py --db easa_ftl.db --manual manual.txt
```

**Résultat:**
```
📋 VALIDATION DE COMPLIANCE

✅ 5 paragraphes pertinents trouvés:

1. ORO.FTL.205 - Flight time and duty periods
   📊 Pertinence: 0.812 (81.2%)
   ✅ TRÈS PERTINENT
```

## 📁 Fichiers Principaux

| Fichier | Description |
|---------|-------------|
| **embeddings_manager.py** | API principale pour gérer les embeddings |
| **build_embeddings.py** | Script pour construire la base |
| **search_regulations.py** | Script pour rechercher et valider |
| **test_embeddings.py** | Suite de tests complète |
| **EMBEDDINGS_GUIDE.md** | Documentation complète |

## 🎯 Cas d'Usage

### 1. Recherche Simple

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa_ftl.db")
results = manager.search("rest requirements", top_k=5)

for r in results:
    print(f"{r.reference}: {r.title} (score: {r.score:.2%})")
```

### 2. Validation de Compliance

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa_ftl.db")

# Texte du manuel
manual_text = """
Pilots must ensure adequate rest before flight operations.
Maximum flight duty period is 13 hours.
"""

# Trouver les paragraphes pertinents
results = manager.search(manual_text, top_k=10, min_score=0.5)

# Analyser
for r in results:
    if r.score >= 0.7:
        print(f"✅ {r.reference}: Conforme ({r.score:.1%})")
    else:
        print(f"⚠️  {r.reference}: À vérifier ({r.score:.1%})")
```

### 3. Construction Complète

```python
from embeddings_manager import build_embeddings_database

# Construire la base pour toute une catégorie
manager = build_embeddings_database(
    xml_path="regulations.xml",
    db_path="easa_oro.db",
    pattern=r"ORO\.[A-Z]+\.[0-9]+",  # Tous les ORO
    batch_size=32
)

# Utiliser
results = manager.search("operator responsibilities", top_k=5)
```

## 🧪 Tests

```bash
# Exécuter tous les tests
python test_embeddings.py
```

**Tests inclus:**
1. ✅ Construction de la base
2. ✅ Recherche simple
3. ✅ Recherche avec filtres
4. ✅ Validation de manuel
5. ✅ Statistiques
6. ✅ Export JSON

## 📊 Performance

| Opération | Temps | Notes |
|-----------|-------|-------|
| Construction (17 paragraphes) | ~30s | ORO.FTL |
| Construction (439 paragraphes) | ~10min | Document complet |
| Recherche | ~0.1-0.5s | Par requête |
| Validation de manuel | ~1-3s | Selon la taille |

**Modèles disponibles:**
- `all-MiniLM-L6-v2` (défaut): 384 dimensions, ~80MB, rapide
- `all-mpnet-base-v2`: 768 dimensions, ~420MB, plus précis
- `paraphrase-multilingual-MiniLM-L12-v2`: Multilingue

## 🔧 Options de Construction

```bash
# Toute la réglementation
python build_embeddings.py --xml regulations.xml

# Une catégorie spécifique
python build_embeddings.py --category "ORO.FTL"

# Pattern personnalisé
python build_embeddings.py --pattern "ORO\.[A-Z]+\.[0-9]+"

# Modèle plus précis
python build_embeddings.py --model "all-mpnet-base-v2"

# Vider et reconstruire
python build_embeddings.py --clear
```

## 🔍 Options de Recherche

```bash
# Mode interactif
python search_regulations.py --interactive

# Requête unique
python search_regulations.py --query "flight time"

# Avec filtres
python search_regulations.py \
    --query "rest requirements" \
    --top-k 10 \
    --min-score 0.5

# Validation de manuel
python search_regulations.py --manual manual.txt

# Batch (fichier de requêtes)
python search_regulations.py \
    --queries-file queries.txt \
    --output results.json
```

## 📚 Documentation

- **EMBEDDINGS_GUIDE.md** - Guide complet avec exemples avancés
- **README_EMBEDDINGS.md** - Ce fichier (démarrage rapide)
- **API Documentation** - Voir docstrings dans `embeddings_manager.py`

## 🎓 Exemples Avancés

### Comparer Deux Versions d'un Manuel

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa.db")

# Charger les versions
with open("manual_v1.txt") as f:
    v1 = f.read()
with open("manual_v2.txt") as f:
    v2 = f.read()

# Comparer
results_v1 = set(r.reference for r in manager.search(v1, top_k=20))
results_v2 = set(r.reference for r in manager.search(v2, top_k=20))

print("Nouveaux paragraphes:", results_v2 - results_v1)
print("Paragraphes retirés:", results_v1 - results_v2)
```

### Export pour Analyse

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa.db")

# Exporter une catégorie
manager.export_to_json("oro_ftl.json", category_filter="ORO.FTL")

# Statistiques
stats = manager.get_stats()
print(f"Total: {stats['total_paragraphs']} paragraphes")
print(f"Catégories: {len(stats['categories'])}")
```

### Recherche par Catégorie

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa.db")

# Rechercher seulement dans ORO.FTL
results = manager.search(
    "flight time",
    top_k=10,
    category_filter="ORO.FTL"
)
```

## 🐛 Dépannage

### "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### "Database not found"

Construisez d'abord la base:
```bash
python build_embeddings.py --category "ORO.FTL"
```

### Performance lente

- Utilisez un GPU si disponible
- Augmentez `--batch-size`
- Utilisez un modèle plus petit

### Scores trop bas

- Essayez un modèle plus précis (`all-mpnet-base-v2`)
- Réduisez `--min-score`
- Vérifiez que la requête est en anglais

## 🔄 Workflow Recommandé

```
1. Construction
   └─> python build_embeddings.py --category "ORO.FTL"

2. Test
   └─> python search_regulations.py --interactive

3. Validation
   └─> python search_regulations.py --manual manual.txt

4. Intégration
   └─> from embeddings_manager import EmbeddingsManager
```

## 📞 Support

- 📖 **Guide complet**: `EMBEDDINGS_GUIDE.md`
- 🧪 **Tests**: `python test_embeddings.py`
- 💡 **Exemples**: Voir les scripts `build_embeddings.py` et `search_regulations.py`

## ✅ Checklist

- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Base construite (`python build_embeddings.py`)
- [ ] Tests réussis (`python test_embeddings.py`)
- [ ] Recherche testée (`python search_regulations.py --interactive`)
- [ ] Validation testée (avec un extrait de manuel)

## 🎉 Résumé

**Ce système vous permet de:**
1. ✅ Construire une base vectorielle de la réglementation EASA
2. ✅ Rechercher sémantiquement dans les paragraphes
3. ✅ Valider automatiquement la compliance de manuels
4. ✅ Trouver les paragraphes pertinents en quelques millisecondes

**Prêt en 5 minutes !**

---

**Version:** 1.2.0  
**Date:** 2025-11-14  
**Python:** 3.8+  
**Dépendances:** sentence-transformers, torch, numpy

