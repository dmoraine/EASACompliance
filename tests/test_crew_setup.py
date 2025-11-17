#!/usr/bin/env python3
"""
Test script to verify compliance_crew.py setup.
Checks all components without needing real API keys or running a full audit.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🧪 Testing CrewAI Compliance Validator Setup")
print("=" * 80)

# Test 1: Import check
print("\n1️⃣  Testing imports...")
try:
    from compliance_crew import (
        ConfigManager,
        MCPClient,
        ComplianceCrewApp,
        ProviderConfig
    )
    print("   ✅ Core imports successful")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test CrewAI imports
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import tool
    print("   ✅ CrewAI imports successful")
except ImportError as e:
    print(f"   ❌ CrewAI import error: {e}")
    print("      Install with: pip install crewai crewai-tools")

# Test MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    print("   ✅ MCP imports successful")
except ImportError as e:
    print(f"   ❌ MCP import error: {e}")
    print("      Install with: pip install mcp")

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

deps = {
    "openai": None,
    "dotenv": "python-dotenv",
    "mcp": None,
    "crewai": None,
}

for module_name, package_name in deps.items():
    try:
        if module_name == "openai":
            import openai
            print(f"   ✅ openai: {openai.__version__}")
        elif module_name == "dotenv":
            import dotenv
            print(f"   ✅ python-dotenv installed")
        elif module_name == "mcp":
            import mcp
            print(f"   ✅ mcp installed")
        elif module_name == "crewai":
            import crewai
            print(f"   ✅ crewai installed")
    except ImportError:
        pkg = package_name or module_name
        print(f"   ❌ {module_name} not installed. Run: pip install {pkg}")

# Test 6: CrewAI tools check
print("\n6️⃣  Checking CrewAI tools wrappers...")
try:
    from compliance_crew import (
        search_easa_regulations,
        get_easa_regulation,
        get_regulatory_chain,
        list_easa_categories,
        validate_text_compliance,
        get_easa_statistics
    )
    tools = [
        search_easa_regulations,
        get_easa_regulation,
        get_regulatory_chain,
        list_easa_categories,
        validate_text_compliance,
        get_easa_statistics
    ]
    print(f"   ✅ {len(tools)} MCP tools wrapped for CrewAI")
    for tool_func in tools:
        print(f"      • {tool_func.name}")
except Exception as e:
    print(f"   ❌ Error loading tools: {e}")

# Test 7: Agent creation check
print("\n7️⃣  Checking agent creation functions...")
try:
    from compliance_crew import (
        create_compliance_auditor,
        create_qa_challenger
    )
    print(f"   ✅ Agent creation functions available")
    print(f"      • create_compliance_auditor")
    print(f"      • create_qa_challenger")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 8: Task creation check
print("\n8️⃣  Checking task creation functions...")
try:
    from compliance_crew import (
        create_audit_task,
        create_challenge_task,
        create_final_report_task
    )
    print(f"   ✅ Task creation functions available")
    print(f"      • create_audit_task (Auditor)")
    print(f"      • create_challenge_task (QA Challenger)")
    print(f"      • create_final_report_task (Final Report)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 9: Environment file check
print("\n9️⃣  Checking environment configuration...")
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
        print("      • OpenAI configured (recommended for CrewAI)")
    if has_hyperbolic:
        print("      • Hyperbolic configured")
    print("      • Ollama: Always available (local)")
    
elif env_example.exists():
    print(f"   ⚠️  .env not found, but env.example exists")
    print(f"      Run: cp env.example .env")
else:
    print(f"   ❌ No .env or env.example file found")

# Test 10: Script syntax check
print("\n🔟  Checking script syntax...")
try:
    import py_compile
    script_path = Path("compliance_crew.py")
    py_compile.compile(str(script_path), doraise=True)
    print(f"   ✅ compliance_crew.py syntax valid")
except Exception as e:
    print(f"   ❌ Syntax error: {e}")

# Summary
print("\n" + "=" * 80)
print("📊 Summary")
print("=" * 80)

ready = db_path.exists() and server_script.exists()

if ready:
    print("✅ Setup looks good! Ready to run compliance audits")
    print("\n💡 To test with a simple example:")
    print('   python compliance_crew.py \\')
    print('     --text "Flight crew members must not exceed 900 hours in a calendar year" \\')
    print('     --output test_report.md \\')
    print('     --provider openai')
    print("\n📖 For full documentation:")
    print("   cat COMPLIANCE_CREW_README.md")
else:
    print("⚠️  Some components are missing. See above for details.")

print("\n⚠️  IMPORTANT NOTES:")
print("   • CrewAI with 2 agents = multiple LLM calls (costs apply)")
print("   • Recommended: Use OpenAI GPT-4 or GPT-4o for best results")
print("   • For testing: Use Ollama (local, free) but results may vary")
print("   • Typical audit takes 2-15 minutes depending on text length")

print("=" * 80)

