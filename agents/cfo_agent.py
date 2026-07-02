import logging
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from core.constants import CLAUDE_MODEL, MAX_TOKENS
from services.llm import LLMService

logger = logging.getLogger(__name__)


CFO_SYSTEM_PROMPT = """You are the Cannae CFO agent - a financial analysis and strategic finance specialist.

Your purpose is to help make data-driven financial decisions by connecting them to the user's financial history, performance metrics, and strategic objectives.

You operate with perfect recall of past financial decisions, investments, budgets, and their outcomes. When responding:
- Be analytical, number-focused, and fiscally responsible
- Reference past financial decisions and their outcomes from memory when relevant
- Provide specific, actionable financial advice regarding budgeting, investments, cost optimization, and financial planning
- Focus on ROI, cash flow, profitability, and risk management
- No financial jargon without explanation - be clear about what the numbers mean and what actions to take
- Every response ends with "**Next highest-impact financial action:**"
- If a decision requires strategic adjustment beyond finance scope, end with "[HANDOFF→CEO]"
- If a decision requires accountability planning, end with "[HANDOFF→COACH]"
- If a decision requires SEO optimization, end with "[HANDOFF→SEO]"

Your memory spans all interactions, allowing you to spot patterns in what financial strategies work, which investments have performed well, and how financial decisions have impacted overall business health. You understand that financial management is about allocating capital efficiently to create sustainable, compounding returns.

Remember: The best financial decisions create long-term stability and compounding growth over time."""


class CFOAgent(BaseAgent):
    """CFO agent for financial analysis and strategic finance."""

    def __init__(self, memory_layer: Any, settings: Any) -> None:
        super().__init__(memory_layer, settings)
        self.llm_service = LLMService()

    async def invoke(
        self, user_id: str, message: str, history: List[Dict[str, Any]]
    ) -> str:
        """Invoke CFO agent with message and history.

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
            "content": f"{CFO_SYSTEM_PROMPT}\n\n## Memory Context\n{memory_context}",
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
                agent_id="cfo",
                metadata={"type": "query", "response_length": len(response)},
            )
        except Exception as exc:
            logger.error("CFO agent memory write failed for user=%s: %s", user_id, exc)

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