import json
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from core.constants import CLAUDE_MODEL, MAX_TOKENS
from services.llm import LLMService


CEO_SYSTEM_PROMPT = """You are the Cannae CEO agent - a strategic advisor with full memory of the user's past decisions.

Your purpose is to help make high-leverage decisions by connecting them to the user's strategic history, embodying the Cannae philosophy: outthink larger forces through superior preparation and memory.

You operate with perfect recall of past decisions and their outcomes. When responding:
- Be direct, confident, and data-informed
- Think in systems and leverage, not tactics
- Reference past decisions from memory when relevant
- No filler, no hedging, no platitudes
- Every response ends with "**Next highest-leverage action:**"
- If a decision requires accountability planning, end with "[HANDOFF→COACH]"
- If a decision requires SEO optimization, end with "[HANDOFF→SEO]"
- If a decision requires financial analysis, end with "[HANDOFF→CFO]"

Your memory spans all interactions, allowing you to spot patterns and connect dots the user might miss. You understand that strategy is about allocating limited resources (time, attention, capital) to create maximum leverage.

Remember: The best decisions create compounding advantages over time."""


class CEOAgent(BaseAgent):
    """CEO agent for strategic decision-making."""

    def __init__(self, memory_layer, settings):
        super().__init__(memory_layer, settings)
        self.llm_service = LLMService()

    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke CEO agent with message and history."""
        # Build memory context
        memory_context = await self._build_memory_context(user_id, message)

        # Prepare conversation history
        formatted_history = []
        for item in history:
            formatted_history.append({
                "role": item.get("role", "user"),
                "content": item.get("content", ""),
            })

        # Add system message
        formatted_history.insert(0, {
            "role": "system",
            "content": f"{CEO_SYSTEM_PROMPT}\n\n## Memory Context\n{memory_context}",
        })

        # Add current message
        formatted_history.append({
            "role": "user",
            "content": message,
        })

        # Call LLM API
        response = await self._call_llm_api(formatted_history)

        # Write interaction to memory
        await self.memory_layer.write(
            user_id=user_id,
            content=message,
            agent_id="ceo",
            metadata={"type": "query", "response_length": len(response)},
        )

        return response

    async def _call_llm_api(self, messages: List[Dict[str, str]]) -> str:
        """Call LLM API with formatted messages."""
        response = await self.llm_service.create_message(
            messages=messages,
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.7
        )
        return response["content"]