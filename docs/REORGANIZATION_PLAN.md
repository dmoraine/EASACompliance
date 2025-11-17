# 📋 Plan de Réorganisation - EASACompliance

## Structure actuelle (problématique)

```
EASACompliance/
├── README.md ✅
├── pyproject.toml ✅
├── requirements.txt
├── requirements-chat.txt ❌ (fragmenté)
├── requirements-crew.txt ❌ (fragmenté)
├── chat_mcp.py ⚠️ (racine encombrée)
├── compliance_crew.py ⚠️ (racine encombrée)
├── test_chat_setup.py ❌ (devrait être dans tests/)
├── test_crew_setup.py ❌ (devrait être dans tests/)
├── CHAT_MCP_README.md ❌ (devrait être dans docs/)
├── COMPLIANCE_CREW_README.md ❌ (devrait être dans docs/)
├── QUICKSTART_CHAT.md ❌ (devrait être dans docs/)
├── IMPLEMENTATION_SUMMARY.md ❌ (devrait être dans docs/)
├── CREW_IMPLEMENTATION_SUMMARY.md ❌ (devrait être dans docs/)
├── PROJECT_SUMMARY.md ❌ (devrait être dans docs/)
├── output.md ❌ (fichier temporaire à supprimer)
└── ... (autres dossiers OK)
```

## Structure cible (propre)

```
EASACompliance/
├── README.md                        # Documentation principale
├── pyproject.toml                   # Config moderne Python (uv/pip)
├── uv.lock                          # Lock file uv
├── requirements.txt                 # Requirements consolidés (fallback)
├── install.sh                       # Script d'installation avec uv
├── env.example                      # Template configuration
├── easa_complete.db                 # Base de données
│
├── chat_mcp.py                      # ✅ Script CLI principal (reste racine)
├── compliance_crew.py               # ✅ Script CLI principal (reste racine)
├── run_mcp_server.py                # ✅ Entry point MCP (reste racine)
│
├── easacompliance/                  # Package principal
│   ├── __init__.py
│   ├── parser.py
│   ├── embeddings.py
│   └── scripts/
│       ├── build_embeddings.py
│       └── search_regulations.py
│
├── mcp_server_easa/                 # MCP server package
│   ├── __init__.py
│   ├── server.py
│   ├── config.py
│   ├── schemas.py
│   └── tools/
│
├── docs/                            # 📚 Toute la documentation
│   ├── chat/                        # Docs Chat MCP
│   │   ├── README.md
│   │   └── QUICKSTART.md
│   ├── crew/                        # Docs CrewAI
│   │   ├── README.md
│   │   └── IMPLEMENTATION.md
│   ├── mcp/                         # Docs MCP Server
│   │   ├── SETUP.md
│   │   └── GUIDE.md
│   ├── parser/                      # Docs Parser
│   │   └── ...
│   └── PROJECT_SUMMARY.md
│
├── tests/                           # 🧪 Tous les tests
│   ├── __init__.py
│   ├── test_embeddings.py
│   ├── test_chat_setup.py           # Déplacé
│   └── test_crew_setup.py           # Déplacé
│
├── examples/                        # Exemples
│   ├── mcp_client_test.py
│   └── config/
│
├── scripts/                         # Scripts utilitaires
│   └── setup_cursor_mcp.py
│
├── tools/                           # Outils de diagnostic
│   └── diagnostics/
│
└── data/                            # Données de référence
    └── EASA-eRules-XML-Export-Schema-1.0.0.xsd
```

## 🔄 Actions à effectuer

### 1. Consolider requirements.txt

Fusionner `requirements.txt`, `requirements-chat.txt`, `requirements-crew.txt` en un seul avec sections optionnelles.

### 2. Créer install.sh (uv)

Script moderne d'installation utilisant `uv` pour rapidité et gestion moderne.

### 3. Réorganiser la documentation

**Déplacer dans docs/** :
- `CHAT_MCP_README.md` → `docs/chat/README.md`
- `QUICKSTART_CHAT.md` → `docs/chat/QUICKSTART.md`
- `IMPLEMENTATION_SUMMARY.md` → `docs/chat/IMPLEMENTATION.md`
- `COMPLIANCE_CREW_README.md` → `docs/crew/README.md`
- `CREW_IMPLEMENTATION_SUMMARY.md` → `docs/crew/IMPLEMENTATION.md`
- `PROJECT_SUMMARY.md` → `docs/PROJECT_SUMMARY.md`

**Garder dans docs/** (déjà bien placés) :
- Tous les fichiers existants dans `docs/`

### 4. Réorganiser les tests

**Déplacer dans tests/** :
- `test_chat_setup.py` → `tests/test_chat_setup.py`
- `test_crew_setup.py` → `tests/test_crew_setup.py`

### 5. Fichiers à SUPPRIMER

- `output.md` - fichier de test temporaire
- `requirements-chat.txt` - consolidé dans requirements.txt
- `requirements-crew.txt` - consolidé dans requirements.txt
- `__pycache__/` à la racine - devrait être ignoré

### 6. Mettre à jour .gitignore

Ajouter :
```
__pycache__/
*.pyc
*.pyo
*.db-journal
output.md
*.md.bak
.env
.venv/
venv/
```

## 📦 Nouveau requirements.txt consolidé

```txt
# EASA Compliance - Consolidated Requirements
# Install all: pip install -r requirements.txt
# Or with uv: uv pip install -r requirements.txt

# ============================================================================
# CORE - Parser et embeddings EASA
# ============================================================================
sentence-transformers>=2.2.0
torch>=2.0.0
numpy>=1.24.0
tqdm>=4.65.0

# ============================================================================
# MCP - Model Context Protocol
# ============================================================================
mcp>=1.0.0

# ============================================================================
# CHAT - Chat MCP Client (chat_mcp.py)
# ============================================================================
openai>=1.0.0
python-dotenv>=1.0.0

# ============================================================================
# CREW - CrewAI Compliance Validator (compliance_crew.py)
# ============================================================================
crewai>=0.30.0
crewai-tools>=0.2.0
markdown>=3.5.0

# ============================================================================
# OPTIONAL - Development tools
# ============================================================================
# pytest>=7.0.0
# black>=23.0.0
# ruff>=0.1.0
```

## 🚀 Script d'installation (install.sh)

```bash
#!/bin/bash
# Installation script using uv (modern Python package installer)

set -e

echo "🚀 EASA Compliance - Installation"
echo "=================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv found: $(uv --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
uv pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate environment: source .venv/bin/activate"
echo "   2. Configure .env: cp env.example .env"
echo "   3. Build database: python easacompliance/scripts/build_embeddings.py ..."
echo "   4. Test chat: python chat_mcp.py --provider ollama"
echo ""
```

## 📊 Résumé des changements

### Fichiers déplacés : 8
- 6 fichiers MD → docs/
- 2 fichiers test → tests/

### Fichiers supprimés : 3
- output.md
- requirements-chat.txt
- requirements-crew.txt

### Fichiers créés : 2
- requirements.txt (consolidé)
- install.sh (script uv)

### Résultat
**Avant** : 16 fichiers à la racine  
**Après** : 7 fichiers à la racine (README, pyproject, requirements, install, env.example, 3 scripts CLI)

### Bénéfices
✅ Racine propre et claire  
✅ Structure standard Python  
✅ Documentation organisée  
✅ Installation moderne (uv)  
✅ Requirements consolidés  
✅ Maintenance facilitée  

