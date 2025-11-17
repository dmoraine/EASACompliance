# 🚀 Serveur MCP EASA

Serveur MCP (Model Context Protocol) exposant les régulations EASA à n'importe quel LLM compatible.

## 🎯 Quick Start

```bash
# 1. Installer les dépendances
uv add mcp

# 2. Construire la base de données (si pas déjà fait)
uv run python easacompliance/scripts/build_embeddings.py \
  --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
  --db easa_complete.db \
  --clear

# 3. Tester le serveur
export EASA_DB_PATH="easa_complete.db"
python examples/mcp_client_test.py
```

## 📦 6 Tools Disponibles

1. **`search_regulations`** - Recherche sémantique
2. **`get_regulation`** - Récupérer une régulation par référence
3. **`get_regulatory_chain`** - IR + AMC + GM associés
4. **`list_categories`** - Liste des catégories
5. **`get_statistics`** - Statistiques de la base
6. **`validate_compliance`** - Validation de conformité

## 🔧 Configuration Claude Desktop

Ajouter à `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "easa-regulations": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp_server_easa/server.py"],
      "env": {
        "EASA_DB_PATH": "/path/to/easa_complete.db"
      }
    }
  }
}
```

## 📚 Documentation Complète

Voir [`docs/MCP_SERVER_GUIDE.md`](../docs/MCP_SERVER_GUIDE.md) pour :
- Architecture détaillée
- Schémas des tools
- Exemples d'usage
- Dépannage

## 🏗️ Structure

```
mcp_server_easa/
├── server.py          # Serveur MCP principal
├── config.py          # Configuration
├── schemas.py         # Schémas de données
└── tools/             # Tools MCP
    ├── search.py      # Recherche sémantique
    ├── retrieve.py    # Récupération de régulations
    ├── browse.py      # Navigation et stats
    └── validate.py    # Validation de conformité
```

## ✅ Tests

```bash
# Tester tous les tools
python examples/mcp_client_test.py

# Attendu:
# ✅ 6 tools disponibles
# ✅ Tous les tests réussis
```

---

**Version** : 1.0.0  
**Status** : 🟢 Production Ready

