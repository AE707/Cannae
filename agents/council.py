from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END

from agents.ceo_agent import CEOAgent
from agents.coach_agent import CoachAgent
from core.config import get_settings
from memory.memory_layer import MemoryLayer


class CouncilState(TypedDict):
    """State shared across all nodes in the council graph."""
    user_id: str
    message: str
    history: list
    memory_context: str
    agent_choice: Literal["ceo", "coach", "seo", "cfo"]  # Which agent to route to
    ceo_response: str
    coach_response: str
    seo_response: str
    cfo_response: str
    handoff_to: Literal["ceo", "coach", "seo", "cfo", ""]
    final_response: str


class Council:
    """LangGraph orchestration for all agents."""

    def __init__(self):
        self.settings = get_settings()
        self.memory_layer = MemoryLayer(self.settings)
        self.ceo_agent = CEOAgent(self.memory_layer, self.settings)
        self.coach_agent = CoachAgent(self.memory_layer, self.settings)
        self.seo_agent = SEOSAgent(self.memory_layer, self.settings)
        self.cfo_agent = CFOAgent(self.memory_layer, self.settings)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for agent orchestration."""
        workflow = StateGraph(CouncilState)

        # Add nodes
        workflow.add_node("retrieve_memory", self._retrieve_memory)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("ceo_node", self._ceo_node)
        workflow.add_node("coach_node", self._coach_node)
        workflow.add_node("seo_node", self._seo_node)
        workflow.add_node("cfo_node", self._cfo_node)
        workflow.add_node("handoff_check", self._handoff_check)
        workflow.add_node("write_memory", self._write_memory)

        # Set entry point
        workflow.set_entry_point("retrieve_memory")

        # Add edges
        workflow.add_edge("retrieve_memory", "route_to_agent")
        workflow.add_conditional_edges(
            "route_to_agent",
            self._choose_agent,
            {
                "ceo": "ceo_node",
                "coach": "coach_node",
                "seo": "seo_node",
                "cfo": "cfo_node",
            },
        )
        workflow.add_edge("ceo_node", "handoff_check")
        workflow.add_edge("coach_node", "handoff_check")
        workflow.add_edge("seo_node", "handoff_check")
        workflow.add_edge("cfo_node", "handoff_check")
        workflow.add_conditional_edges(
            "handoff_check",
            self._should_handoff,
            {
                "ceo": "ceo_node",
                "coach": "coach_node",
                "seo": "seo_node",
                "cfo": "cfo_node",
                "end": "write_memory",
            },
        )
        workflow.add_edge("write_memory", END)

        return workflow.compile()

    async def _retrieve_memory(self, state: CouncilState) -> CouncilState:
        """Retrieve memory context for the user's message."""
        memory_data = await self.memory_layer.read(
            state["user_id"], state["message"]
        )

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

        state["memory_context"] = (
            "\n".join(context_parts) if context_parts else "No relevant memories found."
        )
        return state

    def _route_to_agent(self, state: CouncilState) -> CouncilState:
        """Decide which agent should handle the message based on content."""
        # Routing logic based on message content
        seo_keywords = [
            "seo", "search", "optimization", "ranking", "traffic", "organic",
            "keyword", "backlink", "content", "on-page", "off-page", "technical seo",
            "serp", "google", "bing", "algorithm", "CTR", "impressions"
        ]

        cfo_keywords = [
            "finance", "financial", "budget", "money", "cost", "revenue", "profit",
            "investment", "roi", "cash flow", "expense", "accounting", "tax",
            "forecast", "financial statement", "balance sheet", "income statement",
            "cfo", "chief financial officer"
        ]

        coach_keywords = [
            "habit", "goal", "accountability", "follow through", "commitment",
            "consistency", "discipline", "routine", "behavior", "pattern",
            "track", "progress", "metric", "kpi"
        ]

        # Default to CEO for strategy-related content
        strategy_keywords = [
            "strategy", "strategic", "decision", "decide", "plan", "planning",
            "resource", "capital", "investment", "market", "competition",
            "goal", "objective", "priority", "prioritize", "leverage",
            "system", "systemic", "organization", "structure", "ceo",
            "chief executive officer"
        ]

        message_lower = state["message"].lower()

        # Check for SEO keywords first
        if any(keyword in message_lower for keyword in seo_keywords):
            state["agent_choice"] = "seo"
        # Check for CFO keywords
        elif any(keyword in message_lower for keyword in cfo_keywords):
            state["agent_choice"] = "cfo"
        # Check for Coach keywords
        elif any(keyword in message_lower for keyword in coach_keywords):
            state["agent_choice"] = "coach"
        # Default to CEO for strategy-related content
        elif any(keyword in message_lower for keyword in strategy_keywords):
            state["agent_choice"] = "ceo"
        else:
            # Default to Coach for general accountability/productivity topics
            state["agent_choice"] = "coach"

        return state

    def _choose_agent(self, state: CouncilState) -> Literal["ceo", "coach"]:
        """Choose agent based on routing decision."""
        return state["agent_choice"]

    async def _ceo_node(self, state: CouncilState) -> CouncilState:
        """Execute CEO agent."""
        state["ceo_response"] = await self.ceo_agent.invoke(
            state["user_id"],
            state["message"],
            state["history"],
        )
        return state

    async def _coach_node(self, state: CouncilState) -> CouncilState:
        """Execute Coach agent."""
        state["coach_response"] = await self.coach_agent.invoke(
            state["user_id"],
            state["message"],
            state["history"],
        )
        return state

    async def _seo_node(self, state: CouncilState) -> CouncilState:
        """Execute SEO agent."""
        state["seo_response"] = await self.seo_agent.invoke(
            state["user_id"],
            state["message"],
            state["history"],
        )
        return state

    async def _cfo_node(self, state: CouncilState) -> CouncilState:
        """Execute CFO agent."""
        state["cfo_response"] = await self.cfo_agent.invoke(
            state["user_id"],
            state["message"],
            state["history"],
        )
        return state

    def _handoff_check(self, state: CouncilState) -> CouncilState:
        """Check if handoff is needed based on agent responses."""
        # Check CEO response for handoffs
        if state["ceo_response"]:
            if "[HANDOFF→COACH]" in state["ceo_response"]:
                state["handoff_to"] = "coach"
            elif "[HANDOFF→SEO]" in state["ceo_response"]:
                state["handoff_to"] = "seo"
            elif "[HANDOFF→CFO]" in state["ceo_response"]:
                state["handoff_to"] = "cfo"
        # Check coach response for handoffs
        elif state["coach_response"]:
            if "[HANDOFF→CEO]" in state["coach_response"]:
                state["handoff_to"] = "ceo"
            elif "[HANDOFF→SEO]" in state["coach_response"]:
                state["handoff_to"] = "seo"
            elif "[HANDOFF→CFO]" in state["coach_response"]:
                state["handoff_to"] = "cfo"
        # Check SEO response for handoffs
        elif state["seo_response"]:
            if "[HANDOFF→CEO]" in state["seo_response"]:
                state["handoff_to"] = "ceo"
            elif "[HANDOFF→COACH]" in state["seo_response"]:
                state["handoff_to"] = "coach"
            elif "[HANDOFF→CFO]" in state["seo_response"]:
                state["handoff_to"] = "cfo"
        # Check CFO response for handoffs
        elif state["cfo_response"]:
            if "[HANDOFF→CEO]" in state["cfo_response"]:
                state["handoff_to"] = "ceo"
            elif "[HANDOFF→COACH]" in state["cfo_response"]:
                state["handoff_to"] = "coach"
            elif "[HANDOFF→SEO]" in state["cfo_response"]:
                state["handoff_to"] = "seo"
        else:
            state["handoff_to"] = ""

        return state

    def _should_handoff(self, state: CouncilState) -> Literal["ceo", "coach", "seo", "cfo", "end"]:
        """Determine next step after handoff check."""
        if state["handoff_to"] == "ceo":
            return "ceo"
        elif state["handoff_to"] == "coach":
            return "coach"
        elif state["handoff_to"] == "seo":
            return "seo"
        elif state["handoff_to"] == "cfo":
            return "cfo"
        else:
            return "end"

    async def _write_memory(self, state: CouncilState) -> CouncilState:
        """Write the interaction to memory."""
        # Determine which response to use as final
        if state["handoff_to"] == "ceo":
            state["final_response"] = state["ceo_response"]
        elif state["handoff_to"] == "coach":
            state["final_response"] = state["coach_response"]
        elif state["handoff_to"] == "seo":
            state["final_response"] = state["seo_response"]
        elif state["handoff_to"] == "cfo":
            state["final_response"] = state["cfo_response"]
        else:
            # If no handoff, use the initially selected agent's response
            if state["agent_choice"] == "ceo":
                state["final_response"] = state["ceo_response"]
            elif state["agent_choice"] == "coach":
                state["final_response"] = state["coach_response"]
            elif state["agent_choice"] == "seo":
                state["final_response"] = state["seo_response"]
            elif state["agent_choice"] == "cfo":
                state["final_response"] = state["cfo_response"]

        # Write to memory
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

    async def invoke(
        self, user_id: str, message: str, history: list
    ) -> str:
        """Invoke the council with a message and history."""
        initial_state = CouncilState(
            user_id=user_id,
            message=message,
            history=history,
            memory_context="",
            agent_choice="ceo",  # Default, will be overridden by routing
            ceo_response="",
            coach_response="",
            handoff_to="",
            final_response="",
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]