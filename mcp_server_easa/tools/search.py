"""
MCP Server EASA - Search Tools

Tools pour la recherche sémantique dans les régulations EASA.
"""

from typing import List, Optional
import sys
from pathlib import Path

# Ajouter le chemin racine pour les imports
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from easacompliance import EmbeddingsManager

# Import conditionnel pour gérer les imports relatifs et absolus
try:
    from ..schemas import Regulation
    from ..config import ServerConfig
except ImportError:
    from mcp_server_easa.schemas import Regulation
    from mcp_server_easa.config import ServerConfig


class SearchTools:
    """Tools de recherche dans les régulations EASA"""
    
    def __init__(self, config: ServerConfig):
        """
        Initialise les tools de recherche.
        
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
    
    def search_regulations(
        self,
        query: str,
        top_k: Optional[int] = None,
        types: Optional[List[str]] = None,
        min_score: Optional[float] = None
    ) -> List[Regulation]:
        """
        Recherche sémantique dans les régulations EASA.
        
        Args:
            query: Requête de recherche en texte libre
            top_k: Nombre de résultats à retourner (défaut: config.default_top_k)
            types: Filtrer par types de régulation (ex: ["IR", "AMC"])
            min_score: Score minimum de similarité (0-1)
        
        Returns:
            Liste de Regulation triées par score de pertinence
        
        Example:
            >>> tools.search_regulations("flight time limitations", top_k=5)
            [Regulation(...), ...]
        """
        if top_k is None:
            top_k = self.config.default_top_k
        
        if min_score is None:
            min_score = self.config.min_score_default
        
        # Limiter top_k
        top_k = min(top_k, self.config.max_search_results)
        
        # Rechercher
        results = self.embeddings_manager.search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )
        
        # Convertir en Regulation
        regulations = []
        for result in results:
            # Filtrer par type si demandé
            if types and result.paragraph_type not in types:
                continue
            
            reg = Regulation(
                reference=result.reference,
                title=result.title,
                content=result.content,
                type=result.paragraph_type,
                score=result.score,
                metadata=result.metadata
            )
            regulations.append(reg)
        
        return regulations
    
    def get_tool_schema(self) -> dict:
        """Retourne le schéma MCP pour ce tool"""
        return {
            "name": "search_regulations",
            "description": (
                "Search EASA regulations using semantic similarity. "
                "Returns the most relevant regulations for a given query. "
                "Useful for finding regulations related to specific topics, "
                "requirements, or operational scenarios."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in natural language (e.g., 'flight time limitations for crew')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": f"Number of results to return (default: {self.config.default_top_k}, max: {self.config.max_search_results})",
                        "minimum": 1,
                        "maximum": self.config.max_search_results,
                        "default": self.config.default_top_k
                    },
                    "types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by regulation types (e.g., ['IR', 'AMC', 'GM_IR'])",
                        "default": None
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1, default: 0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": self.config.min_score_default
                    }
                },
                "required": ["query"]
            }
        }

