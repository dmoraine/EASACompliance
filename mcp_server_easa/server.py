"""
MCP Server EASA - Main Server Implementation

Ce serveur expose les régulations EASA via le protocole MCP (Model Context Protocol).
Il peut être connecté à n'importe quel client MCP (Claude Desktop, LLM personnalisé, etc.).
"""

import asyncio
import json
from typing import Any
import sys
from pathlib import Path

# Ajouter le chemin racine AVANT les imports
_root = Path(__file__).parent.parent
_server_dir = Path(__file__).parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_server_dir))

# Importer mcp
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("ERROR: mcp package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Imports du serveur (gestion des imports relatifs et absolus)
try:
    # Essayer d'abord les imports relatifs (si exécuté comme module)
    from .config import ServerConfig
    from .tools import SearchTools, RetrieveTools, BrowseTools, ValidateTools
except ImportError:
    # Sinon, utiliser les imports absolus (si exécuté directement)
    from config import ServerConfig
    from tools import SearchTools, RetrieveTools, BrowseTools, ValidateTools


class EASAMCPServer:
    """Serveur MCP pour les régulations EASA"""
    
    def __init__(self, config: ServerConfig = None):
        """
        Initialise le serveur MCP EASA.
        
        Args:
            config: Configuration du serveur (None = config par défaut)
        """
        self.config = config or ServerConfig.from_env()
        
        # Valider la configuration
        try:
            self.config.validate()
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Créer le serveur MCP
        self.server = Server("easa-regulations")
        
        # Initialiser les tools
        self.search_tools = SearchTools(self.config)
        self.retrieve_tools = RetrieveTools(self.config)
        self.browse_tools = BrowseTools(self.config)
        self.validate_tools = ValidateTools(self.config)
        
        # Enregistrer les handlers
        self._register_handlers()
        
        print(f"✅ EASA MCP Server initialized", file=sys.stderr)
        print(f"   Database: {self.config.db_path}", file=sys.stderr)
        print(f"   Model: {self.config.model_name}", file=sys.stderr)
    
    def _register_handlers(self):
        """Enregistre tous les handlers MCP"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Liste tous les tools disponibles"""
            tools = []
            
            # Search tool
            tools.append(Tool(**self.search_tools.get_tool_schema()))
            
            # Retrieve tools
            for schema in self.retrieve_tools.get_tool_schemas():
                tools.append(Tool(**schema))
            
            # Browse tools
            for schema in self.browse_tools.get_tool_schemas():
                tools.append(Tool(**schema))
            
            # Validate tool
            tools.append(Tool(**self.validate_tools.get_tool_schema()))
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Exécute un tool"""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_msg = {
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }
                return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]
    
    async def _execute_tool(self, name: str, arguments: dict) -> dict:
        """
        Exécute un tool spécifique.
        
        Args:
            name: Nom du tool
            arguments: Arguments du tool
        
        Returns:
            Résultat du tool sous forme de dictionnaire
        """
        # Search regulations
        if name == "search_regulations":
            regulations = self.search_tools.search_regulations(
                query=arguments["query"],
                top_k=arguments.get("top_k"),
                types=arguments.get("types"),
                min_score=arguments.get("min_score")
            )
            return {
                "count": len(regulations),
                "regulations": [r.to_dict() for r in regulations]
            }
        
        # Get regulation
        elif name == "get_regulation":
            regulation = self.retrieve_tools.get_regulation(
                reference=arguments["reference"]
            )
            if regulation:
                return regulation.to_dict()
            else:
                return {"error": f"Regulation not found: {arguments['reference']}"}
        
        # Get regulatory chain
        elif name == "get_regulatory_chain":
            chain = self.retrieve_tools.get_regulatory_chain(
                reference=arguments["reference"]
            )
            return chain.to_dict()
        
        # List categories
        elif name == "list_categories":
            categories = self.browse_tools.list_categories(
                limit=arguments.get("limit", 50)
            )
            return {
                "count": len(categories),
                "categories": [c.to_dict() for c in categories]
            }
        
        # Get statistics
        elif name == "get_statistics":
            stats = self.browse_tools.get_statistics()
            return stats.to_dict()
        
        # Validate compliance
        elif name == "validate_compliance":
            result = self.validate_tools.validate_compliance(
                text=arguments["text"],
                category=arguments.get("category"),
                top_k=arguments.get("top_k", 10),
                min_score=arguments.get("min_score", 0.3)
            )
            return result.to_dict()
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        """Lance le serveur MCP via stdio"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Point d'entrée principal"""
    # Charger la configuration depuis les variables d'environnement
    config = ServerConfig.from_env()
    
    # Créer et lancer le serveur
    server = EASAMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

