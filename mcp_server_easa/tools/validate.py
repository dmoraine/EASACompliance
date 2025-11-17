"""
MCP Server EASA - Validate Tools

Tools pour valider la conformité d'un texte avec les régulations EASA.
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
    from ..schemas import Regulation, ComplianceResult
    from ..config import ServerConfig
except ImportError:
    from mcp_server_easa.schemas import Regulation, ComplianceResult
    from mcp_server_easa.config import ServerConfig


class ValidateTools:
    """Tools de validation de conformité"""
    
    def __init__(self, config: ServerConfig):
        """
        Initialise les tools de validation.
        
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
    
    def validate_compliance(
        self,
        text: str,
        category: Optional[str] = None,
        top_k: int = 10,
        min_score: float = 0.3
    ) -> ComplianceResult:
        """
        Valide la conformité d'un texte avec les régulations EASA.
        
        Args:
            text: Texte à valider (manuel, procédure, etc.)
            category: Filtrer par catégorie spécifique (ex: "ORO.FTL")
            top_k: Nombre de régulations pertinentes à analyser
            min_score: Score minimum de pertinence
        
        Returns:
            ComplianceResult avec score, régulations pertinentes, gaps et recommandations
        
        Example:
            >>> tools.validate_compliance(
            ...     "Flight crew must not exceed 900 hours in a year",
            ...     category="ORO.FTL"
            ... )
            ComplianceResult(score=0.75, ...)
        """
        # Rechercher les régulations pertinentes
        results = self.embeddings_manager.search(
            query=text,
            top_k=top_k,
            min_score=min_score
        )
        
        # Filtrer par catégorie si demandé
        if category:
            results = [r for r in results if category in r.reference]
        
        # Convertir en Regulation
        regulations = []
        for result in results:
            reg = Regulation(
                reference=result.reference,
                title=result.title,
                content=result.content,
                type=result.paragraph_type,
                score=result.score,
                metadata=result.metadata
            )
            regulations.append(reg)
        
        # Calculer le score de conformité
        compliance_score = self._calculate_compliance_score(regulations)
        
        # Identifier les gaps
        gaps = self._identify_gaps(text, regulations)
        
        # Générer des recommandations
        recommendations = self._generate_recommendations(regulations, gaps)
        
        # Créer un résumé
        summary = self._generate_summary(compliance_score, regulations, gaps)
        
        return ComplianceResult(
            score=compliance_score,
            relevant_regulations=regulations,
            gaps=gaps,
            recommendations=recommendations,
            summary=summary
        )
    
    def _calculate_compliance_score(self, regulations: List[Regulation]) -> float:
        """
        Calcule un score de conformité basé sur les régulations trouvées.
        
        Score basé sur :
        - Nombre de régulations pertinentes trouvées
        - Scores de similarité moyens
        - Présence de régulations à haut score
        """
        if not regulations:
            return 0.0
        
        # Score moyen pondéré
        scores = [r.score for r in regulations if r.score is not None]
        if not scores:
            return 0.0
        
        avg_score = sum(scores) / len(scores)
        
        # Bonus si on a des scores très élevés (>0.7)
        high_score_count = sum(1 for s in scores if s >= 0.7)
        high_score_bonus = min(high_score_count * 0.1, 0.2)
        
        # Score final
        final_score = min(avg_score + high_score_bonus, 1.0)
        
        return round(final_score, 2)
    
    def _identify_gaps(self, text: str, regulations: List[Regulation]) -> List[str]:
        """
        Identifie les gaps potentiels de conformité.
        
        Cette fonction identifie les régulations importantes qui ne sont
        pas bien couvertes par le texte.
        """
        gaps = []
        
        # Gap 1: Pas assez de régulations pertinentes
        if len(regulations) < 3:
            gaps.append(
                "Limited relevant regulations found. "
                "Text may not cover key regulatory requirements."
            )
        
        # Gap 2: Scores de similarité faibles
        low_score_count = sum(1 for r in regulations if r.score and r.score < 0.5)
        if low_score_count > len(regulations) / 2:
            gaps.append(
                "Many regulations have low similarity scores. "
                "Text may not adequately address regulatory requirements."
            )
        
        # Gap 3: Types de régulations manquants
        types_found = set(r.type for r in regulations)
        if "AMC to IR" not in types_found:
            gaps.append(
                "No AMC (Acceptable Means of Compliance) found. "
                "Consider how compliance will be demonstrated."
            )
        
        if "GM to IR" not in types_found:
            gaps.append(
                "No GM (Guidance Material) found. "
                "Additional guidance may be needed for implementation."
            )
        
        return gaps
    
    def _generate_recommendations(
        self,
        regulations: List[Regulation],
        gaps: List[str]
    ) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        # Recommandations basées sur les régulations trouvées
        if regulations:
            top_reg = regulations[0]
            recommendations.append(
                f"Review {top_reg.reference}: {top_reg.title}"
            )
        
        # Recommandations basées sur les gaps
        if len(gaps) > 0:
            recommendations.append(
                "Address identified gaps to improve compliance coverage"
            )
        
        # Recommandations sur les AMC/GM
        has_ir = any("IR (Implementing rule)" in r.type for r in regulations)
        has_amc = any("AMC" in r.type for r in regulations)
        
        if has_ir and not has_amc:
            recommendations.append(
                "Consider reviewing associated AMC and GM for implementation guidance"
            )
        
        return recommendations
    
    def _generate_summary(
        self,
        score: float,
        regulations: List[Regulation],
        gaps: List[str]
    ) -> str:
        """Génère un résumé de l'analyse de conformité"""
        level = "HIGH" if score >= 0.8 else "MEDIUM" if score >= 0.6 else "LOW"
        
        summary_parts = [
            f"Compliance Level: {level} (score: {score:.2f})",
            f"Found {len(regulations)} relevant regulations",
        ]
        
        if gaps:
            summary_parts.append(f"Identified {len(gaps)} potential gaps")
        
        return ". ".join(summary_parts) + "."
    
    def get_tool_schema(self) -> dict:
        """Retourne le schéma MCP pour ce tool"""
        return {
            "name": "validate_compliance",
            "description": (
                "Validate compliance of a text (manual, procedure, policy) "
                "against EASA regulations. Returns a compliance score, relevant "
                "regulations, identified gaps, and recommendations. "
                "Useful for assessing if operational documentation meets "
                "regulatory requirements."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to validate (manual section, procedure, policy, etc.)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional: filter by specific category (e.g., 'ORO.FTL')",
                        "default": None
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant regulations to analyze (default: 10)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum relevance score (0-1, default: 0.3)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.3
                    }
                },
                "required": ["text"]
            }
        }

