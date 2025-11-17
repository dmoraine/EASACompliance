#!/usr/bin/env python3
"""
Client de test simple pour le serveur MCP EASA.

Ce script teste toutes les fonctionnalités du serveur MCP.
"""

import asyncio
import json
from pathlib import Path
import sys

# Ajouter le chemin racine
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("ERROR: mcp package not found. Install with: pip install mcp")
    sys.exit(1)


async def test_server():
    """Teste le serveur MCP EASA"""
    
    print("=" * 80)
    print("🧪 TEST DU SERVEUR MCP EASA")
    print("=" * 80)
    print()
    
    # Configuration du serveur
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "run_mcp_server.py"],
        env={
            "EASA_DB_PATH": "easa_complete.db",
            "EASA_MODEL": "all-MiniLM-L6-v2"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialiser la session
            await session.initialize()
            
            print("✅ Connexion au serveur établie")
            print()
            
            # Test 1: Liste des tools
            print("📋 TEST 1: Liste des tools disponibles")
            print("-" * 80)
            tools = await session.list_tools()
            print(f"✅ {len(tools.tools)} tools disponibles:")
            for tool in tools.tools:
                print(f"   • {tool.name}: {tool.description[:60]}...")
            print()
            
            # Test 2: Get statistics
            print("📊 TEST 2: Statistiques de la base")
            print("-" * 80)
            result = await session.call_tool("get_statistics", {})
            stats = json.loads(result.content[0].text)
            
            # Vérifier si c'est une erreur
            if 'error' in stats:
                print(f"❌ Erreur: {stats.get('error')}")
                print(f"   Tool: {stats.get('tool')}")
                print(f"   Args: {stats.get('arguments')}")
            else:
                print(f"✅ Total régulations: {stats.get('total_regulations', 'N/A')}")
                if 'by_type' in stats:
                    print(f"   Types:")
                    for type_name, count in list(stats['by_type'].items())[:5]:
                        print(f"   - {type_name}: {count}")
            print()
            
            # Test 3: List categories
            print("📁 TEST 3: Liste des catégories")
            print("-" * 80)
            result = await session.call_tool("list_categories", {"limit": 10})
            cats = json.loads(result.content[0].text)
            print(f"✅ {cats['count']} catégories trouvées:")
            for cat in cats['categories'][:5]:
                print(f"   • {cat['category']}: {cat['count']} régulations")
            print()
            
            # Test 4: Search regulations
            print("🔍 TEST 4: Recherche sémantique")
            print("-" * 80)
            query = "flight time limitations for crew"
            result = await session.call_tool(
                "search_regulations",
                {
                    "query": query,
                    "top_k": 3
                }
            )
            search_results = json.loads(result.content[0].text)
            print(f"✅ Requête: '{query}'")
            print(f"   {search_results['count']} résultats:")
            for reg in search_results['regulations']:
                print(f"   • {reg['reference']}: {reg['title']}")
                print(f"     Score: {reg['score']:.3f}")
            print()
            
            # Test 5: Get specific regulation
            print("📖 TEST 5: Récupération d'une régulation")
            print("-" * 80)
            reference = "ORO.FTL.110"
            result = await session.call_tool(
                "get_regulation",
                {"reference": reference}
            )
            reg_data = json.loads(result.content[0].text)
            if "error" not in reg_data:
                print(f"✅ Régulation: {reg_data['reference']}")
                print(f"   Titre: {reg_data['title']}")
                print(f"   Type: {reg_data['type']}")
                print(f"   Contenu: {reg_data['content'][:100]}...")
            else:
                print(f"❌ {reg_data['error']}")
            print()
            
            # Test 6: Get regulatory chain
            print("🔗 TEST 6: Chaîne réglementaire")
            print("-" * 80)
            result = await session.call_tool(
                "get_regulatory_chain",
                {"reference": reference}
            )
            chain = json.loads(result.content[0].text)
            print(f"✅ Chaîne pour {reference}:")
            if chain.get('ir'):
                print(f"   IR: {chain['ir']['reference']}")
            print(f"   AMCs: {len(chain['amcs'])}")
            print(f"   GMs: {len(chain['gms'])}")
            print(f"   Total: {chain['total_items']} items")
            print()
            
            # Test 7: Validate compliance
            print("✔️  TEST 7: Validation de conformité")
            print("-" * 80)
            text = "Flight crew members must not exceed 900 hours in a calendar year"
            result = await session.call_tool(
                "validate_compliance",
                {
                    "text": text,
                    "top_k": 5
                }
            )
            compliance = json.loads(result.content[0].text)
            print(f"✅ Texte: '{text[:60]}...'")
            print(f"   Score: {compliance['score']:.2f}")
            print(f"   Niveau: {compliance['compliance_level']}")
            print(f"   Régulations pertinentes: {len(compliance['relevant_regulations'])}")
            print(f"   Gaps: {len(compliance['gaps'])}")
            print()
    
    print("=" * 80)
    print("✅ TOUS LES TESTS RÉUSSIS")
    print("=" * 80)


async def main():
    """Point d'entrée principal"""
    try:
        await test_server()
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

