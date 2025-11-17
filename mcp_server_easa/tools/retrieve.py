"""
MCP Server EASA - Retrieve Tools

Tools pour récupérer des régulations spécifiques par référence.
"""

from typing import Optional
import sys
from pathlib import Path
import re

# Ajouter le chemin racine pour les imports
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from easacompliance import EASAParser, EmbeddingsManager, TopicType

# Import conditionnel pour gérer les imports relatifs et absolus
try:
    from ..schemas import Regulation, RegulatoryChain
    from ..config import ServerConfig
except ImportError:
    from mcp_server_easa.schemas import Regulation, RegulatoryChain
    from mcp_server_easa.config import ServerConfig


class RetrieveTools:
    """Tools de récupération de régulations spécifiques"""
    
    def __init__(self, config: ServerConfig):
        """
        Initialise les tools de récupération.
        
        Args:
            config: Configuration du serveur
        """
        self.config = config
        self._parser = None
        self._embeddings_manager = None
    
    @property
    def parser(self) -> Optional[EASAParser]:
        """Lazy loading du parser (si XML disponible)"""
        if self._parser is None and self.config.xml_path:
            self._parser = EASAParser(self.config.xml_path)
        return self._parser
    
    @property
    def embeddings_manager(self) -> EmbeddingsManager:
        """Lazy loading du gestionnaire d'embeddings"""
        if self._embeddings_manager is None:
            self._embeddings_manager = EmbeddingsManager(
                db_path=self.config.db_path,
                model_name=self.config.model_name
            )
        return self._embeddings_manager
    
    def get_regulation(self, reference: str) -> Optional[Regulation]:
        """
        Récupère une régulation par sa référence exacte.
        
        Args:
            reference: Référence de la régulation (ex: "ORO.FTL.110", "AMC1 ORO.FTL.110")
        
        Returns:
            Regulation si trouvée, None sinon
        
        Example:
            >>> tools.get_regulation("ORO.FTL.110")
            Regulation(reference="ORO.FTL.110", ...)
        """
        # Essayer d'abord avec le parser si disponible
        if self.parser:
            topic = self.parser.get_topic_by_reference(reference)
            if topic:
                return Regulation(
                    reference=topic.reference,
                    title=topic.title,
                    content=topic.content,
                    type=topic.topic_type.value,
                    metadata=topic.metadata
                )
        
        # Sinon, chercher dans les embeddings
        results = self.embeddings_manager.search(reference, top_k=10, min_score=0.0)
        
        # Chercher une correspondance exacte
        for result in results:
            if result.reference.lower() == reference.lower():
                return Regulation(
                    reference=result.reference,
                    title=result.title,
                    content=result.content,
                    type=result.paragraph_type,
                    metadata=result.metadata
                )
        
        return None
    
    def get_regulatory_chain(self, reference: str) -> RegulatoryChain:
        """
        Récupère une chaîne réglementaire : IR + AMC + GM associés.
        
        Args:
            reference: Référence d'une règle IR (ex: "ORO.FTL.110")
        
        Returns:
            RegulatoryChain contenant IR, AMC et GM
        
        Example:
            >>> tools.get_regulatory_chain("ORO.FTL.110")
            RegulatoryChain(
                ir=Regulation(...),
                amcs=[Regulation(...), ...],
                gms=[Regulation(...), ...]
            )
        """
        chain = RegulatoryChain()
        
        # Nettoyer la référence (enlever les préfixes AMC/GM si présents)
        clean_ref = re.sub(r'^(AMC|GM)\d+\s+', '', reference)
        
        # 1. Récupérer l'IR
        chain.ir = self.get_regulation(clean_ref)
        
        # 2. Chercher les AMC associés
        # Pattern: "AMC" suivi de la référence
        amc_results = self.embeddings_manager.search(
            f"AMC {clean_ref}",
            top_k=20,
            min_score=0.0
        )
        
        for result in amc_results:
            # Vérifier que c'est bien un AMC lié à cette référence
            if ("AMC" in result.reference and 
                clean_ref in result.reference and
                "AMC to IR" in result.paragraph_type):
                
                reg = Regulation(
                    reference=result.reference,
                    title=result.title,
                    content=result.content,
                    type=result.paragraph_type,
                    metadata=result.metadata
                )
                chain.amcs.append(reg)
        
        # 3. Chercher les GM associés
        gm_results = self.embeddings_manager.search(
            f"GM {clean_ref}",
            top_k=20,
            min_score=0.0
        )
        
        for result in gm_results:
            # Vérifier que c'est bien un GM lié à cette référence
            if ("GM" in result.reference and 
                clean_ref in result.reference and
                "GM to IR" in result.paragraph_type):
                
                reg = Regulation(
                    reference=result.reference,
                    title=result.title,
                    content=result.content,
                    type=result.paragraph_type,
                    metadata=result.metadata
                )
                chain.gms.append(reg)
        
        return chain
    
    def get_tool_schemas(self) -> list[dict]:
        """Retourne les schémas MCP pour ces tools"""
        return [
            {
                "name": "get_regulation",
                "description": (
                    "Retrieve a specific EASA regulation by its exact reference. "
                    "Use this when you know the exact regulation reference "
                    "(e.g., 'ORO.FTL.110', 'AMC1 ORO.FTL.110')."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Exact regulation reference (e.g., 'ORO.FTL.110', 'AMC1 ARO.GEN.120(a)')"
                        }
                    },
                    "required": ["reference"]
                }
            },
            {
                "name": "get_regulatory_chain",
                "description": (
                    "Get a complete regulatory chain for an IR (Implementing Rule). "
                    "Returns the IR and all associated AMC (Acceptable Means of Compliance) "
                    "and GM (Guidance Material). Useful for understanding all guidance "
                    "related to a specific regulation."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "IR reference (e.g., 'ORO.FTL.110')"
                        }
                    },
                    "required": ["reference"]
                }
            }
        ]

