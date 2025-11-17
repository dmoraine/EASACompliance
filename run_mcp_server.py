#!/usr/bin/env python3
"""
Main entry point for the EASA MCP server.

This script properly configures the PYTHONPATH and launches the server.
"""

import sys
from pathlib import Path

# Add the mcp_server_easa directory to PYTHONPATH
server_dir = Path(__file__).parent / "mcp_server_easa"
root_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(root_dir))

# Import and launch the server
if __name__ == "__main__":
    # Dynamic import to avoid relative import issues
    import asyncio
    import os
    
    # Ensure environment variables are set
    if "EASA_DB_PATH" not in os.environ:
        os.environ["EASA_DB_PATH"] = str(root_dir / "easa_complete.db")
    
    # Now we can import the server
    from mcp_server_easa.server import main
    
    # Launch the server
    asyncio.run(main())
