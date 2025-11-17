#!/usr/bin/env python3
"""
Build EASA Embeddings Database - Entry Point Script

This is a convenience wrapper at the root level that calls the actual
implementation in easacompliance/scripts/build_embeddings.py

Usage:
    python build_embeddings.py --xml <xml_file> --db <db_file> [options]

Examples:
    # Build complete database
    python build_embeddings.py \
        --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
        --db easa_complete.db \
        --clear

    # Build specific category
    python build_embeddings.py \
        --xml "Easy Access Rules for Air Operations - February 2025 - xml.xml" \
        --category "ORO.FTL" \
        --db oro_ftl.db \
        --clear
"""

import sys
from pathlib import Path

# Add the package to path
_root = Path(__file__).parent
sys.path.insert(0, str(_root))

# Import and run the main function from the actual implementation
if __name__ == "__main__":
    from easacompliance.scripts.build_embeddings import main
    main()

