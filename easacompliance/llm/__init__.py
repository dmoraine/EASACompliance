"""
Custom LLM wrappers for EASA Compliance tools
==============================================

This module provides custom LLM implementations for providers that don't
work well with the default litellm integration in CrewAI.

Usage:
    from easacompliance.llm import HyperbolicLLM
    
    llm = HyperbolicLLM(
        model="deepseek-ai/DeepSeek-V3",
        api_key="your-key",
        base_url="https://api.hyperbolic.xyz/v1"
    )
"""

from .hyperbolic import HyperbolicLLM

__all__ = ["HyperbolicLLM"]

