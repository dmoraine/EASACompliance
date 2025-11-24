"""
EASA Compliance Parser Package
===============================

Package pour extraire, parser et rechercher dans les règlements EASA.
Optimisé pour l'intégration avec des systèmes RAG (Retrieval Augmented Generation).

Usage:
    from easacompliance import EASAParser, Topic, TopicType
    from easacompliance import EmbeddingsManager, SearchResult
    
    # Parser
    parser = EASAParser("regulations.xml")
    topic = parser.get_topic_by_reference("ORO.FTL.110")
    
    # Embeddings
    manager = EmbeddingsManager("embeddings.db")
    results = manager.search("flight time limitations", top_k=5)
"""

from .parser import EASAParser, Topic, TopicType
from .embeddings import EmbeddingsManager, SearchResult

# LLM wrappers (optional, only if crewai is installed)
try:
    from .llm import HyperbolicLLM
    _has_llm = True
except ImportError:
    _has_llm = False

__version__ = "2.0.0"
__author__ = "Didier"
__all__ = [
    "EASAParser",
    "Topic",
    "TopicType",
    "EmbeddingsManager",
    "SearchResult",
]

# Add LLM to exports if available
if _has_llm:
    __all__.append("HyperbolicLLM")

