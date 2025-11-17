# 🔄 Actions de Réorganisation - À Valider

Ce fichier liste toutes les actions à effectuer pour réorganiser le projet.  
**⚠️ VALIDATION REQUISE AVANT EXÉCUTION**

## 📋 Résumé

- **Fichiers à déplacer** : 8
- **Fichiers à supprimer** : 4
- **Fichiers à créer** : 3
- **Fichiers à renommer** : 1

---

## 1️⃣ FICHIERS À DÉPLACER

### Documentation → docs/

```bash
# Chat MCP documentation
mv CHAT_MCP_README.md docs/chat/README.md
mv QUICKSTART_CHAT.md docs/chat/QUICKSTART.md
mv IMPLEMENTATION_SUMMARY.md docs/chat/IMPLEMENTATION.md

# CrewAI documentation
mv COMPLIANCE_CREW_README.md docs/crew/README.md
mv CREW_IMPLEMENTATION_SUMMARY.md docs/crew/IMPLEMENTATION.md

# Project documentation
mv PROJECT_SUMMARY.md docs/PROJECT_SUMMARY.md
```

### Tests → tests/

```bash
mv test_chat_setup.py tests/test_chat_setup.py
mv test_crew_setup.py tests/test_crew_setup.py
```

**Total : 8 fichiers déplacés**

---

## 2️⃣ FICHIERS À SUPPRIMER

### Fichiers temporaires/inutiles

```bash
# Fichier de test temporaire
rm output.md

# Requirements fragmentés (consolidés dans requirements-consolidated.txt)
rm requirements-chat.txt
rm requirements-crew.txt

# Plan de réorganisation (une fois actions effectuées)
rm REORGANIZATION_PLAN.md
```

**Total : 4 fichiers supprimés**

---

## 3️⃣ FICHIERS À RENOMMER

### Requirements consolidé

```bash
# Renommer requirements-consolidated.txt → requirements.txt
# (sauvegarder l'ancien requirements.txt si nécessaire)
mv requirements.txt requirements-old.txt  # Backup
mv requirements-consolidated.txt requirements.txt
```

**Total : 1 fichier renommé**

---

## 4️⃣ FICHIERS CRÉÉS

### ✅ Déjà créés :

1. **install.sh** - Script d'installation moderne avec uv
2. **requirements-consolidated.txt** - Requirements consolidés
3. **REORGANIZATION_PLAN.md** - Plan détaillé
4. **REORGANIZATION_ACTIONS.md** - Ce fichier

### Structure docs/ créée :

```
docs/
├── chat/           # Documentation Chat MCP
├── crew/           # Documentation CrewAI
├── mcp/            # Documentation MCP Server (existant)
└── parser/         # Documentation Parser (existant)
```

---

## 5️⃣ FICHIERS À METTRE À JOUR

### README.md principal

Ajouter une section "Structure du projet" avec la nouvelle organisation :

```markdown
## 📁 Structure du Projet

```
EASACompliance/
├── chat_mcp.py                    # Chat CLI avec LLMs
├── compliance_crew.py             # Audit CrewAI
├── run_mcp_server.py              # Serveur MCP
├── install.sh                     # Installation (uv)
├── requirements.txt               # Dépendances
├── easacompliance/                # Package principal
├── mcp_server_easa/               # MCP server
├── docs/                          # Documentation
│   ├── chat/                      # Docs Chat MCP
│   ├── crew/                      # Docs CrewAI
│   ├── mcp/                       # Docs MCP Server
│   └── parser/                    # Docs Parser
├── tests/                         # Tests
└── examples/                      # Exemples
```
```

### .gitignore

Ajouter si pas déjà présent :

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Virtual environments
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
.env
*.db-journal
output.md
*.md.bak
requirements-old.txt

# Build
dist/
build/
*.egg-info/
```

---

## 📊 AVANT / APRÈS

### Structure racine AVANT (16 fichiers)

```
✅ README.md
✅ pyproject.toml
✅ uv.lock
✅ env.example
✅ easa_complete.db
✅ run_mcp_server.py
✅ chat_mcp.py
✅ compliance_crew.py
❌ requirements.txt (à remplacer)
❌ requirements-chat.txt
❌ requirements-crew.txt
❌ test_chat_setup.py
❌ test_crew_setup.py
❌ CHAT_MCP_README.md
❌ COMPLIANCE_CREW_README.md
❌ QUICKSTART_CHAT.md
❌ IMPLEMENTATION_SUMMARY.md
❌ CREW_IMPLEMENTATION_SUMMARY.md
❌ PROJECT_SUMMARY.md
❌ output.md
```

### Structure racine APRÈS (9 fichiers) ✨

```
✅ README.md
✅ pyproject.toml
✅ uv.lock
✅ requirements.txt (consolidé)
✅ install.sh (nouveau)
✅ env.example
✅ easa_complete.db
✅ run_mcp_server.py
✅ chat_mcp.py
✅ compliance_crew.py
```

**Réduction : 16 → 9 fichiers (-44%)**

---

## 🚀 SCRIPT D'EXÉCUTION (une fois validé)

```bash
#!/bin/bash
# reorganize.sh - Execute reorganization actions

set -e

echo "🔄 Starting reorganization..."

# 1. Create docs structure
echo "📁 Creating docs structure..."
mkdir -p docs/chat docs/crew

# 2. Move documentation
echo "📚 Moving documentation files..."
mv CHAT_MCP_README.md docs/chat/README.md
mv QUICKSTART_CHAT.md docs/chat/QUICKSTART.md
mv IMPLEMENTATION_SUMMARY.md docs/chat/IMPLEMENTATION.md
mv COMPLIANCE_CREW_README.md docs/crew/README.md
mv CREW_IMPLEMENTATION_SUMMARY.md docs/crew/IMPLEMENTATION.md
mv PROJECT_SUMMARY.md docs/PROJECT_SUMMARY.md

# 3. Move tests
echo "🧪 Moving test files..."
mv test_chat_setup.py tests/test_chat_setup.py
mv test_crew_setup.py tests/test_crew_setup.py

# 4. Consolidate requirements
echo "📦 Consolidating requirements..."
mv requirements.txt requirements-old.txt
mv requirements-consolidated.txt requirements.txt

# 5. Remove obsolete files
echo "🗑️  Removing obsolete files..."
rm -f output.md
rm -f requirements-chat.txt
rm -f requirements-crew.txt

echo "✅ Reorganization complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Review the changes: git status"
echo "  2. Test installation: ./install.sh"
echo "  3. Update README.md with new structure"
echo "  4. Commit changes: git add . && git commit -m 'refactor: reorganize project structure'"
```

---

## ⚠️ POINTS D'ATTENTION

### Avant d'exécuter :

1. **Sauvegarder** : Faire un commit git ou backup
2. **Vérifier** : Aucun fichier important n'est ouvert dans l'IDE
3. **Tester** : Vérifier que les imports dans les scripts ne cassent pas

### Après exécution :

1. **Tester l'installation** : `./install.sh`
2. **Tester les scripts** :
   ```bash
   python chat_mcp.py --help
   python compliance_crew.py --help
   ```
3. **Vérifier la doc** : S'assurer que tous les liens relatifs fonctionnent
4. **Mettre à jour README.md** : Ajouter la nouvelle structure

---

## 🎯 VALIDATION

✅ **Je valide la réorganisation** → Exécuter le script `reorganize.sh`  
❌ **J'annule** → Supprimer ce fichier et REORGANIZATION_PLAN.md

---

**Créé le** : 2025-11-17  
**Statut** : ⏳ En attente de validation

