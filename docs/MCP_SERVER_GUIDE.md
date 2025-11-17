# 🚀 EASA MCP Server - Complete Guide

The EASA MCP server exposes EASA regulations via the MCP (Model Context Protocol), allowing any compatible LLM to consult and analyze aviation regulations.

## 📋 Table of Contents

- [Overview](#-overview)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Available Tools](#-available-tools)
- [Usage](#-usage)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

### What is MCP?

The **Model Context Protocol** (MCP) is a standard protocol for connecting LLMs to external data sources and tools. The EASA MCP server allows an LLM to access the EASA regulatory database in a structured way.

### Architecture

```
┌─────────────────────────────────────┐
│     LLM (Claude, GPT, etc.)         │
│   ┌──────────────────────────────┐  │
│   │   MCP Client                 │  │
│   └────────────┬─────────────────┘  │
└────────────────┼────────────────────┘
                 │ MCP Protocol
                 ↓
    ┌────────────────────────────────┐
    │   EASA MCP Server              │
    │  ┌───────────────────────────┐ │
    │  │ 6 Tools:                  │ │
    │  │ - search_regulations      │ │
    │  │ - get_regulation          │ │
    │  │ - get_regulatory_chain    │ │
    │  │ - list_categories         │ │
    │  │ - get_statistics          │ │
    │  │ - validate_compliance     │ │
    │  └───────────────────────────┘ │
    └────────────┬───────────────────┘
                 │
    ┌────────────▼───────────────────┐
    │   EASA Embeddings Database     │
    │   (3199 regulations)           │
    │   - IR, AMC, GM, CS            │
    └────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

```bash
# Python 3.10+
python --version

# MCP package
pip install mcp
# or
uv add mcp

# EASA database built
ls -lh easa_complete.db
```

### Server Installation

```bash
cd /path/to/EASACompliance

# The server is already in mcp_server_easa/
# Verify the structure
tree mcp_server_easa/
```

---

## ⚙️ Configuration

### Environment Variables

The server can be configured via environment variables:

```bash
# Database path (required)
export EASA_DB_PATH="/path/to/easa_complete.db"

# Embeddings model (optional)
export EASA_MODEL="all-MiniLM-L12-v2"

# Maximum number of results (optional)
export EASA_MAX_RESULTS="20"

# Enable cache (optional)
export EASA_CACHE="true"

# Path to source XML (optional, for direct access)
export EASA_XML_PATH="/path/to/regulations.xml"
```

### Configuration for Claude Desktop

Add to the file `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or  
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "easa-regulations": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/path/to/EASACompliance/run_mcp_server.py"
      ],
      "env": {
        "EASA_DB_PATH": "/path/to/EASACompliance/easa_complete.db",
        "EASA_MODEL": "all-MiniLM-L12-v2"
      }
    }
  }
}
```

**Note**: Replace `/path/to/EASACompliance` with the absolute path of your project.  
See also `examples/claude_desktop_config.json` for a ready-to-use template.

---

## 🛠️ Available Tools

### 1. `search_regulations`

Semantic search in EASA regulations.

**Input:**
```json
{
  "query": "flight time limitations for crew",
  "top_k": 5,
  "types": ["IR", "AMC"],
  "min_score": 0.3
}
```

**Output:**
```json
{
  "count": 5,
  "regulations": [
    {
      "reference": "ORO.FTL.110",
      "title": "Operator responsibilities",
      "content": "...",
      "type": "IR (Implementing rule);",
      "score": 0.876
    }
  ]
}
```

**Usage:**
- Find regulations on a specific topic
- Explore regulatory concepts
- Identify applicable requirements

---

### 2. `get_regulation`

Retrieves a regulation by its exact reference.

**Input:**
```json
{
  "reference": "ORO.FTL.110"
}
```

**Output:**
```json
{
  "reference": "ORO.FTL.110",
  "title": "Operator responsibilities",
  "content": "...",
  "type": "IR (Implementing rule);",
  "metadata": {...}
}
```

**Usage:**
- Consult a specific regulation
- Verify the exact content of a rule
- Retrieve metadata

---

### 3. `get_regulatory_chain`

Retrieves an IR rule and all its associated AMC/GM.

**Input:**
```json
{
  "reference": "ORO.FTL.110"
}
```

**Output:**
```json
{
  "ir": {
    "reference": "ORO.FTL.110",
    "title": "Operator responsibilities",
    "..."
  },
  "amcs": [
    {"reference": "AMC1 ORO.FTL.110", "..."},
    {"reference": "AMC2 ORO.FTL.110", "..."}
  ],
  "gms": [
    {"reference": "GM1 ORO.FTL.110", "..."}
  ],
  "total_items": 4
}
```

**Usage:**
- Understand how to apply a rule
- Find acceptable means of compliance
- Consult guidance material

---

### 4. `list_categories`

Lists all available regulation categories.

**Input:**
```json
{
  "limit": 20
}
```

**Output:**
```json
{
  "count": 20,
  "categories": [
    {
      "category": "ORO.FTL",
      "count": 17,
      "description": "Flight Time Limitations and Rest Requirements"
    },
    {
      "category": "ORO.FC",
      "count": 31,
      "description": "Flight Crew Requirements"
    }
  ]
}
```

**Usage:**
- Explore available regulatory domains
- Discover relevant categories
- Understand EASA structure

---

### 5. `get_statistics`

Retrieves statistics about the regulatory database.

**Input:**
```json
{}
```

**Output:**
```json
{
  "total_regulations": 3199,
  "by_type": {
    "IR (Implementing rule);": 1022,
    "AMC to IR (...)": 1156,
    "GM to IR (...)": 982
  },
  "by_category": {
    "ORO.FTL": 17,
    "ORO.FC": 31
  },
  "db_size_mb": 20.6,
  "model_name": "all-MiniLM-L12-v2"
}
```

**Usage:**
- Understand database coverage
- Verify data availability
- Diagnose configuration

---

### 6. `validate_compliance`

Validates text compliance with EASA regulations.

**Input:**
```json
{
  "text": "Flight crew must not exceed 900 hours in a calendar year",
  "category": "ORO.FTL",
  "top_k": 10,
  "min_score": 0.3
}
```

**Output:**
```json
{
  "score": 0.75,
  "compliance_level": "MEDIUM",
  "relevant_regulations": [...],
  "gaps": [
    "Consider how compliance will be demonstrated"
  ],
  "recommendations": [
    "Review ORO.FTL.110: Operator responsibilities"
  ],
  "summary": "Compliance Level: MEDIUM (score: 0.75). Found 5 relevant regulations."
}
```

**Usage:**
- Validate an operations manual
- Identify compliance gaps
- Get recommendations

---

## 🚀 Usage

### With Claude Desktop

1. **Configure**: Add configuration to `claude_desktop_config.json`
2. **Restart**: Restart Claude Desktop
3. **Use**: The server appears automatically in available tools

Example conversation:

```
👤 User:
"What are the flight time limitations for crew?"

🤖 Claude (uses search_regulations):
I'll search for regulations on flight time limitations.

[Call: search_regulations("flight time limitations for crew")]

According to EASA regulations, here are the main requirements...
```

---

### With a Python Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def query_easa():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "run_mcp_server.py"],
        env={"EASA_DB_PATH": "easa_complete.db"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Search
            result = await session.call_tool(
                "search_regulations",
                {"query": "flight time limitations", "top_k": 3}
            )
            print(result.content[0].text)

asyncio.run(query_easa())
```

---

### Test the Server

```bash
# Run the test
cd /path/to/EASACompliance
python examples/mcp_client_test.py

# Expected output:
# ✅ Server connection established
# ✅ 6 tools available
# ✅ Tests passed
```

---

## 📚 Usage Examples

### Example 1: Simple Search

**Prompt:**
```
"Find regulations about rest requirements for crew"
```

**The LLM uses:**
```json
search_regulations({
  "query": "rest requirements for crew",
  "top_k": 5
})
```

---

### Example 2: Regulation Analysis

**Prompt:**
```
"What is ORO.FTL.110 and what are the associated compliance methods?"
```

**The LLM uses:**
```json
get_regulatory_chain({
  "reference": "ORO.FTL.110"
})
```

---

### Example 3: Manual Validation

**Prompt:**
```
"Validate this text against EASA regulations:
'Pilots must have at least 12 hours of rest before a flight'"
```

**The LLM uses:**
```json
validate_compliance({
  "text": "Pilots must have at least 12 hours...",
  "category": "ORO.FTL"
})
```

---

## 🔧 Troubleshooting

### Error: "Database not found"

```bash
# Verify that the database exists
ls -lh easa_complete.db

# Build the database if necessary
python build_embeddings.py \
  --xml "regulations.xml" \
  --db easa_complete.db \
  --clear
```

### Error: "mcp package not found"

```bash
# Install mcp
pip install mcp
# or
uv add mcp
```

### Server doesn't start

```bash
# Test directly
export EASA_DB_PATH="easa_complete.db"
python run_mcp_server.py

# Check logs
# The server should display:
# ✅ EASA MCP Server initialized
# Database: easa_complete.db
# Model: all-MiniLM-L12-v2
```

### Slow performance

```bash
# Enable cache
export EASA_CACHE="true"

# Reduce top_k
# In queries, use top_k=3 instead of top_k=20
```

---

## 📊 Coverage Statistics

The database contains:
- **3199 regulations** (95.3% of source XML)
- **1156 AMC** (36.1%)
- **982 GM to IR** (30.7%)
- **1022 IR** (31.9%)
- **17 GM to CS** (0.5%)
- **7 CS** (0.2%)

---

## 🔗 Resources

- **Source code**: `mcp_server_easa/`
- **Examples**: `examples/`
- **MCP documentation**: https://modelcontextprotocol.io
- **Embeddings database**: See `docs/RAPPORT_CORRECTION_AMC_GM.md`

---

**Version**: 1.0.0  
**Date**: 2025-11-17  
**Status**: ✅ Production Ready
