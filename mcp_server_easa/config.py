"""
MCP Server EASA - Configuration
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration du serveur MCP EASA"""
    
    # Paths
    db_path: str = "easa_complete.db"
    xml_path: Optional[str] = None  # Optionnel, pour accès direct au XML
    
    # Modèle d'embeddings
    model_name: str = "all-MiniLM-L6-v2"
    
    # Limites
    max_search_results: int = 20
    default_top_k: int = 5
    min_score_default: float = 0.0
    
    # Cache
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 heure
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Charge la configuration depuis les variables d'environnement"""
        import os
        
        return cls(
            db_path=os.getenv("EASA_DB_PATH", "easa_complete.db"),
            xml_path=os.getenv("EASA_XML_PATH"),
            model_name=os.getenv("EASA_MODEL", "all-MiniLM-L6-v2"),
            max_search_results=int(os.getenv("EASA_MAX_RESULTS", "20")),
            enable_cache=os.getenv("EASA_CACHE", "true").lower() == "true",
        )
    
    def validate(self) -> None:
        """Valide la configuration"""
        db = Path(self.db_path)
        if not db.exists():
            raise FileNotFoundError(
                f"Base de données introuvable: {self.db_path}\n"
                f"Utilisez 'easacompliance/scripts/build_embeddings.py' pour la créer."
            )
        
        if self.xml_path:
            xml = Path(self.xml_path)
            if not xml.exists():
                raise FileNotFoundError(f"Fichier XML introuvable: {self.xml_path}")


# Configuration par défaut
DEFAULT_CONFIG = ServerConfig()

