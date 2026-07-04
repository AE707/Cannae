from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json

from core.config import get_settings
from memory.memory_layer import MemoryLayer


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, memory_layer: MemoryLayer, settings):
        self.memory_layer = memory_layer
        self.settings = settings

    @abstractmethod
    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke the agent with a message and history."""
        pass

    async def _build_memory_context(self, user_id: str, query: str) -> str:
        """Build memory context from both stores."""
        memory_data = await self.memory_layer.read(user_id, query)

        context_parts = []

        # Add semantic memory
        if memory_data["semantic"]:
            context_parts.append("## Relevant Past Interactions")
            for item in memory_data["semantic"]:
                context_parts.append(f"- {item['content']} (from {item['metadata'].get('agent_id', 'unknown')})")

        # Add graph memory
        if memory_data["graph"]:
            context_parts.append("\n## Past Decisions & Patterns")
            for item in memory_data["graph"]:
                context_parts.append(f"- {item['content']} (from {item['agent_id']})")

        return "\n".join(context_parts) if context_parts else "No relevant memories found."