"""
MCP Server EASA - Main Module
"""

__version__ = "1.0.0"
__author__ = "Didier"

from .config import ServerConfig, DEFAULT_CONFIG
from .schemas import (
    Regulation,
    RegulatoryChain,
    CategoryInfo,
    ComplianceResult,
    Statistics,
    RegulationType,
)

__all__ = [
    "ServerConfig",
    "DEFAULT_CONFIG",
    "Regulation",
    "RegulatoryChain",
    "CategoryInfo",
    "ComplianceResult",
    "Statistics",
    "RegulationType",
]

