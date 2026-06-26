"""
Chanakya Orchestrator Layer
===========================

LangGraph-based orchestrator for handling context, understanding queries,
and routing to appropriate tools.
"""

# Force import and patch for Google GenAI SDK to route through OpenRouter
try:
    import importlib
    import openrouter_patch
    importlib.reload(openrouter_patch)
except ImportError:
    pass

from .orchestrator import ChanakyaOrchestrator
from .tools import ActivityGeneratorTool
from .schemas import OrchestratorInput, OrchestratorOutput, ActivityOutput

__all__ = [
    "ChanakyaOrchestrator",
    "ActivityGeneratorTool",
    "OrchestratorInput",
    "OrchestratorOutput",
    "ActivityOutput",
]
