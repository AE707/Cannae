import logging
from typing import List, Dict, Any

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


COACH_SYSTEM_PROMPT = """You are the Cannae Coach agent - an accountability partner focused on goal tracking, behavioral loops, and habit systems.

Your purpose is to help the user follow through on commitments by connecting current actions to past patterns, embodying the Cannae philosophy: outthink larger forces through superior preparation and memory.

You operate with perfect recall of past commitments and their outcomes. When responding:
- Be warm but challenging - ask the hard questions others avoid
- Reference past commitments and patterns from memory when relevant
- Focus on accountability, follow-through, and behavioral consistency
- No vague encouragement - be specific about what worked and what didn't
- Every response surfaces one past commitment before responding to a new one
- If discussion reveals need for strategic adjustment, end with "[HANDOFF→CEO]"
- If discussion reveals need for SEO optimization, end with "[HANDOFF→SEO]"
- If discussion reveals need for financial analysis, end with "[HANDOFF→CFO]"

Your memory spans all interactions, allowing you to spot patterns of follow-through and avoidance the user might miss. You understand that accountability is about creating systems that make progress inevitable, not relying on willpower alone.

Remember: The best accountability systems create positive feedback loops over time."""


class CoachAgent(BaseAgent):
    """Coach agent for accountability and goal tracking."""

    def __init__(self, memory_layer: Any, settings: Any) -> None:
        super().__init__(memory_layer, settings)
        self.llm_service = LLMService()

    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke Coach agent with message and history.

        LLM errors are propagated to the caller. Memory write failures
        are logged but do not prevent returning the response.
        """
        memory_context = await self._build_memory_context(user_id, message)

        formatted_history: List[Dict[str, str]] = []
        for item in history:
            formatted_history.append({
                "role": item.get("role", "user"),
                "content": item.get("content", ""),
            })

        formatted_history.insert(0, {
            "role": "system",
            "content": f"{COACH_SYSTEM_PROMPT}\n\n## Memory Context\n{memory_context}",
        })

        formatted_history.append({
            "role": "user",
            "content": message,
        })

        response = await self._call_llm_api(formatted_history)

        try:
            await self.memory_layer.write(
                user_id=user_id,
                content=message,
                agent_id="coach",
                metadata={"type": "query", "response_length": len(response)},
            )
        except Exception as exc:
            logger.error("Coach agent memory write failed for user=%s: %s", user_id, exc)

        return response

    async def _call_llm_api(self, messages: List[Dict[str, str]]) -> str:
        """Call LLM API with formatted messages.

        Raises LLMServiceError on failure.
        """
        response = await self.llm_service.create_message(
            messages=messages,
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.7
        )
        return response["content"]
    agent_id = "coach"
    system_prompt = COACH_SYSTEM_PROMPT
