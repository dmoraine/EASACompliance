"""
Custom LLM wrappers for EASA Compliance tools
==============================================

This module provides custom LLM implementations for providers that don't
work well with the default litellm integration in CrewAI.

Usage:
    from easacompliance.llm import HyperbolicLLM, OllamaLLM
    
    # For Hyperbolic
    llm = HyperbolicLLM(
        model="deepseek-ai/DeepSeek-V3",
        api_key="your-key",
        base_url="https://api.hyperbolic.xyz/v1"
    )
    
    # For Ollama (local)
    llm = OllamaLLM(
        model="qwen3:14b",
        base_url="http://localhost:11434/v1"
    )
"""

from .hyperbolic import HyperbolicLLM
from .ollama import OllamaLLM

__all__ = ["HyperbolicLLM", "OllamaLLM"]

