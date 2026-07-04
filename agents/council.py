from typing import Literal, TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent, format_memory_context
from core.config import get_settings
from core.constants import AgentId, HANDOFF_PREFIX, HANDOFF_TARGETS
from memory.memory_layer import MemoryLayer


class CouncilState(TypedDict):
    """State shared across all nodes in the council graph."""
    user_id: str
    message: str
    history: list
    memory_context: str
    agent_choice: AgentId
    response: str
    handoff_to: str  # AgentId or ""
    final_response: str


# Keyword routing configuration — single place to tune
_ROUTING_KEYWORDS: dict[AgentId, list[str]] = {
    "seo": [
        "seo", "search", "optimization", "ranking", "traffic", "organic",
        "keyword", "backlink", "content", "on-page", "off-page", "technical seo",
        "serp", "google", "bing", "algorithm", "ctr", "impressions",
    ],
    "cfo": [
        "finance", "financial", "budget", "money", "cost", "revenue", "profit",
        "investment", "roi", "cash flow", "expense", "accounting", "tax",
        "forecast", "financial statement", "balance sheet", "income statement",
        "cfo", "chief financial officer",
    ],
    "coach": [
        "habit", "goal", "accountability", "follow through", "commitment",
        "consistency", "discipline", "routine", "behavior", "pattern",
        "track", "progress", "metric", "kpi",
    ],
    "ceo": [
        "strategy", "strategic", "decision", "decide", "plan", "planning",
        "resource", "capital", "investment", "market", "competition",
        "goal", "objective", "priority", "prioritize", "leverage",
        "system", "systemic", "organization", "structure", "ceo",
        "chief executive officer",
    ],
}


def parse_handoff(response: str) -> Optional[AgentId]:
    """Extract a handoff target from an agent response, if present."""
    for marker_name, agent_id in HANDOFF_TARGETS.items():
        if f"{HANDOFF_PREFIX}{marker_name}]" in response:
            return agent_id
    return None


def route_message(message: str) -> AgentId:
    """Determine which agent should handle a message based on keyword matching."""
    message_lower = message.lower()
    # Check in priority order: seo, cfo, coach, ceo
    for agent_id in ("seo", "cfo", "coach", "ceo"):
        keywords = _ROUTING_KEYWORDS[agent_id]  # type: ignore[index]
        if any(kw in message_lower for kw in keywords):
            return agent_id  # type: ignore[return-value]
    return "coach"  # default


class Council:
    """LangGraph orchestration for all agents."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.memory_layer = MemoryLayer(self.settings)

        # Import here to avoid circular import at module level
        from agents.ceo_agent import CEOAgent
        from agents.coach_agent import CoachAgent
        from agents.seo_agent import SEOAgent
        from agents.cfo_agent import CFOAgent

        self._agents: dict[AgentId, BaseAgent] = {
            "ceo": CEOAgent(self.memory_layer, self.settings),
            "coach": CoachAgent(self.memory_layer, self.settings),
            "seo": SEOAgent(self.memory_layer, self.settings),
            "cfo": CFOAgent(self.memory_layer, self.settings),
        }
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for agent orchestration."""
        workflow = StateGraph(CouncilState)

        workflow.add_node("retrieve_memory", self._retrieve_memory)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_agent", self._execute_agent)
        workflow.add_node("handoff_check", self._handoff_check)
        workflow.add_node("write_memory", self._write_memory)

        workflow.set_entry_point("retrieve_memory")

        workflow.add_edge("retrieve_memory", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_agent")
        workflow.add_edge("execute_agent", "handoff_check")
        workflow.add_conditional_edges(
            "handoff_check",
            self._should_handoff,
            {"continue": "execute_agent", "end": "write_memory"},
        )
        workflow.add_edge("write_memory", END)

        return workflow.compile()

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    async def _retrieve_memory(self, state: CouncilState) -> CouncilState:
        """Retrieve memory context for the user's message."""
        memory_data = await self.memory_layer.read(state["user_id"], state["message"])
        state["memory_context"] = format_memory_context(memory_data)
        return state

    def _route_to_agent(self, state: CouncilState) -> CouncilState:
        """Decide which agent should handle the message."""
        state["agent_choice"] = route_message(state["message"])
        return state

    async def _execute_agent(self, state: CouncilState) -> CouncilState:
        """Execute the currently selected agent."""
        agent = self._agents[state["agent_choice"]]
        state["response"] = await agent.invoke(
            state["user_id"], state["message"], state["history"]
        )
        return state

    def _handoff_check(self, state: CouncilState) -> CouncilState:
        """Check if handoff is needed based on agent response."""
        target = parse_handoff(state["response"])
        if target and target != state["agent_choice"]:
            state["handoff_to"] = target
            state["agent_choice"] = target
        else:
            state["handoff_to"] = ""
        return state

    def _should_handoff(self, state: CouncilState) -> Literal["continue", "end"]:
        """Determine whether to continue with a handoff or finish."""
        return "continue" if state["handoff_to"] else "end"

    async def _write_memory(self, state: CouncilState) -> CouncilState:
        """Write the interaction to memory and set final response."""
        state["final_response"] = state["response"]

        await self.memory_layer.write(
            user_id=state["user_id"],
            content=state["message"],
            agent_id=state["agent_choice"],
            metadata={
                "type": "council_interaction",
                "handoff_occurred": bool(state["handoff_to"]),
                "handoff_to": state["handoff_to"],
                "response_length": len(state["final_response"]),
            },
        )
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def invoke(self, user_id: str, message: str, history: list) -> str:
        """Invoke the council with a message and history."""
        initial_state: CouncilState = {
            "user_id": user_id,
            "message": message,
            "history": history,
            "memory_context": "",
            "agent_choice": "ceo",
            "response": "",
            "handoff_to": "",
            "final_response": "",
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]
