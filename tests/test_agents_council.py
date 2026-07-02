"""Tests for agents/council.py — routing logic and handoff detection."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.council import Council, CouncilState


@pytest.fixture
def council():
    """Create a Council instance with mocked dependencies, bypassing __init__."""
    c = Council.__new__(Council)
    c.settings = MagicMock()
    c.memory_layer = MagicMock()
    c.memory_layer.read = AsyncMock(return_value={"semantic": [], "graph": []})
    c.memory_layer.write = AsyncMock()
    c.ceo_agent = MagicMock()
    c.ceo_agent.invoke = AsyncMock(return_value="CEO response")
    c.coach_agent = MagicMock()
    c.coach_agent.invoke = AsyncMock(return_value="Coach response")
    c.seo_agent = MagicMock()
    c.seo_agent.invoke = AsyncMock(return_value="SEO response")
    c.cfo_agent = MagicMock()
    c.cfo_agent.invoke = AsyncMock(return_value="CFO response")
    c.graph = MagicMock()
    return c


def make_state(**overrides) -> CouncilState:
    """Helper to create a CouncilState with defaults."""
    defaults = {
        "user_id": "test_user",
        "message": "",
        "history": [],
        "memory_context": "",
        "agent_choice": "ceo",
        "ceo_response": "",
        "coach_response": "",
        "seo_response": "",
        "cfo_response": "",
        "handoff_to": "",
        "final_response": "",
    }
    defaults.update(overrides)
    return defaults


class TestRouting:
    """Test the _route_to_agent keyword-based routing logic."""

    def test_routes_to_coach_for_habit_keywords(self, council):
        state = make_state(message="I need to build a daily habit for writing")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "coach"

    def test_routes_to_coach_for_accountability(self, council):
        state = make_state(message="Help me with accountability for my goals")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "coach"

    def test_routes_to_coach_for_commitment(self, council):
        state = make_state(message="I made a commitment to exercise daily")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "coach"

    def test_routes_to_ceo_for_strategy(self, council):
        state = make_state(message="What's the best strategy for entering a new market?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "ceo"

    def test_routes_to_ceo_for_decision_making(self, council):
        state = make_state(message="Help me decide between two directions for the company")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "ceo"

    def test_routes_to_ceo_for_resource_allocation(self, council):
        state = make_state(message="How should I allocate our limited capital?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "ceo"

    def test_routes_to_seo_for_search_optimization(self, council):
        state = make_state(message="How can I improve our SEO ranking on Google?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "seo"

    def test_routes_to_seo_for_keyword_research(self, council):
        state = make_state(message="What keyword should I target for organic traffic?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "seo"

    def test_routes_to_cfo_for_financial(self, council):
        state = make_state(message="What's our budget forecast for next quarter?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "cfo"

    def test_routes_to_cfo_for_revenue(self, council):
        state = make_state(message="Analyze our revenue and profit margins")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "cfo"

    def test_defaults_to_coach_for_ambiguous(self, council):
        state = make_state(message="Hello, how are you?")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "coach"

    def test_routing_is_case_insensitive(self, council):
        state = make_state(message="My STRATEGY needs a DECISION")
        result = council._route_to_agent(state)
        assert result["agent_choice"] == "ceo"


class TestHandoffCheck:
    """Test the _handoff_check method for detecting handoff markers."""

    def test_ceo_handoff_to_coach(self, council):
        state = make_state(ceo_response="Here's my analysis. [HANDOFF\u2192COACH]")
        result = council._handoff_check(state)
        assert result["handoff_to"] == "coach"

    def test_ceo_handoff_to_seo(self, council):
        state = make_state(ceo_response="Needs SEO work [HANDOFF\u2192SEO]")
        result = council._handoff_check(state)
        assert result["handoff_to"] == "seo"

    def test_ceo_handoff_to_cfo(self, council):
        state = make_state(ceo_response="Financial review needed [HANDOFF\u2192CFO]")
        result = council._handoff_check(state)
        assert result["handoff_to"] == "cfo"

    def test_coach_handoff_to_ceo(self, council):
        state = make_state(coach_response="Strategic pivot needed [HANDOFF\u2192CEO]")
        result = council._handoff_check(state)
        assert result["handoff_to"] == "ceo"

    def test_coach_handoff_to_seo(self, council):
        state = make_state(coach_response="SEO review [HANDOFF\u2192SEO]")
        result = council._handoff_check(state)
        assert result["handoff_to"] == "seo"

    def test_no_handoff_when_no_marker(self, council):
        state = make_state(ceo_response="Just a normal response without markers")
        result = council._handoff_check(state)
        assert result["handoff_to"] == ""

    def test_no_handoff_when_empty_responses(self, council):
        state = make_state()
        result = council._handoff_check(state)
        assert result["handoff_to"] == ""


class TestShouldHandoff:
    """Test the _should_handoff routing decision."""

    def test_returns_ceo_for_ceo_handoff(self, council):
        state = make_state(handoff_to="ceo")
        assert council._should_handoff(state) == "ceo"

    def test_returns_coach_for_coach_handoff(self, council):
        state = make_state(handoff_to="coach")
        assert council._should_handoff(state) == "coach"

    def test_returns_seo_for_seo_handoff(self, council):
        state = make_state(handoff_to="seo")
        assert council._should_handoff(state) == "seo"

    def test_returns_cfo_for_cfo_handoff(self, council):
        state = make_state(handoff_to="cfo")
        assert council._should_handoff(state) == "cfo"

    def test_returns_end_for_no_handoff(self, council):
        state = make_state(handoff_to="")
        assert council._should_handoff(state) == "end"


class TestChooseAgent:
    """Test the _choose_agent conditional edge."""

    def test_returns_agent_choice(self, council):
        state = make_state(agent_choice="ceo")
        assert council._choose_agent(state) == "ceo"

    def test_returns_coach(self, council):
        state = make_state(agent_choice="coach")
        assert council._choose_agent(state) == "coach"


class TestWriteMemory:
    """Test the _write_memory node for final response selection."""

    @pytest.mark.asyncio
    async def test_selects_ceo_response_when_no_handoff(self, council):
        state = make_state(
            agent_choice="ceo",
            ceo_response="CEO says this",
            handoff_to=""
        )
        result = await council._write_memory(state)
        assert result["final_response"] == "CEO says this"

    @pytest.mark.asyncio
    async def test_selects_coach_response_when_no_handoff(self, council):
        state = make_state(
            agent_choice="coach",
            coach_response="Coach says that",
            handoff_to=""
        )
        result = await council._write_memory(state)
        assert result["final_response"] == "Coach says that"

    @pytest.mark.asyncio
    async def test_selects_handoff_agent_response(self, council):
        state = make_state(
            agent_choice="ceo",
            ceo_response="Initial CEO",
            coach_response="Coach follow-up",
            handoff_to="coach"
        )
        result = await council._write_memory(state)
        assert result["final_response"] == "Coach follow-up"

    @pytest.mark.asyncio
    async def test_writes_to_memory_layer(self, council):
        state = make_state(
            agent_choice="ceo",
            ceo_response="Response",
            handoff_to=""
        )
        await council._write_memory(state)
        council.memory_layer.write.assert_called_once()
