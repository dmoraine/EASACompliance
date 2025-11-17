# 🔧 Outils de Diagnostic EASA

Ce dossier contient des scripts de diagnostic utilisés pour analyser et déboguer le parsing des fichiers XML EASA et les bases de données d'embeddings.

## 📋 Scripts Disponibles

### 1. `diagnostic_types.py`
Analyse les valeurs de `TypeOfContent` présentes dans le XML EASA.

**Usage :**
```bash
python tools/diagnostics/diagnostic_types.py "path/to/xml/file.xml"
```

**Sortie :**
- Liste de toutes les valeurs de TypeOfContent trouvées
- Comparaison avec les valeurs attendues par le parser
- Identification des valeurs non reconnues

---

### 2. `diagnostic_db.py`
Analyse les types de topics stockés dans une base d'embeddings.

**Usage :**
```bash
python tools/diagnostics/diagnostic_db.py "path/to/database.db"
```

**Sortie :**
- Répartition par type de topic
- Statistiques de contenu
- Échantillons de métadonnées

---

### 3. `diagnostic_references.py`
Vérifie quels types de topics ont des références extraites par le parser.

**Usage :**
```bash
python tools/diagnostics/diagnostic_references.py "path/to/xml/file.xml"
```

**Sortie :**
- Statistiques de références par type
- Pourcentage de topics avec/sans référence
- Exemples de références extraites

---

### 4. `diagnostic_source_titles.py`
Affiche des exemples de `source-title` pour chaque type de topic.

**Usage :**
```bash
python tools/diagnostics/diagnostic_source_titles.py "path/to/xml/file.xml"
```

**Sortie :**
- Exemples de source-title par type
- Analyse de l'extraction de références
- Aide pour déboguer les patterns regex

---

### 5. `diagnostic_no_reference.py`
Liste les topics qui n'ont pas de référence extraite.

**Usage :**
```bash
python tools/diagnostics/diagnostic_no_reference.py "path/to/xml/file.xml"
```

**Sortie :**
- Topics sans référence par type
- Exemples avec titre et contenu
- Aide pour identifier les patterns manquants

---

### 6. `diagnostic_compare.py`
Compare deux bases de données d'embeddings.

**Usage :**
```bash
python tools/diagnostics/diagnostic_compare.py "base1.db" "base2.db"
```

**Sortie :**
- Comparaison détaillée par type
- Différences de contenu
- Statistiques de gain/perte

---

## 🎯 Cas d'Usage

### Déboguer l'extraction de références
```bash
# 1. Voir les source-titles originaux
python tools/diagnostics/diagnostic_source_titles.py "regulations.xml"

# 2. Vérifier l'extraction
python tools/diagnostics/diagnostic_references.py "regulations.xml"

# 3. Identifier les topics sans référence
python tools/diagnostics/diagnostic_no_reference.py "regulations.xml"
```

### Vérifier une base d'embeddings
```bash
# 1. Analyser le contenu
python tools/diagnostics/diagnostic_db.py "embeddings.db"

# 2. Comparer avec le XML source
python tools/diagnostics/diagnostic_types.py "regulations.xml"
```

### Comparer deux versions
```bash
# Avant/après une modification du parser
python tools/diagnostics/diagnostic_compare.py "old.db" "new.db"
```

---

## 📝 Notes

Ces outils ont été créés lors de la résolution du problème de parsing des AMC et GM (voir `docs/RAPPORT_CORRECTION_AMC_GM.md`). 

Ils restent disponibles pour :
- Déboguer de futurs problèmes de parsing
- Analyser de nouveaux fichiers XML EASA
- Valider les bases d'embeddings
- Comparer différentes versions

**Note :** Ces scripts nécessitent que le package `easacompliance` soit installé en mode développement (`uv pip install -e .`).

