# 🤖 Guide des Embeddings EASA

## Vue d'ensemble

Le système d'embeddings EASA permet de :
- 🔍 **Rechercher** sémantiquement dans la réglementation
- ✅ **Valider** la compliance d'un manuel
- 📊 **Trouver** les paragraphes pertinents automatiquement
- 🎯 **Comparer** des textes avec la réglementation

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Cela installera :
# - sentence-transformers (pour les embeddings)
# - torch (backend pour les modèles)
# - numpy, tqdm (utilitaires)
```

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EASA Compliance System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Parser XML (easa_parser.py)                             │
│     └─> Extrait les paragraphes EASA                        │
│                                                               │
│  2. Embeddings Manager (embeddings_manager.py)              │
│     ├─> Génère les embeddings (sentence-transformers)       │
│     ├─> Stocke dans SQLite                                  │
│     └─> Recherche sémantique                                │
│                                                               │
│  3. Applications                                             │
│     ├─> build_embeddings.py (construction de la base)       │
│     └─> search_regulations.py (recherche et validation)     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Utilisation

### 1. Construire la Base d'Embeddings

#### Option A: Toute la réglementation

```bash
python build_embeddings.py --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml"
```

#### Option B: Une catégorie spécifique (recommandé pour commencer)

```bash
# Seulement ORO.FTL (17 paragraphes)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --category "ORO.FTL" \
    --db "easa_ftl.db"

# Seulement ORO.GEN
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --category "ORO.GEN" \
    --db "easa_gen.db"
```

#### Option C: Pattern personnalisé

```bash
# Tous les ORO (FTL, GEN, etc.)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --pattern "ORO\.[A-Z]+\.[0-9]+" \
    --db "easa_oro.db"
```

#### Options avancées

```bash
python build_embeddings.py \
    --xml "regulations.xml" \
    --db "easa.db" \
    --model "all-mpnet-base-v2" \    # Modèle plus précis
    --batch-size 64 \                 # Batch plus grand (si GPU)
    --clear                           # Vider la base avant
```

**Modèles disponibles:**
- `all-MiniLM-L6-v2` (défaut): Rapide, 384 dimensions, ~80MB
- `all-mpnet-base-v2`: Plus précis, 768 dimensions, ~420MB
- `paraphrase-multilingual-MiniLM-L12-v2`: Multilingue

### 2. Rechercher dans la Réglementation

#### Mode Interactif (recommandé)

```bash
python search_regulations.py --interactive
```

**Exemple de session:**
```
🔎 Requête: flight time limitations for crew members
✅ 3 résultats trouvés:

1. 📋 ORO.FTL.205 - Flight time and duty periods
   📊 Score: 0.782 (78.2%)
   📄 Extrait: The operator shall establish...

2. 📋 ORO.FTL.210 - Flight duty period
   📊 Score: 0.745 (74.5%)
   📄 Extrait: The maximum daily FDP...
```

#### Mode Requête Unique

```bash
python search_regulations.py \
    --query "rest requirements for pilots" \
    --top-k 5
```

#### Mode Batch (plusieurs requêtes)

```bash
# Créer un fichier queries.txt
echo "flight time limitations" > queries.txt
echo "rest requirements" >> queries.txt
echo "operator responsibilities" >> queries.txt

# Exécuter
python search_regulations.py \
    --queries-file queries.txt \
    --output results.json
```

### 3. Valider la Compliance d'un Manuel

```bash
# Créer un fichier avec le texte du manuel
cat > manual_extract.txt << 'EOF'
Flight crew members shall not exceed the maximum flight duty period
as specified in the operations manual. Rest periods shall be provided
in accordance with applicable regulations.
EOF

# Valider
python search_regulations.py \
    --manual manual_extract.txt \
    --top-k 10 \
    --min-score 0.3
```

**Résultat:**
```
📋 VALIDATION DE COMPLIANCE

✅ 8 paragraphes pertinents trouvés:

1. 📋 ORO.FTL.205 - Flight time and duty periods
   📊 Pertinence: 0.812 (81.2%)
   ✅ TRÈS PERTINENT

2. 📋 ORO.FTL.235 - Rest periods
   📊 Pertinence: 0.756 (75.6%)
   ✅ TRÈS PERTINENT

📊 RÉSUMÉ
✅ Très pertinents (≥70%): 3
⚠️  Pertinents (50-70%): 3
ℹ️  Potentiellement pertinents (30-50%): 2
```

## 🎯 Cas d'Usage

### Cas 1: Vérifier la Compliance d'une Procédure

```python
from embeddings_manager import EmbeddingsManager

# Charger la base
manager = EmbeddingsManager(db_path="easa_embeddings.db")

# Texte de la procédure
procedure = """
Pilots must ensure adequate rest before flight operations.
Maximum flight duty period is 13 hours for operations with
2 crew members.
"""

# Rechercher les paragraphes pertinents
results = manager.search(procedure, top_k=5, min_score=0.5)

# Analyser
for result in results:
    print(f"{result.reference}: {result.score:.2%}")
    if result.score >= 0.7:
        print("  ✅ Conforme")
    else:
        print("  ⚠️  À vérifier")
```

### Cas 2: Trouver tous les Paragraphes sur un Sujet

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa_embeddings.db")

# Rechercher tous les paragraphes sur les "rest requirements"
results = manager.search(
    "rest requirements and rest periods",
    top_k=20,
    min_score=0.4
)

# Grouper par catégorie
by_category = {}
for r in results:
    cat = r.reference.rsplit('.', 1)[0]
    if cat not in by_category:
        by_category[cat] = []
    by_category[cat].append(r)

# Afficher
for cat, items in by_category.items():
    print(f"\n{cat}: {len(items)} paragraphes")
    for item in items:
        print(f"  • {item.reference}: {item.title}")
```

### Cas 3: Comparer Deux Manuels

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa_embeddings.db")

# Charger les manuels
with open("manual_v1.txt") as f:
    manual_v1 = f.read()

with open("manual_v2.txt") as f:
    manual_v2 = f.read()

# Comparer
results_v1 = manager.search(manual_v1, top_k=10)
results_v2 = manager.search(manual_v2, top_k=10)

# Analyser les différences
refs_v1 = set(r.reference for r in results_v1)
refs_v2 = set(r.reference for r in results_v2)

print("Paragraphes ajoutés:", refs_v2 - refs_v1)
print("Paragraphes retirés:", refs_v1 - refs_v2)
```

### Cas 4: Export pour Analyse

```python
from embeddings_manager import EmbeddingsManager

manager = EmbeddingsManager(db_path="easa_embeddings.db")

# Exporter une catégorie
manager.export_to_json(
    output_path="oro_ftl_export.json",
    category_filter="ORO.FTL"
)

# Statistiques
stats = manager.get_stats()
print(f"Total: {stats['total_paragraphs']} paragraphes")
print(f"Taille: {stats['db_size_mb']} MB")
```

## 📊 Performance

### Temps de Construction

| Catégorie | Paragraphes | Temps | Taille DB |
|-----------|-------------|-------|-----------|
| ORO.FTL | 17 | ~30s | ~2 MB |
| ORO.GEN | 25 | ~45s | ~3 MB |
| Tout ORO | ~100 | ~3min | ~12 MB |
| Complet | 439 | ~10min | ~50 MB |

### Temps de Recherche

- **Requête simple**: ~0.1-0.5s
- **Validation de manuel**: ~1-3s (selon la taille)
- **Batch (100 requêtes)**: ~30-60s

### Optimisations

```python
# ✅ BON: Réutiliser le manager
manager = EmbeddingsManager(db_path="easa.db")
for query in queries:
    results = manager.search(query)

# ❌ MAUVAIS: Créer un nouveau manager à chaque fois
for query in queries:
    manager = EmbeddingsManager(db_path="easa.db")  # Lent !
    results = manager.search(query)
```

## 🔍 Interprétation des Scores

| Score | Signification | Action |
|-------|---------------|--------|
| ≥ 0.80 | Très similaire | ✅ Probablement conforme |
| 0.60-0.79 | Similaire | ⚠️  Vérifier manuellement |
| 0.40-0.59 | Potentiellement lié | ℹ️  Examiner le contexte |
| < 0.40 | Peu similaire | ❓ Probablement non pertinent |

**Note:** Les scores dépendent du modèle utilisé et du contexte.

## 🛠️ API Python

### Classe `EmbeddingsManager`

```python
from embeddings_manager import EmbeddingsManager

# Initialiser
manager = EmbeddingsManager(
    db_path="easa.db",
    model_name="all-MiniLM-L6-v2"
)

# Ajouter un paragraphe
from easa_parser import EASAParser
parser = EASAParser("regulations.xml")
paragraph = parser.extract_paragraph("ORO.FTL.110")
manager.add_paragraph(paragraph)

# Ajouter en batch (recommandé)
paragraphs = [parser.extract_paragraph(ref) for ref in refs]
manager.add_paragraphs_batch(paragraphs, batch_size=32)

# Rechercher
results = manager.search(
    query="flight time limitations",
    top_k=5,
    category_filter="ORO.FTL",  # Optionnel
    min_score=0.3                # Optionnel
)

# Statistiques
stats = manager.get_stats()

# Export
manager.export_to_json("export.json", category_filter="ORO.FTL")

# Vider
manager.clear_database()
```

### Fonction Utilitaire

```python
from embeddings_manager import build_embeddings_database

# Construction complète en une fonction
manager = build_embeddings_database(
    xml_path="regulations.xml",
    db_path="easa.db",
    pattern=r"ORO\.FTL\.[0-9]+",
    batch_size=32
)
```

## 🐛 Dépannage

### Erreur: "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### Erreur: "Model not found"

Le modèle se télécharge automatiquement au premier lancement.
Assurez-vous d'avoir une connexion internet.

### Performance lente

- Utilisez un GPU si disponible (PyTorch détecte automatiquement)
- Augmentez `batch_size` (si vous avez assez de RAM/VRAM)
- Utilisez un modèle plus petit (`all-MiniLM-L6-v2`)

### Base de données corrompue

```bash
# Reconstruire
python build_embeddings.py --clear
```

## 📚 Ressources

- **sentence-transformers**: https://www.sbert.net/
- **Modèles disponibles**: https://www.sbert.net/docs/pretrained_models.html
- **Documentation EASA**: https://www.easa.europa.eu/

## 🎓 Exemples Complets

Voir les fichiers:
- `build_embeddings.py` - Construction de la base
- `search_regulations.py` - Recherche et validation
- `embeddings_manager.py` - API complète

## 🚀 Prochaines Étapes

1. ✅ Construire la base d'embeddings
2. ✅ Tester avec des requêtes simples
3. ✅ Valider un extrait de manuel
4. 🔄 Intégrer dans votre application
5. 🔄 Affiner les seuils de score
6. 🔄 Ajouter d'autres catégories

---

**Version:** 1.2.0  
**Date:** 2025-11-14  
**Compatibilité:** Python 3.8+

