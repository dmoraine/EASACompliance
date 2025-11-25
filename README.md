# EASA Compliance Parser

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Parser and semantic search system for EASA (European Union Aviation Safety Agency) regulations. Optimized for integration with RAG (Retrieval Augmented Generation) systems.

## ✨ Features

- ✅ **Official EASA structure-based parser** : Uses the EASA eRules XML Export XSD schema
- ✅ **3,357+ topics extracted** : Complete access to all regulations (IR, AMC, GM, CS)
- ✅ **Batch processing** : Parse all XML files in a directory automatically
- ✅ **Universal parser** : Automatically detects EASA document location (item2.xml, item9.xml, etc.)
- ✅ **Semantic search** : Embeddings with sentence-transformers for similarity search
- ✅ **Complete metadata** : Dates, regulatory sources, content types
- ✅ **Optimized performance** : SDT indexing in O(n) for fast parsing (~5 seconds)
- ✅ **MCP Server** : Integration with Model Context Protocol for LLMs
- ✅ **Chat Client** : CLI interface to chat with LLMs connected to EASA regulations
- ✅ **CrewAI Compliance** : Automated audit with AI agent team (Auditor + QA)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/dmoraine/easacompliance.git
cd easacompliance

# Install with pip
pip install -e .

# Or with uv (modern and faster)
./install.sh
```

The `install.sh` script uses `uv` for fast dependency resolution and installation.

## 🚀 Quick Start

### 🤖 Chat MCP Client

Interactive CLI interface to chat with LLMs (OpenAI, Ollama, Hyperbolic) connected to EASA regulations via MCP:

```bash
# Configuration
cp env.example .env
# Edit .env with your API keys

# Launch chat
python chat_mcp.py --provider ollama  # Local, no API key needed
python chat_mcp.py --provider openai  # With OpenAI
python chat_mcp.py --provider hyperbolic  # With Hyperbolic
```

**Features**:
- 💬 Interactive chat with streaming responses
- 🔧 Automatic function calling to EASA MCP server
- 🔍 Search, retrieval and regulatory compliance validation
- 🌐 Multi-provider support (OpenAI, local Ollama, Hyperbolic)

👉 [Complete Chat MCP Guide](docs/chat/QUICKSTART.md)

### 🎯 CrewAI Compliance Validator (NEW!)

Automated compliance audit with a team of 2 AI agents (Auditor + QA Challenger) that collaborate and challenge each other:

```bash
# Configuration (same .env as for chat)
cp env.example .env

# Audit a text
python compliance_crew.py \
  --text "Flight crew members must not exceed 900 hours" \
  --output report.md \
  --provider openai

# Audit a file
python compliance_crew.py \
  --file operations_manual.txt \
  --output compliance_report.md \
  --provider openai

# Interactive mode
python compliance_crew.py --interactive --output report.md
```

**Features**:
- 🤖 2 specialized agents: Expert Auditor + QA Challenger
- ✅ Cross-validation: QA challenges and verifies findings
- 📋 Detailed Markdown report with exact EASA references
- 🔍 Non-compliance identification with severity levels
- 🔧 Full access to EASA MCP tools for agents
- 🌐 Multi-provider support (recommended: OpenAI GPT-4)

👉 [Complete CrewAI Compliance Guide](docs/crew/README.md)

### 📊 Building the Embeddings Database

The script supports two modes: **single file** or **directory batch processing**.

#### Single File Mode

```bash
# Parse a single XML file (3,357 topics)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --db easa_complete.db \
    --clear

# Parse only a specific category (e.g., ORO.FTL)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --category "ORO.FTL" \
    --db oro_ftl.db \
    --clear

# Parse only IR (Implementing Rules)
python build_embeddings.py \
    --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
    --types IR \
    --db easa_ir.db \
    --clear
```

#### Directory Batch Mode (NEW!)

Parse all XML files in a directory automatically:

```bash
# Parse all XML files in easy_access/ (default directory)
python build_embeddings.py \
    --db easa_complete.db \
    --clear

# Parse all XML files in a specific directory
python build_embeddings.py \
    --dir easy_access \
    --db easa_complete.db \
    --clear

# Parse all XML files with filters
python build_embeddings.py \
    --dir easy_access \
    --db easa_ir_only.db \
    --types IR \
    --clear
```

**Features**:
- ✅ Automatically detects all `.xml` files in the directory
- ✅ Processes files sequentially with progress tracking
- ✅ Duplicate prevention (UNIQUE constraint on references)
- ✅ Error handling per file (continues if one fails)
- ✅ Detailed summary with statistics per file and final totals

**Note**: The `build_embeddings.py` script at the root is a convenient wrapper to the full implementation in `easacompliance/scripts/build_embeddings.py`. You can also use the module directly: `python -m easacompliance.scripts.build_embeddings` or `python easacompliance/scripts/build_embeddings.py`

### 🔍 Semantic Search

```bash
# Interactive mode
python -m easacompliance.scripts.search_regulations \
    --db "easa_complete.db" \
    --interactive

# Single search
python -m easacompliance.scripts.search_regulations \
    --db "easa_complete.db" \
    --query "flight time limitations" \
    --top-k 5

# Manual compliance validation
python -m easacompliance.scripts.search_regulations \
    --db "easa_complete.db" \
    --manual "operations_manual.txt" \
    --top-k 10 \
    --min-score 0.3
```

**Note**: You can also use the direct path: `python easacompliance/scripts/search_regulations.py`

### 💻 Python Usage

```python
from easacompliance import EASAParser, EmbeddingsManager, TopicType

# Parser
parser = EASAParser("regulations.xml")

# Extract a specific topic
topic = parser.get_topic_by_reference("ORO.FTL.110")
print(f"{topic.reference} - {topic.title}")
print(f"Type: {topic.topic_type.value}")
print(f"Content: {topic.content}")

# Extract all topics from a category
oro_ftl_topics = parser.get_all_topics(pattern=r'^ORO\.FTL\.')
print(f"Found {len(oro_ftl_topics)} ORO.FTL topics")

# Semantic search
manager = EmbeddingsManager("easa_complete.db")
results = manager.search("flight time limitations", top_k=5)

for result in results:
    print(f"{result.reference}: {result.title} (score: {result.score:.3f})")
```

## 📁 Project Structure

```
EASACompliance/              # Project root
├── build_embeddings.py      # Build embeddings database (root script wrapper)
├── chat_mcp.py              # Chat MCP client (root script)
├── compliance_crew.py        # CrewAI compliance validator (root script)
├── run_mcp_server.py        # MCP server launcher (root script)
├── install.sh               # Installation script (uses uv)
├── env.example              # Environment variables template
├── requirements.txt          # Consolidated dependencies
│
├── easacompliance/          # Main package
│   ├── __init__.py          # Public exports
│   ├── parser.py            # EASA parser (EASAParser, Topic, TopicType)
│   ├── embeddings.py        # Embeddings manager (EmbeddingsManager)
│   └── scripts/             # CLI scripts
│       ├── build_embeddings.py
│       └── search_regulations.py
│
├── mcp_server_easa/          # MCP server package
│   ├── server.py            # MCP server implementation
│   ├── config.py            # Configuration
│   ├── schemas.py           # Data schemas
│   └── tools/               # MCP tools
│       ├── search.py
│       ├── retrieve.py
│       ├── browse.py
│       └── validate.py
│
├── tests/                   # Tests
│   ├── test_embeddings.py
│   ├── test_chat_setup.py
│   └── test_crew_setup.py
│
├── docs/                    # Documentation
│   ├── chat/                # Chat MCP documentation
│   │   ├── README.md
│   │   ├── QUICKSTART.md
│   │   └── IMPLEMENTATION.md
│   ├── crew/                # CrewAI documentation
│   │   ├── README.md
│   │   └── IMPLEMENTATION.md
│   ├── EMBEDDINGS_GUIDE.md
│   └── ...
│
├── data/                    # Reference data
│   └── EASA-eRules-XML-Export-Schema-1.0.0.xsd
│
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 📊 Statistics

The parser extracts **3,357+ structured topics** from Air Operations documents:

| Type | Count | Description |
|------|-------|-------------|
| **IR** | 1,025 | Implementing Rules |
| **AMC** | 1,263 | Acceptable Means of Compliance |
| **GM to IR** | 1,026 | Guidance Material to Implementing Rules |
| **CS** | 7 | Certification Specifications |
| **GM to CS** | 18 | Guidance Material to Certification Specifications |
| **Others** | 18 | Easy Access Rules, disclaimers, etc. |

**Note**: Additional topics are extracted from other EASA documents (Aircrew, etc.) when using batch processing mode.

## 🔧 Filtering Options

All filtering options work in both **single file** and **batch directory** modes:

### By category
```bash
--category "ORO.FTL"     # All ORO.FTL.*
--category "CS FTL"      # All CS FTL.*
```

### By content type
```bash
--types IR               # Only Implementing Rules
--types IR AMC           # IR + AMC
--types ALL              # All (default)
```

### By regulatory subject
```bash
--subject "Part-ORO"     # All Part-ORO
--subject "Part-CAT"     # All Part-CAT
```

### By regex pattern
```bash
--pattern "ORO\\.FTL\\." # Custom pattern
```

**Note**: Filters are applied to all files when using batch mode (`--dir`).

## 📚 Documentation

- [Parser Complete Guide](docs/REFONTE_PARSER_RAPPORT.md)
- [Embeddings Guide](docs/EMBEDDINGS_GUIDE.md)
- [Quick Start Guide](docs/QUICKSTART.md)
- [Chat MCP Guide](docs/chat/QUICKSTART.md)
- [CrewAI Compliance Guide](docs/crew/README.md)
- [MCP Server Guide](docs/MCP_SERVER_GUIDE.md)

## 🧪 Tests

```bash
# Run tests
python -m pytest tests/

# Or directly
python tests/test_embeddings.py
python tests/test_chat_setup.py
python tests/test_crew_setup.py
```

## 📝 Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for version history.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or pull request.

## 📄 License

MIT License - See the LICENSE file for details.

## 🙏 Acknowledgments

- EASA for the official XML schema
- sentence-transformers for embeddings
- The Python community for development tools

## 📧 Contact

For questions or suggestions, open an issue on GitHub.

---

**Version**: 2.0.0  
**Last updated**: 2025
