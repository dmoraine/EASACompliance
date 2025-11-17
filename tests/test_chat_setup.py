#!/usr/bin/env python3
"""
Test script to verify chat_mcp.py setup without needing real API keys.
This checks that all components load correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🧪 Testing Chat MCP Setup")
print("=" * 80)

# Test 1: Import check
print("\n1️⃣  Testing imports...")
try:
    from chat_mcp import (
        ConfigManager,
        MCPClient,
        UnifiedLLMClient,
        ChatMCPApp,
        ProviderConfig
    )
    print("   ✅ All imports successful")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Configuration manager
print("\n2️⃣  Testing ConfigManager...")
try:
    config_manager = ConfigManager()
    providers = config_manager.list_providers()
    print(f"   ✅ ConfigManager initialized")
    print(f"   📋 Available providers: {', '.join(providers) if providers else 'None (check .env)'}")
    
    for provider_id in providers:
        config = config_manager.get_provider(provider_id)
        print(f"      • {config.name}: {config.model}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Database check
print("\n3️⃣  Checking EASA database...")
db_path = Path("easa_complete.db")
if db_path.exists():
    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"   ✅ Database found: {db_path} ({size_mb:.2f} MB)")
else:
    print(f"   ⚠️  Database not found: {db_path}")
    print(f"      Run: python easacompliance/scripts/build_embeddings.py")

# Test 4: MCP server script check
print("\n4️⃣  Checking MCP server...")
server_script = Path("run_mcp_server.py")
if server_script.exists():
    print(f"   ✅ MCP server script found: {server_script}")
else:
    print(f"   ❌ MCP server script not found: {server_script}")

# Test 5: Dependencies check
print("\n5️⃣  Checking dependencies...")
try:
    import openai
    print(f"   ✅ openai: {openai.__version__}")
except ImportError:
    print("   ❌ openai not installed. Run: pip install openai>=1.0.0")

try:
    import dotenv
    print(f"   ✅ python-dotenv installed")
except ImportError:
    print("   ❌ python-dotenv not installed. Run: pip install python-dotenv")

try:
    import mcp
    print(f"   ✅ mcp installed")
except ImportError:
    print("   ❌ mcp not installed. Run: pip install mcp")

# Test 6: Environment file check
print("\n6️⃣  Checking environment configuration...")
env_file = Path(".env")
env_example = Path("env.example")

if env_file.exists():
    print(f"   ✅ .env file found")
    
    # Check for provider configurations
    with open(env_file, 'r') as f:
        content = f.read()
        
    has_openai = "OPENAI_API_KEY" in content and "sk-" in content
    has_hyperbolic = "HYPERBOLIC_API_KEY" in content and len(content) > 100
    
    if has_openai:
        print("      • OpenAI configured")
    if has_hyperbolic:
        print("      • Hyperbolic configured")
    print("      • Ollama: Always available (local)")
    
elif env_example.exists():
    print(f"   ⚠️  .env not found, but env.example exists")
    print(f"      Run: cp env.example .env")
else:
    print(f"   ❌ No .env or env.example file found")

# Summary
print("\n" + "=" * 80)
print("📊 Summary")
print("=" * 80)

if db_path.exists() and server_script.exists():
    print("✅ Setup looks good! Ready to test chat_mcp.py")
    print("\n💡 To test:")
    print("   python chat_mcp.py --provider ollama  # For local testing")
    print("   python chat_mcp.py --provider openai  # If OpenAI configured")
else:
    print("⚠️  Some components are missing. See above for details.")

print("=" * 80)

