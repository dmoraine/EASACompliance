# Chat MCP Client - EASA Regulations

Script CLI interactif pour chatter avec des LLMs (OpenAI, Ollama, Hyperbolic) connecté au serveur MCP easa-regulations.

## 🚀 Installation

### 1. Installer les dépendances

```bash
# Dépendances principales (si pas déjà installé)
pip install -r requirements.txt

# Dépendances pour le chat client
pip install -r requirements-chat.txt
```

Ou avec `uv` :

```bash
uv pip install -r requirements.txt
uv pip install -r requirements-chat.txt
```

### 2. Configurer les LLM providers

Copiez le fichier de configuration :

```bash
cp env.example .env
```

Éditez le fichier `.env` et remplissez vos clés API :

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Ollama (local, pas besoin de clé)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b

# Hyperbolic
HYPERBOLIC_API_KEY=your-key-here
HYPERBOLIC_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
```

**Note** : Vous n'avez pas besoin de configurer tous les providers, seulement ceux que vous souhaitez utiliser.

## 📖 Utilisation

### Lancement du script

**Mode interactif** (sélection du provider au démarrage) :

```bash
python chat_mcp.py
```

**Avec provider spécifié** :

```bash
# Utiliser OpenAI
python chat_mcp.py --provider openai

# Utiliser Ollama (local)
python chat_mcp.py --provider ollama

# Utiliser Hyperbolic
python chat_mcp.py --provider hyperbolic
```

### Commandes disponibles dans le chat

Une fois le chat lancé, vous pouvez utiliser ces commandes :

- `/quit` ou `/exit` - Quitter le chat
- `/tools` - Lister les outils MCP disponibles
- `/help` - Afficher l'aide
- `/provider` - Information pour changer de provider (nécessite un redémarrage)

### Exemples de requêtes

Le script supporte le **function calling** automatique avec le serveur MCP. Voici des exemples :

```
You: What are the flight time limitations for crew members?

You: Search for regulations about duty time requirements

You: Get me the full text of ORO.FTL.110

You: What regulations are related to rest periods?

You: Validate this text: "Flight crew members must not exceed 900 hours in a calendar year"
```

Le LLM peut automatiquement appeler les outils MCP disponibles :
- `search_regulations` - Recherche sémantique dans les régulations
- `get_regulation` - Récupérer une régulation spécifique
- `get_regulatory_chain` - Obtenir la chaîne réglementaire complète
- `list_categories` - Lister les catégories de régulations
- `get_statistics` - Obtenir des statistiques sur la base
- `validate_compliance` - Valider la conformité d'un texte

## 🔧 Configuration avancée

### Variables d'environnement MCP

Le script utilise également ces variables pour configurer le serveur MCP :

```bash
EASA_DB_PATH=easa_complete.db
EASA_MODEL=all-MiniLM-L6-v2
EASA_MAX_RESULTS=20
EASA_CACHE=true
```

### Utiliser un autre modèle

Éditez simplement la variable correspondante dans `.env` :

```bash
# Pour OpenAI
OPENAI_MODEL=gpt-4-turbo

# Pour Ollama
OLLAMA_MODEL=mistral:7b

# Pour Hyperbolic
HYPERBOLIC_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
```

## 🎯 Fonctionnalités

✅ **Multi-provider** : Support OpenAI, Ollama (local), Hyperbolic
✅ **Streaming** : Réponses en temps réel
✅ **Function calling** : Le LLM peut appeler automatiquement les outils MCP
✅ **Interface simple** : CLI minimaliste pour POC
✅ **Configuration flexible** : Plusieurs providers dans un seul .env

## 🐛 Dépannage

### "Database not found"

Assurez-vous d'avoir créé la base de données :

```bash
python easacompliance/scripts/build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --db "easa_complete.db" \
    --clear
```

### "Provider not configured"

Vérifiez que vous avez bien rempli les variables d'environnement dans `.env` pour le provider sélectionné.

### Ollama ne fonctionne pas

Assurez-vous qu'Ollama est lancé :

```bash
# Vérifier si Ollama tourne
curl http://localhost:11434/v1/models

# Lancer Ollama si nécessaire
ollama serve
```

### Erreur de connexion MCP

Vérifiez que :
1. Le fichier `run_mcp_server.py` existe
2. La base de données `easa_complete.db` existe
3. Les dépendances MCP sont installées (`pip install mcp`)

## 📝 Architecture

Le script est composé de :

1. **ConfigManager** : Gestion de la configuration des providers
2. **MCPClient** : Client pour interagir avec le serveur MCP EASA
3. **UnifiedLLMClient** : Client unifié pour les APIs compatibles OpenAI
4. **ChatMCPApp** : Application principale avec boucle interactive

## 🔗 Liens utiles

- [Documentation MCP](https://modelcontextprotocol.io/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Ollama](https://ollama.ai/)
- [Hyperbolic](https://hyperbolic.xyz/)

## 📄 Licence

MIT License - Voir le fichier LICENSE du projet principal.

