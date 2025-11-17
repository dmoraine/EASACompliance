# CrewAI Compliance Validator - EASA Regulations

Script CLI utilisant CrewAI avec une équipe de 2 agents (Auditeur + QA Challenger) pour valider la compliance d'un texte avec les régulations EASA via le serveur MCP.

## 🎯 Objectif

Auditer automatiquement la conformité de textes opérationnels (manuels, procédures, politiques) avec les régulations EASA en utilisant une équipe d'agents IA qui collaborent et se challengent mutuellement.

## ✨ Fonctionnalités

- 🤖 **2 Agents spécialisés** : Auditeur expert + Challenger QA
- 🔍 **Audit complet** : Identification de tous les manquements réglementaires
- ✅ **Validation croisée** : Le QA challenge et vérifie les findings de l'auditeur
- 📋 **Rapport détaillé** : Format Markdown avec références exactes et recommandations
- 🔧 **Accès MCP** : Les agents utilisent les tools du serveur MCP EASA
- 🌐 **Multi-providers** : Support OpenAI, Ollama, Hyperbolic
- 💬 **Modes multiples** : Texte direct, fichier, ou interactif

## 📦 Installation

### 1. Installer les dépendances

```bash
# Dépendances de base (si pas déjà installées)
pip install -r requirements.txt
pip install -r requirements-chat.txt

# Dépendances CrewAI
pip install -r requirements-crew.txt
```

Ou avec `uv` :

```bash
uv pip install -r requirements.txt
uv pip install -r requirements-chat.txt
uv pip install -r requirements-crew.txt
```

### 2. Configuration

Utilisez le même fichier `.env` que pour `chat_mcp.py` :

```bash
# Si pas encore fait
cp env.example .env
# Éditer avec vos clés API
```

Configuration minimale :

```bash
# OpenAI (recommandé pour CrewAI)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Ou Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
```

## 🚀 Utilisation

### Mode texte direct

```bash
python compliance_crew.py \
  --text "Flight crew members must not exceed 900 hours in a calendar year" \
  --output report.md \
  --provider openai
```

### Mode fichier

```bash
python compliance_crew.py \
  --file operations_manual.txt \
  --output compliance_report.md \
  --provider openai
```

### Mode interactif

```bash
python compliance_crew.py \
  --interactive \
  --output report.md

# Puis entrez votre texte, terminez avec END ou Ctrl+D
```

### Options disponibles

```bash
python compliance_crew.py --help

Options:
  --text TEXT         Texte à auditer (ligne de commande)
  --file FILE         Fichier contenant le texte à auditer
  --interactive       Mode interactif (entrer le texte au clavier)
  --output OUTPUT     Fichier de sortie pour le rapport (obligatoire)
  --provider PROVIDER Provider LLM (openai, ollama, hyperbolic)
  --quiet             Réduire la verbosité (moins de logs des agents)
  --db DB             Chemin vers la base EASA (défaut: easa_complete.db)
```

## 🤖 Architecture de l'équipe

### Agent 1: Compliance Auditor

**Rôle** : Auditeur senior EASA avec 15+ ans d'expérience

**Responsabilités** :
- Analyser le texte de manière méthodique
- Identifier tous les manquements réglementaires
- Citer les références exactes des régulations
- Évaluer la criticité (HIGH/MEDIUM/LOW)
- Proposer des actions correctives

**Tools disponibles** :
- `search_easa_regulations` : Recherche sémantique
- `get_easa_regulation` : Récupération d'une régulation
- `get_regulatory_chain` : Chaîne réglementaire complète
- `list_easa_categories` : Liste des catégories
- `validate_text_compliance` : Validation automatique
- `get_easa_statistics` : Statistiques de la base

### Agent 2: Quality Assurance Challenger

**Rôle** : Expert QA critique qui challenge l'auditeur

**Responsabilités** :
- Vérifier chaque finding de l'auditeur
- Contre-vérifier les références réglementaires
- Identifier les findings incorrects ou manquants
- Ajuster les niveaux de criticité si nécessaire
- Valider ou rejeter chaque finding avec preuves

**Tools disponibles** : Les mêmes que l'auditeur

### Workflow (3 Tasks séquentielles)

```
1. AUDIT TASK (Auditor)
   │
   ├─ Analyse du texte
   ├─ Recherche des régulations applicables
   ├─ Identification des manquements
   └─ Output: Liste des findings avec références
   │
   ↓
2. CHALLENGE TASK (QA Challenger)
   │
   ├─ Review de chaque finding
   ├─ Vérification des références
   ├─ Identification de findings manquants
   └─ Output: Validation + Critique + Ajouts
   │
   ↓
3. FINAL REPORT TASK (Auditor + QA)
   │
   ├─ Consolidation des findings validés
   ├─ Résolution des désaccords
   ├─ Organisation par criticité
   └─ Output: Rapport Markdown complet
```

## 📄 Format du rapport

Le rapport généré est un document Markdown structuré :

```markdown
# EASA Compliance Audit Report

## Executive Summary
- Date et heure d'analyse
- Texte analysé (extrait)
- Nombre total de manquements
- Répartition par criticité (HIGH/MEDIUM/LOW)
- Évaluation globale de la conformité

## Detailed Findings

### HIGH CRITICALITY FINDINGS

#### Finding 1: [Titre du manquement]
- **Criticality**: HIGH
- **Regulation Reference**: ORO.FTL.110
- **Text Excerpt**: "[citation du texte audité]"
- **Issue Description**: [Description du problème]
- **Regulatory Requirement**: [Citation exacte de la régulation]
- **Recommendation**: [Action corrective recommandée]
- **QA Validation**: Confirmed

### MEDIUM CRITICALITY FINDINGS
[...]

### LOW CRITICALITY FINDINGS
[...]

## Applicable Regulations Summary
Liste de toutes les régulations EASA référencées

## Recommendations Summary
Actions prioritaires recommandées

## Conclusion
Évaluation globale et prochaines étapes
```

## 💡 Exemples concrets

### Exemple 1: Validation d'une limite de temps de vol

```bash
python compliance_crew.py \
  --text "Flight crew members shall not exceed 1000 flight hours in any consecutive 12 months" \
  --output ftl_audit.md \
  --provider openai
```

**Résultat attendu** : Le système identifiera que la limite EASA est de 900 heures (ORO.FTL.210), pas 1000.

### Exemple 2: Audit d'un manuel d'opérations

```bash
python compliance_crew.py \
  --file operations_manual_chapter3.txt \
  --output ops_manual_audit.md \
  --provider openai
```

**Résultat attendu** : Rapport complet listant tous les manquements du chapitre.

### Exemple 3: Mode interactif

```bash
python compliance_crew.py --interactive --output my_audit.md

# Entrez votre texte :
Pilots must have a minimum rest of 8 hours between duty periods.
The maximum duty time is 14 hours for single pilot operations.
END

# Le système va analyser et générer le rapport
```

## 🔧 Configuration avancée

### Verbosité

Par défaut, le script affiche tous les logs des agents (utile pour voir leur raisonnement) :

```bash
# Mode verbeux (défaut)
python compliance_crew.py --text "..." --output report.md

# Mode silencieux
python compliance_crew.py --text "..." --output report.md --quiet
```

### Choix du provider

```bash
# OpenAI (recommandé pour meilleure qualité)
python compliance_crew.py --text "..." --output report.md --provider openai

# Ollama (local, gratuit mais moins performant)
python compliance_crew.py --text "..." --output report.md --provider ollama

# Hyperbolic (économique)
python compliance_crew.py --text "..." --output report.md --provider hyperbolic
```

### Base de données EASA

```bash
# Utiliser une autre base
python compliance_crew.py \
  --text "..." \
  --output report.md \
  --db custom_easa.db
```

## ⚠️ Points importants

### Coûts LLM

CrewAI avec 2 agents et 3 tasks = plusieurs appels LLM :
- ~10-20 appels pour un texte court
- ~30-50 appels pour un texte long
- Coût estimé avec GPT-4: $0.50 - $2.00 par audit

💡 **Astuce** : Utilisez Ollama (local) pour tester sans coûts.

### Temps d'exécution

- Texte court (< 500 mots) : 2-5 minutes
- Texte moyen (500-2000 mots) : 5-15 minutes  
- Texte long (> 2000 mots) : 15-30 minutes

Le temps dépend du provider et de la complexité du texte.

### Qualité des résultats

**Meilleurs résultats** :
- ✅ OpenAI GPT-4 : Très précis, bonnes citations
- ✅ OpenAI GPT-4o : Bon compromis qualité/vitesse
- ⚠️ Ollama Llama 3.1 70B+ : Correct mais nécessite vérification
- ❌ Ollama Llama 3.1 8B : Trop petit, résultats inconsistants

## 🐛 Dépannage

### "Database not found"

```bash
python easacompliance/scripts/build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --db "easa_complete.db" \
    --clear
```

### "Provider not configured"

Vérifiez votre `.env` :

```bash
cat .env | grep OPENAI_API_KEY
# Devrait afficher votre clé (pas vide)
```

### "MCP server connection failed"

Vérifiez que :
1. Le fichier `run_mcp_server.py` existe
2. La base `easa_complete.db` existe
3. Les dépendances MCP sont installées

### Erreur CrewAI

Si CrewAI plante :

```bash
# Réinstaller CrewAI
pip uninstall crewai crewai-tools -y
pip install crewai>=0.30.0 crewai-tools>=0.2.0
```

### Ollama ne répond pas

```bash
# Vérifier qu'Ollama tourne
curl http://localhost:11434/v1/models

# Redémarrer si nécessaire
ollama serve
```

## 📊 Comparaison avec d'autres outils

| Outil | Approche | Avantages | Inconvénients |
|-------|----------|-----------|---------------|
| **compliance_crew.py** | Multi-agents (2 agents qui se challengent) | ✅ Validation croisée<br>✅ Findings de haute qualité<br>✅ Rapport structuré | ❌ Plus lent<br>❌ Coûts LLM plus élevés |
| **chat_mcp.py** | Chat interactif simple | ✅ Rapide<br>✅ Flexible | ❌ Pas de validation croisée<br>❌ Rapport manuel |
| **search_regulations.py** | Recherche sémantique | ✅ Très rapide<br>✅ Gratuit | ❌ Pas d'analyse de compliance<br>❌ Pas de rapport |

## 🔗 Liens utiles

- [Documentation CrewAI](https://docs.crewai.com/)
- [Documentation MCP](https://modelcontextprotocol.io/)
- [EASA eRules](https://www.easa.europa.eu/en/document-library/easy-access-rules)

## 📝 Exemples de sorties

Voir le dossier `examples/` (si disponible) pour des exemples de rapports générés.

## 🎓 Bonnes pratiques

### Préparer le texte à auditer

1. **Texte structuré** : Mieux vaut un texte bien formaté
2. **Longueur raisonnable** : 500-2000 mots = sweet spot
3. **Contexte clair** : Mentionner le contexte opérationnel

### Interpréter les résultats

1. **HIGH criticality** : Nécessite action immédiate (sécurité)
2. **MEDIUM criticality** : Important mais pas urgent
3. **LOW criticality** : Améliorations recommandées

### Vérifier les findings

⚠️ **Important** : Toujours vérifier les findings avec un expert humain !

Les agents font un excellent travail mais peuvent :
- Mal interpréter des régulations ambiguës
- Manquer du contexte opérationnel spécifique
- Sur/sous-estimer la criticité

## 📄 Licence

MIT License - Voir le fichier LICENSE du projet principal.

---

**Version**: 1.0.0  
**Date**: 2025
**Auteur**: EASACompliance Project

