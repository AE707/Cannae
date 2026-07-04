"""Tests for memory/graph_memory.py"""
import pytest
import asyncio
from memory.graph_memory import GraphMemory


class TestGraphMemoryStubMode:
    """Tests for GraphMemory in stub mode (no API key)."""

    @pytest.fixture
    def graph(self):
        return GraphMemory(mem0_api_key=None)

    def test_stub_mode_enabled_when_no_key(self):
        g = GraphMemory(mem0_api_key=None)
        assert g._stub_mode is True

    def test_stub_mode_disabled_when_key_provided(self):
        g = GraphMemory(mem0_api_key="some-key")
        assert g._stub_mode is False

    @pytest.mark.asyncio
    async def test_add_decision_stub_returns_id(self, graph):
        result = await graph.add_decision(
            user_id="user1", content="Launch MVP", agent_id="ceo"
        )
        assert isinstance(result, str)
        assert "stub_decision" in result
        assert "user1" in result
        assert "ceo" in result

    @pytest.mark.asyncio
    async def test_get_context_stub_returns_list(self, graph):
        results = await graph.get_context(user_id="user1", query="strategy")
        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_context_stub_has_expected_structure(self, graph):
        results = await graph.get_context(user_id="user1", query="anything")
        for item in results:
            assert "id" in item
            assert "content" in item
            assert "agent_id" in item
            assert "timestamp" in item

    @pytest.mark.asyncio
    async def test_get_context_stub_agent_ids(self, graph):
        results = await graph.get_context(user_id="user1", query="test")
        agent_ids = [r["agent_id"] for r in results]
        assert "ceo" in agent_ids
        assert "coach" in agent_ids


class TestGraphMemoryWithKey:
    """Tests for GraphMemory with an API key (non-stub mode)."""

    @pytest.fixture
    def graph(self):
        return GraphMemory(mem0_api_key="test-key")

    @pytest.mark.asyncio
    async def test_add_decision_stores_decision(self, graph):
        result = await graph.add_decision(
            user_id="user1", content="Hire a designer", agent_id="ceo"
        )
        assert isinstance(result, str)
        assert "decision" in result

    @pytest.mark.asyncio
    async def test_add_decision_creates_storage(self, graph):
        await graph.add_decision(
            user_id="user1", content="Focus on retention", agent_id="coach"
        )
        assert hasattr(graph, "_decisions")
        assert "user1" in graph._decisions
        assert len(graph._decisions["user1"]) == 1

    @pytest.mark.asyncio
    async def test_add_multiple_decisions(self, graph):
        await graph.add_decision("user1", "Decision A", "ceo")
        await graph.add_decision("user1", "Decision B", "coach")
        await graph.add_decision("user2", "Decision C", "ceo")

        assert len(graph._decisions["user1"]) == 2
        assert len(graph._decisions["user2"]) == 1

    @pytest.mark.asyncio
    async def test_decision_structure(self, graph):
        await graph.add_decision("user1", "Scale the team", "ceo")
        decision = graph._decisions["user1"][0]
        assert decision["content"] == "Scale the team"
        assert decision["agent_id"] == "ceo"
        assert "timestamp" in decision
        assert "id" in decision

    @pytest.mark.asyncio
    async def test_get_context_non_stub_returns_empty(self, graph):
        # Non-stub mode without real Mem0 integration returns empty
        results = await graph.get_context(user_id="user1", query="anything")
        assert results == []
