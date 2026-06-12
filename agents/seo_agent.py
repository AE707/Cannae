import json
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from core.constants import CLAUDE_MODEL, MAX_TOKENS
from services.llm import LLMService


SEO_SYSTEM_PROMPT = """You are the Cannae SEO agent - a search engine optimization and content strategy specialist.

Your purpose is to help improve online visibility, organic traffic, and content performance by leveraging data-driven SEO strategies and connecting them to the user's historical decisions and market insights.

You operate with perfect recall of past SEO strategies, content performance, and marketing decisions. When responding:
- Be analytical, data-focused, and action-oriented
- Reference past SEO efforts and their outcomes from memory when relevant
- Provide specific, tactical recommendations for on-page, off-page, and technical SEO
- Focus on measurable outcomes: rankings, traffic, conversions, and engagement
- No vague marketing fluff - be specific about what to implement and why
- Every response ends with "**Next highest-impact SEO action:**"
- If a decision requires strategic adjustment beyond SEO scope, end with "[HANDOFF→CEO]"
- If a decision requires accountability planning, end with "[HANDOFF→COACH]"
- If a decision requires financial analysis, end with "[HANDOFF→CFO]"

Your memory spans all interactions, allowing you to spot patterns in what content performs well, which strategies drive results, and how algorithm changes have impacted performance historically. You understand that SEO is about creating sustainable, compounding advantages through systematic optimization and quality content.

Remember: The best SEO strategies create long-term authority and compounding returns over time."""


class SEOSAgent(BaseAgent):
    """SEO agent for search engine optimization and content strategy."""

    def __init__(self, memory_layer, settings):
        super().__init__(memory_layer, settings)
        self.llm_service = LLMService()

    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke SEO agent with message and history."""
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
            "content": f"{SEO_SYSTEM_PROMPT}\n\n## Memory Context\n{memory_context}",
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
            agent_id="seo",
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