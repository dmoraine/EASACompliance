# 🚀 Démarrage Rapide - Chat MCP Client

Guide rapide pour utiliser le chat MCP avec les régulations EASA.

## ⚡ Installation en 3 étapes

### 1. Installer les dépendances

```bash
pip install -r requirements-chat.txt
```

### 2. Configurer les providers

```bash
# Copier le template
cp env.example .env

# Éditer avec vos clés API
nano .env  # ou vim, code, etc.
```

**Configuration minimale pour tester** (avec Ollama local) :

```bash
# Pas besoin de clés API pour Ollama !
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
```

### 3. Lancer le chat

```bash
# Avec Ollama (local, pas de clé nécessaire)
python chat_mcp.py --provider ollama

# Ou mode interactif pour choisir le provider
python chat_mcp.py
```

## 🎯 Exemples d'utilisation

### Recherche simple

```
You: What are the flight time limitations?

# Le LLM va automatiquement appeler search_regulations()
# et vous donner une réponse basée sur les régulations EASA
```

### Récupération d'une régulation spécifique

```
You: Get me the full text of ORO.FTL.110

# Le LLM va appeler get_regulation("ORO.FTL.110")
```

### Validation de conformité

```
You: Validate this text: "Flight crew members must not exceed 900 hours in a calendar year"

# Le LLM va appeler validate_compliance() avec votre texte
```

### Questions complexes

```
You: What regulations apply to rest periods for long-haul flights?

# Le LLM peut combiner plusieurs appels d'outils pour répondre
```

## 🔧 Configuration des providers

### OpenAI

```bash
OPENAI_API_KEY=sk-votre-cle-ici
OPENAI_MODEL=gpt-4o
```

### Ollama (Local - RECOMMANDÉ pour tester)

```bash
# 1. Installer Ollama: https://ollama.ai/
# 2. Télécharger un modèle
ollama pull llama3.1:8b

# 3. Lancer Ollama
ollama serve

# 4. Dans .env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
```

### Hyperbolic

```bash
HYPERBOLIC_API_KEY=votre-cle-ici
HYPERBOLIC_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
```

## 📋 Commandes dans le chat

- `/quit` - Quitter
- `/tools` - Lister les outils MCP disponibles
- `/help` - Afficher l'aide
- `/provider` - Info sur le changement de provider

## ✅ Vérifier l'installation

```bash
python test_chat_setup.py
```

Ce script vérifie :
- ✅ Imports et dépendances
- ✅ Configuration des providers
- ✅ Base de données EASA
- ✅ Serveur MCP

## 🎬 Workflow typique

1. **Lancer le chat** : `python chat_mcp.py --provider ollama`
2. **Poser une question** : Le LLM appelle automatiquement les outils MCP si nécessaire
3. **Voir le résultat** : Réponse streamée en temps réel avec citations réglementaires

## 🐛 Problèmes courants

### "Database not found"

```bash
python easacompliance/scripts/build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --db "easa_complete.db" \
    --clear
```

### "Provider not configured"

Vérifiez votre fichier `.env` et assurez-vous d'avoir les bonnes clés API.

### Ollama ne répond pas

```bash
# Vérifier qu'Ollama tourne
curl http://localhost:11434/v1/models

# Redémarrer si nécessaire
ollama serve
```

## 📚 Documentation complète

- [CHAT_MCP_README.md](CHAT_MCP_README.md) - Documentation complète
- [env.example](env.example) - Template de configuration
- [test_chat_setup.py](test_chat_setup.py) - Script de test

## 💡 Astuce

Pour un test rapide sans clé API, utilisez **Ollama** en local :

```bash
# Installation en une ligne (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Lancer Ollama et télécharger un modèle
ollama serve &
ollama pull llama3.1:8b

# Tester le chat
python chat_mcp.py --provider ollama
```

Puis posez une question comme :
```
You: Search for regulations about crew rest requirements
```

Le LLM va automatiquement utiliser le serveur MCP pour chercher dans les régulations EASA ! 🎉
