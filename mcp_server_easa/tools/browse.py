"""
MCP Server EASA - Browse Tools

Tools pour naviguer et explorer la base de données réglementaire.
"""

from typing import List, Dict
import sys
from pathlib import Path
import sqlite3
import json
from collections import Counter

# Ajouter le chemin racine pour les imports
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from easacompliance import EmbeddingsManager

# Import conditionnel pour gérer les imports relatifs et absolus
try:
    from ..schemas import CategoryInfo, Statistics
    from ..config import ServerConfig
except ImportError:
    from mcp_server_easa.schemas import CategoryInfo, Statistics
    from mcp_server_easa.config import ServerConfig


class BrowseTools:
    """Tools de navigation et statistiques"""
    
    def __init__(self, config: ServerConfig):
        """
        Initialise les tools de navigation.
        
        Args:
            config: Configuration du serveur
        """
        self.config = config
        self._embeddings_manager = None
    
    @property
    def embeddings_manager(self) -> EmbeddingsManager:
        """Lazy loading du gestionnaire d'embeddings"""
        if self._embeddings_manager is None:
            self._embeddings_manager = EmbeddingsManager(
                db_path=self.config.db_path,
                model_name=self.config.model_name
            )
        return self._embeddings_manager
    
    def list_categories(self, limit: int = 50) -> List[CategoryInfo]:
        """
        Liste toutes les catégories de régulations disponibles.
        
        Args:
            limit: Nombre maximum de catégories à retourner
        
        Returns:
            Liste de CategoryInfo triées par nombre de régulations
        
        Example:
            >>> tools.list_categories(limit=10)
            [CategoryInfo(category="ORO.FTL", count=17), ...]
        """
        # Récupérer toutes les métadonnées
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT metadata FROM paragraphs")
        rows = cursor.fetchall()
        
        # Compter par catégorie
        categories = Counter()
        for row in rows:
            try:
                metadata = json.loads(row[0])
                category = metadata.get('category', 'Unknown')
                if category and category != 'Unknown' and category != 'No-Category':
                    categories[category] += 1
            except:
                pass
        
        conn.close()
        
        # Créer les CategoryInfo
        result = []
        for category, count in categories.most_common(limit):
            info = CategoryInfo(
                category=category,
                count=count,
                description=self._get_category_description(category)
            )
            result.append(info)
        
        return result
    
    def _get_category_description(self, category: str) -> str:
        """Génère une description pour une catégorie"""
        descriptions = {
            "ORO.FTL": "Flight Time Limitations and Rest Requirements",
            "ORO.FC": "Flight Crew Requirements",
            "ORO.CC": "Cabin Crew Requirements",
            "ORO.GEN": "General Requirements for Air Operations",
            "ARO.GEN": "Authority Requirements - General",
            "ARO.OPS": "Authority Requirements - Operations",
            "CAT.OP": "Commercial Air Transport Operations",
            "SPO.OP": "Specialised Operations",
            "NCO.OP": "Non-Commercial Operations with Complex Aircraft",
            "NCC.OP": "Non-Commercial Operations",
            "CS FTL": "Certification Specifications - Flight Time Limitations",
        }
        return descriptions.get(category, "")
    
    def get_statistics(self) -> Statistics:
        """
        Récupère les statistiques de la base réglementaire.
        
        Returns:
            Statistics avec informations complètes
        
        Example:
            >>> tools.get_statistics()
            Statistics(total_regulations=3199, ...)
        """
        # Utiliser le gestionnaire d'embeddings
        stats = self.embeddings_manager.get_stats()
        
        # Récupérer la répartition par type
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT metadata FROM paragraphs")
        rows = cursor.fetchall()
        
        type_counts = Counter()
        category_counts = Counter()
        
        for row in rows:
            try:
                metadata = json.loads(row[0])
                
                # Type
                topic_type = metadata.get('topic_type', 'Unknown')
                type_counts[topic_type] += 1
                
                # Catégorie
                category = metadata.get('category', 'Unknown')
                if category and category not in ['Unknown', 'No-Category']:
                    category_counts[category] += 1
            except:
                pass
        
        conn.close()
        
        # Taille de la base
        db_size_mb = Path(self.config.db_path).stat().st_size / (1024 * 1024)
        
        return Statistics(
            total_regulations=stats.get('total_paragraphs', 0),
            by_type=dict(type_counts),
            by_category=dict(category_counts.most_common(20)),
            db_size_mb=db_size_mb,
            model_name=self.config.model_name
        )
    
    def get_tool_schemas(self) -> list[dict]:
        """Retourne les schémas MCP pour ces tools"""
        return [
            {
                "name": "list_categories",
                "description": (
                    "List all available EASA regulation categories. "
                    "Returns categories sorted by number of regulations. "
                    "Useful for exploring what regulatory areas are covered "
                    "in the database (e.g., ORO.FTL for Flight Time Limitations, "
                    "ORO.FC for Flight Crew, etc.)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of categories to return (default: 50)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "get_statistics",
                "description": (
                    "Get comprehensive statistics about the EASA regulatory database. "
                    "Returns total number of regulations, breakdown by type (IR, AMC, GM, etc.), "
                    "breakdown by category, database size, and model information. "
                    "Useful for understanding the scope and coverage of the database."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

