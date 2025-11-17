# 🎯 Rapport de Correction - Parsing AMC et GM

## 📊 Problème Initial

L'analyse du fichier XSD et du XML EASA a révélé que **86.6% des topics** (2907 sur 3357) étaient exclus de la base de données d'embeddings.

### Topics manquants
- ❌ **1263 AMC** (Acceptable Means of Compliance)
- ❌ **1026 GM to IR** (Guidance Material to IR)
- ❌ **18 GM to CS** (Guidance Material to CS)
- ❌ **582 IR supplémentaires**

### Cause racine
Le script `build_embeddings.py` filtrait les topics avec `if topic.reference:`, mais :
- Les AMC/GM ont un format différent (`AMC1 ORO.FTL.110` au lieu de `ORO.FTL.110`)
- La regex d'extraction ne capturait que les références au début de la chaîne
- Résultat : 86.6% des topics exclus !

---

## ✅ Solutions Implémentées

### 1. Amélioration du Parser (`easacompliance/parser.py`)

**Méthode `_extract_reference_and_title()` améliorée :**

```python
# Cas 1: Format AMC/GM (ex: "AMC1 ORO.FTL.110 Title")
amc_gm_pattern = re.compile(
    r'^((?:AMC|GM)\d+)\s+'  # AMC1 ou GM1
    r'([A-Z]{2,4}[\.\-\s][A-Z]{2,4}\.[0-9]+(?:\.[0-9]+)?(?:\([a-z0-9;]+\))?)'
)

# Cas 2: Format Article (ex: "AMC1 Article 2(1)(d) Definitions")
article_pattern = re.compile(
    r'^((?:AMC|GM)\d+\s+Article\s+[\d\w\(\)\.\;]+)'
)
```

**Résultat :** Extraction de références passée de 13.4% à **50%** des topics

### 2. Suppression du Filtre Restrictif (`scripts/build_embeddings.py`)

**Avant :**
```python
for topic in topics:
    if topic.reference:  # ❌ Exclut 86.6% des topics
        paragraphs.append(topic)
```

**Après :**
```python
for topic in topics:
    # Filtrer uniquement les topics COMPLÈTEMENT vides
    if not topic.reference and not topic.title and not topic.content:
        skipped_empty += 1
        continue
    paragraphs.append(topic)  # ✅ Garde tout ce qui a du contenu
```

### 3. Identifiants de Secours

Pour les topics sans référence :
1. Utiliser le **titre** (tronqué à 60 caractères)
2. Sinon, utiliser l'**ERules ID**
3. Dernier recours : `"UNKNOWN"`

---

## 📈 Résultats

### Comparaison Avant/Après

| Type | Ancienne DB | Nouvelle DB | Gain |
|------|-------------|-------------|------|
| **AMC to IR** | 0 (0%) | **1156 (36.1%)** | +∞ |
| **GM to IR** | 0 (0%) | **982 (30.7%)** | +∞ |
| **GM to CS** | 0 (0%) | **17 (0.5%)** | +∞ |
| **IR** | 440 (98.4%) | **1022 (31.9%)** | +132% |
| **CS** | 7 (1.6%) | **7 (0.2%)** | stable |
| **Easy access** | 0 | **9 (0.3%)** | nouveau |
| **Other** | 0 | **6 (0.2%)** | nouveau |
| **TOTAL** | **447** | **3199** | **+716%** |

### Couverture

- ✅ **3199 topics** indexés sur 3357 disponibles (95.3%)
- ✅ **100%** des entrées ont du contenu
- ⚠️ **158 topics** (4.7%) exclus car complètement vides

### Exemples de Topics AMC

```
AMC1 ARO.GEN.120(d)(3) - Means of compliance
AMC1 ARO.GEN.120(e) - Means of compliance
AMC1 ARO.GEN.135A - Immediate reaction to an information security incident
AMC1 ARO.GEN.200(a) - Management system
AMC2 ARO.GEN.200(a)(2) - Management system
```

### Exemples de Topics GM

```
GM1 Article 2(1)(d) - Definitions
GM1 Article 3(5)(e) - Oversight capabilities
GM1 Article 4(3) - Ramp inspections
GM1 Article 6.4a - Derogations
GM2 Article 6.4a(a);(b) - Derogations
```

---

## 🔧 Fichiers Modifiés

1. **`easacompliance/parser.py`** (lignes 239-302)
   - Amélioration de `_extract_reference_and_title()`
   - Support des formats AMC/GM/Article

2. **`scripts/build_embeddings.py`** (lignes 16-89, 153-169)
   - Adaptateur avec identifiants de secours
   - Filtre permissif au lieu de restrictif

3. **`easacompliance/scripts/build_embeddings.py`** (lignes 22-96, 181-197)
   - Même modifications que ci-dessus

4. **`pyproject.toml`** (ligne 38)
   - Correction du format des entry points pour les scripts

---

## 📝 Scripts de Diagnostic Créés

1. **`scripts/diagnostic_types.py`** - Analyse les TypeOfContent dans le XML
2. **`scripts/diagnostic_db.py`** - Analyse les types dans la base d'embeddings
3. **`scripts/diagnostic_references.py`** - Vérifie l'extraction des références
4. **`scripts/diagnostic_source_titles.py`** - Affiche des exemples de source-title
5. **`scripts/diagnostic_no_reference.py`** - Liste les topics sans référence

---

## 🚀 Utilisation

### Reconstruire la Base Complète

```bash
cd /home/didier/Dev/EASACompliance

# Avec uv run (recommandé)
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_complete_v2.db \
  --clear

# Vérifier le résultat
python scripts/diagnostic_db.py easa_complete_v2.db
```

### Filtrer par Type

```bash
# Uniquement les AMC
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_amc_only.db \
  --types AMC \
  --clear

# IR + AMC + GM
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_full.db \
  --types IR AMC GM_IR \
  --clear
```

---

## ✅ Conclusion

Le parsing des **AMC** (Acceptable Means of Compliance) et des **GM** (Guidance Material) fonctionne désormais correctement. La base de données contient maintenant **7.2 fois plus de topics** qu'avant, offrant une couverture quasi-complète (95.3%) de la réglementation EASA.

**Impact :**
- Recherches sémantiques beaucoup plus riches
- Accès aux moyens de conformité et au matériel d'orientation
- Meilleure compréhension du contexte réglementaire
- Base de données RAG complète et fiable

---

**Date :** 2025-11-15  
**Version :** EASACompliance v2.0.0  
**Statut :** ✅ Résolu

