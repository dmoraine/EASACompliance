"""
MCP Server EASA - Schémas de données

Définit les structures de données utilisées par le serveur MCP.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class RegulationType(str, Enum):
    """Types de régulation EASA"""
    IR = "IR (Implementing rule);"
    AMC = "AMC to IR (Acceptable means of compliance to implementing rule);"
    GM_IR = "GM to IR (Guidance material to implementing rule);"
    CS = "CS (Certification specification);"
    GM_CS = "GM to CS (Guidance material to certification specification);"
    EASY_ACCESS = "Easy access rules;"
    OTHER = "Other"


@dataclass
class Regulation:
    """Représente une régulation EASA"""
    reference: str
    title: str
    content: str
    type: str
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        data = asdict(self)
        # Ne pas inclure metadata si vide
        if not data.get('metadata'):
            data.pop('metadata', None)
        # Ne pas inclure score si None
        if data.get('score') is None:
            data.pop('score', None)
        return data
    
    @property
    def category(self) -> str:
        """Extrait la catégorie de la référence"""
        if not self.reference or '.' not in self.reference:
            return "Unknown"
        
        # Pour "AMC1 ORO.FTL.110", extraire "ORO.FTL"
        if ' ' in self.reference:
            ref_part = self.reference.split(' ')[-1]
        else:
            ref_part = self.reference
        
        parts = ref_part.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return ref_part


@dataclass
class RegulatoryChain:
    """Chaîne réglementaire : IR + AMC + GM"""
    ir: Optional[Regulation] = None
    amcs: List[Regulation] = None
    gms: List[Regulation] = None
    
    def __post_init__(self):
        if self.amcs is None:
            self.amcs = []
        if self.gms is None:
            self.gms = []
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            "ir": self.ir.to_dict() if self.ir else None,
            "amcs": [amc.to_dict() for amc in self.amcs],
            "gms": [gm.to_dict() for gm in self.gms],
            "total_items": 1 + len(self.amcs) + len(self.gms) if self.ir else len(self.amcs) + len(self.gms)
        }


@dataclass
class CategoryInfo:
    """Informations sur une catégorie"""
    category: str
    count: int
    description: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        data = asdict(self)
        if not data.get('description'):
            data.pop('description', None)
        return data


@dataclass
class ComplianceResult:
    """Résultat de validation de conformité"""
    score: float  # 0-1
    relevant_regulations: List[Regulation]
    gaps: List[str]
    recommendations: List[str]
    summary: str
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            "score": self.score,
            "relevant_regulations": [r.to_dict() for r in self.relevant_regulations],
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "summary": self.summary,
            "compliance_level": self._get_compliance_level()
        }
    
    def _get_compliance_level(self) -> str:
        """Détermine le niveau de conformité"""
        if self.score >= 0.8:
            return "HIGH"
        elif self.score >= 0.6:
            return "MEDIUM"
        elif self.score >= 0.4:
            return "LOW"
        else:
            return "VERY_LOW"


@dataclass
class Statistics:
    """Statistiques de la base réglementaire"""
    total_regulations: int
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    db_size_mb: float
    model_name: str
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return asdict(self)

