from abc import ABC, abstractmethod
from typing import List, Dict, Any

from core.constants import CLAUDE_MODEL, MAX_TOKENS, AgentId
from memory.memory_layer import MemoryLayer
from services.llm import LLMService


class BaseAgent(ABC):
    """Base class for all agents.

    Subclasses only need to define `agent_id` and `system_prompt`.
    The invoke/LLM/memory logic lives here once.
    """

    agent_id: AgentId
    system_prompt: str

    def __init__(self, memory_layer: MemoryLayer, settings: Any) -> None:
        self.memory_layer = memory_layer
        self.settings = settings
        self.llm_service = LLMService()

    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke the agent with a message and conversation history."""
        memory_context = await self._build_memory_context(user_id, message)

        formatted_history = _format_history(history)

        # Prepend system message with memory context
        formatted_history.insert(0, {
            "role": "system",
            "content": f"{self.system_prompt}\n\n## Memory Context\n{memory_context}",
        })

        # Append current user message
        formatted_history.append({"role": "user", "content": message})

        response = await self._call_llm(formatted_history)

        await self.memory_layer.write(
            user_id=user_id,
            content=message,
            agent_id=self.agent_id,
            metadata={"type": "query", "response_length": len(response)},
        )

        return response

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the LLM service and return the text content."""
        response = await self.llm_service.create_message(
            messages=messages,
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.7,
        )
        return response["content"]

    async def _build_memory_context(self, user_id: str, query: str) -> str:
        """Build memory context string from both vector and graph stores."""
        memory_data = await self.memory_layer.read(user_id, query)
        return format_memory_context(memory_data)


# ------------------------------------------------------------------
# Module-level utilities (reusable outside agent classes)
# ------------------------------------------------------------------


def format_memory_context(memory_data: Dict[str, Any]) -> str:
    """Format raw memory data into a human-readable context string.

    Used by both BaseAgent._build_memory_context and Council._retrieve_memory.
    """
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


def _format_history(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Convert raw history dicts into the {role, content} format expected by the LLM."""
    return [
        {"role": item.get("role", "user"), "content": item.get("content", "")}
        for item in history
    ]