"""Tests for agents/base_agent.py"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.base_agent import BaseAgent
from memory.memory_layer import MemoryLayer


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    async def invoke(self, user_id: str, message: str, history: list) -> str:
        return f"response to: {message}"


@pytest.fixture
def mock_memory_layer():
    ml = MagicMock(spec=MemoryLayer)
    ml.read = AsyncMock()
    return ml


@pytest.fixture
def agent(mock_memory_layer):
    settings = MagicMock()
    return ConcreteAgent(mock_memory_layer, settings)


class TestBaseAgentInit:
    def test_stores_memory_layer(self, agent, mock_memory_layer):
        assert agent.memory_layer is mock_memory_layer

    def test_stores_settings(self, agent):
        assert agent.settings is not None


class TestBuildMemoryContext:
    @pytest.mark.asyncio
    async def test_returns_no_memories_when_empty(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {"semantic": [], "graph": []}
        result = await agent._build_memory_context("user1", "test query")
        assert result == "No relevant memories found."

    @pytest.mark.asyncio
    async def test_includes_semantic_memories(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {
            "semantic": [
                {"content": "Past strategy discussion", "metadata": {"agent_id": "ceo"}, "distance": 0.1}
            ],
            "graph": [],
        }
        result = await agent._build_memory_context("user1", "strategy")
        assert "Relevant Past Interactions" in result
        assert "Past strategy discussion" in result
        assert "ceo" in result

    @pytest.mark.asyncio
    async def test_includes_graph_memories(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {
            "semantic": [],
            "graph": [
                {"id": "d1", "content": "Decided to pivot", "agent_id": "ceo", "timestamp": 100.0}
            ],
        }
        result = await agent._build_memory_context("user1", "pivot")
        assert "Past Decisions & Patterns" in result
        assert "Decided to pivot" in result

    @pytest.mark.asyncio
    async def test_includes_both_when_available(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {
            "semantic": [
                {"content": "Revenue discussion", "metadata": {"agent_id": "cfo"}, "distance": 0.2}
            ],
            "graph": [
                {"id": "d1", "content": "Revenue target set", "agent_id": "ceo", "timestamp": 100.0}
            ],
        }
        result = await agent._build_memory_context("user1", "revenue")
        assert "Relevant Past Interactions" in result
        assert "Past Decisions & Patterns" in result

    @pytest.mark.asyncio
    async def test_handles_missing_agent_id_in_metadata(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {
            "semantic": [
                {"content": "Some memory", "metadata": {}, "distance": 0.3}
            ],
            "graph": [],
        }
        result = await agent._build_memory_context("user1", "test")
        assert "unknown" in result

    @pytest.mark.asyncio
    async def test_calls_memory_layer_read(self, agent, mock_memory_layer):
        mock_memory_layer.read.return_value = {"semantic": [], "graph": []}
        await agent._build_memory_context("user_abc", "my query")
        mock_memory_layer.read.assert_called_once_with("user_abc", "my query")
