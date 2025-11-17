#!/bin/bash
# ============================================================================
# EASA Compliance - Installation Script
# ============================================================================
# Modern installation using uv (fast Python package installer)
# https://github.com/astral-sh/uv
# ============================================================================

set -e

echo ""
echo "🚀 EASA Compliance - Installation"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 uv not found. Installing uv..."
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo ""
    echo "✅ uv installed successfully"
else
    echo "✅ uv found: $(uv --version)"
fi

echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv

echo "✅ Virtual environment created"
echo ""

# Determine activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    ACTIVATE_CMD=".venv\\Scripts\\activate"
else
    ACTIVATE_CMD="source .venv/bin/activate"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
echo ""
uv pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Activate environment:"
echo "   $ACTIVATE_CMD"
echo ""
echo "2. Configure .env file:"
echo "   cp env.example .env"
echo "   # Then edit .env with your API keys"
echo ""
echo "3. Build EASA database (if not already done):"
echo "   python easacompliance/scripts/build_embeddings.py \\"
echo "     --xml 'Easy Access Rules for Air Operations - February 2025 - xml.xml' \\"
echo "     --db easa_complete.db \\"
echo "     --clear"
echo ""
echo "4. Test the tools:"
echo "   # Chat MCP Client"
echo "   python chat_mcp.py --provider ollama"
echo ""
echo "   # CrewAI Compliance Validator"
echo "   python compliance_crew.py \\"
echo "     --text 'Your text to audit' \\"
echo "     --output report.md \\"
echo "     --provider openai"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Documentation:"
echo "   - Main README: README.md"
echo "   - Chat MCP: docs/chat/README.md"
echo "   - CrewAI: docs/crew/README.md"
echo "   - MCP Server: docs/mcp/GUIDE.md"
echo ""
echo "🎉 Happy auditing with EASA regulations!"
echo ""

