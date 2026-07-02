import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from memory.memory_layer import MemoryLayer

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, memory_layer: MemoryLayer, settings: Any) -> None:
        self.memory_layer = memory_layer
        self.settings = settings

    @abstractmethod
    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke the agent with a message and history."""
        pass

    async def _build_memory_context(self, user_id: str, query: str) -> str:
        """Build memory context from both stores.

        Memory retrieval failures are logged but do not block the agent
        from responding — it just proceeds without memory context.
        """
        try:
            memory_data = await self.memory_layer.read(user_id, query)
        except Exception as exc:
            logger.warning(
                "Memory retrieval failed for user=%s, proceeding without context: %s",
                user_id, exc,
            )
            return "No relevant memories found."

        context_parts: List[str] = []

        if memory_data["semantic"]:
            context_parts.append("## Relevant Past Interactions")
            for item in memory_data["semantic"]:
                context_parts.append(
                    f"- {item['content']} (from {item['metadata'].get('agent_id', 'unknown')})"
                )

        if memory_data["graph"]:
            context_parts.append("\n## Past Decisions & Patterns")
            for item in memory_data["graph"]:
                context_parts.append(f"- {item['content']} (from {item['agent_id']})")

        return "\n".join(context_parts) if context_parts else "No relevant memories found."