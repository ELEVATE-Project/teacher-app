"""
Base Tool Class
===============

Abstract base class for all orchestrator tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseTool(ABC):
    """
    Abstract base class for orchestrator tools.
    
    All tools should inherit from this class and implement the required methods.
    """
    
    name: str = "base_tool"
    description: str = "Base tool description"
    
    @abstractmethod
    async def run(self, query: str, context: Optional[dict] = None) -> Any:
        """
        Execute the tool with the given query and context.
        
        Args:
            query: The main input/topic for the tool
            context: Optional context dictionary
        
        Returns:
            Tool-specific output
        """
        pass
    
    def run_sync(self, query: str, context: Optional[dict] = None) -> Any:
        """Synchronous version of run()."""
        import asyncio
        return asyncio.run(self.run(query, context))
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
