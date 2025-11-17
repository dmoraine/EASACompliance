#!/usr/bin/env python3
"""
Helper script to configure Cursor with the EASA MCP server.

This script:
1. Detects the Cursor config location
2. Creates/merges the MCP configuration
3. Displays final instructions
"""

import json
import os
import sys
from pathlib import Path
from shutil import copy2

def find_cursor_config():
    """Finds the Cursor configuration file"""
    home = Path.home()
    
    # Possible locations depending on OS
    possible_paths = [
        # Linux
        home / ".config" / "Cursor" / "User" / "globalStorage" / "mcp.json",
        home / ".cursor" / "mcp.json",
        # macOS
        home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "mcp.json",
        # Windows (approximate)
        Path(os.getenv("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "mcp.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # If none exist, use the first Linux location by default
    default_path = home / ".config" / "Cursor" / "User" / "globalStorage" / "mcp.json"
    return default_path

def get_project_paths():
    """Retrieves project paths"""
    script_dir = Path(__file__).parent.parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    return {
        "python": str(venv_python) if venv_python.exists() else "python",
        "server_script": str(script_dir / "run_mcp_server.py"),
        "database": str(script_dir / "easa_complete.db")
    }

def create_config(config_path, paths):
    """Creates or updates the MCP configuration"""
    config_dir = config_path.parent
    
    # Create directory if necessary
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # EASA configuration
    easa_config = {
        "command": paths["python"],
        "args": [
            paths["server_script"]
        ],
        "env": {
            "EASA_DB_PATH": paths["database"],
            "EASA_MODEL": "all-MiniLM-L12-v2",
            "EASA_MAX_RESULTS": "20",
            "EASA_CACHE": "true"
        }
    }
    
    # Load existing config or create a new one
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  File {config_path} exists but is not valid JSON")
            print(f"   Creating backup...")
            backup_path = config_path.with_suffix('.json.backup')
            copy2(config_path, backup_path)
            config = {"mcpServers": {}}
    else:
        config = {"mcpServers": {}}
    
    # Add or update EASA config
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    config["mcpServers"]["easa-regulations"] = easa_config
    
    # Save
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def main():
    """Main entry point"""
    print("=" * 80)
    print("🔧 CURSOR CONFIGURATION FOR EASA MCP SERVER")
    print("=" * 80)
    print()
    
    # Verify that the database exists
    paths = get_project_paths()
    db_path = Path(paths["database"])
    
    if not db_path.exists():
        print(f"❌ Error: Database not found: {paths['database']}")
        print()
        print("💡 Solution: Build the database first:")
        print(f"   python build_embeddings.py \\")
        print(f"     --xml \"Easy Access Rules for Air Operations - February 2025 - xml.xml\" \\")
        print(f"     --db easa_complete.db --clear")
        sys.exit(1)
    
    print(f"✅ Database found: {paths['database']}")
    print()
    
    # Find the config file
    config_path = find_cursor_config()
    print(f"📁 Configuration file: {config_path}")
    print()
    
    # Create/update the config
    try:
        created_path = create_config(config_path, paths)
        print(f"✅ Configuration created/updated: {created_path}")
        print()
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        sys.exit(1)
    
    # Final instructions
    print("=" * 80)
    print("📋 NEXT STEPS")
    print("=" * 80)
    print()
    print("1. ✅ Configuration created automatically")
    print()
    print("2. 🔄 Completely restart Cursor")
    print("   - Close all Cursor windows")
    print("   - Relaunch Cursor")
    print()
    print("3. ✅ Verify the connection")
    print("   - Open Cursor Chat")
    print("   - Test: \"Find EASA regulations about flight times\"")
    print()
    print("4. 📊 Check the logs")
    print("   - View → Output")
    print("   - Search for \"MCP\" or \"EASA\"")
    print("   - Should display: ✅ EASA MCP Server initialized")
    print()
    print("=" * 80)
    print("✅ CONFIGURATION COMPLETE")
    print("=" * 80)
    print()
    print(f"📁 Config file: {config_path}")
    print(f"🔧 Server: {paths['server_script']}")
    print(f"🗄️  Database: {paths['database']}")
    print()

if __name__ == "__main__":
    main()
