"""Tests for memory/memory_layer.py"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memory.memory_layer import MemoryLayer


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.chromadb_path = "/tmp/test_chroma"
    settings.mem0_api_key = None
    return settings


@pytest.fixture
def memory_layer(mock_settings):
    with patch("memory.memory_layer.VectorStore") as MockVS, \
         patch("memory.memory_layer.GraphMemory") as MockGM:
        MockVS.return_value = MagicMock()
        MockGM.return_value = MagicMock()
        ml = MemoryLayer(mock_settings)
        # Replace with async mocks
        ml.vector_store.add = AsyncMock(return_value="vec-123")
        ml.vector_store.query = AsyncMock(return_value=[
            {"content": "past decision", "metadata": {"agent_id": "ceo"}, "distance": 0.1}
        ])
        ml.graph_memory.add_decision = AsyncMock(return_value="graph-456")
        ml.graph_memory.get_context = AsyncMock(return_value=[
            {"id": "ctx-1", "content": "relevant context", "agent_id": "coach", "timestamp": 1000.0}
        ])
        return ml


class TestMemoryLayerInit:
    def test_creates_vector_store(self, mock_settings):
        with patch("memory.memory_layer.VectorStore") as MockVS, \
             patch("memory.memory_layer.GraphMemory"):
            ml = MemoryLayer(mock_settings)
            MockVS.assert_called_once_with(mock_settings.chromadb_path)

    def test_creates_graph_memory(self, mock_settings):
        with patch("memory.memory_layer.VectorStore"), \
             patch("memory.memory_layer.GraphMemory") as MockGM:
            ml = MemoryLayer(mock_settings)
            MockGM.assert_called_once_with(mock_settings.mem0_api_key)


class TestMemoryLayerWrite:
    @pytest.mark.asyncio
    async def test_write_calls_vector_store(self, memory_layer):
        await memory_layer.write(
            user_id="user1", content="test content", agent_id="ceo", metadata={"key": "val"}
        )
        memory_layer.vector_store.add.assert_called_once()
        call_args = memory_layer.vector_store.add.call_args
        assert call_args[0][0] == "user1"
        assert call_args[0][1] == "test content"

    @pytest.mark.asyncio
    async def test_write_calls_graph_memory(self, memory_layer):
        await memory_layer.write(
            user_id="user1", content="test content", agent_id="ceo", metadata={}
        )
        memory_layer.graph_memory.add_decision.assert_called_once_with(
            "user1", "test content", "ceo"
        )

    @pytest.mark.asyncio
    async def test_write_passes_metadata_to_vector(self, memory_layer):
        await memory_layer.write(
            user_id="user1", content="data", agent_id="coach", metadata={"custom": "field"}
        )
        call_args = memory_layer.vector_store.add.call_args
        metadata = call_args[0][2]
        assert metadata["agent_id"] == "coach"
        assert metadata["type"] == "interaction"
        assert metadata["custom"] == "field"

    @pytest.mark.asyncio
    async def test_write_runs_both_concurrently(self, memory_layer):
        # Both calls should complete without blocking each other
        await memory_layer.write("user1", "content", "ceo", {})
        assert memory_layer.vector_store.add.call_count == 1
        assert memory_layer.graph_memory.add_decision.call_count == 1


class TestMemoryLayerRead:
    @pytest.mark.asyncio
    async def test_read_returns_dict_with_semantic_and_graph(self, memory_layer):
        result = await memory_layer.read(user_id="user1", query="strategy")
        assert "semantic" in result
        assert "graph" in result

    @pytest.mark.asyncio
    async def test_read_calls_vector_store_query(self, memory_layer):
        await memory_layer.read(user_id="user1", query="my query")
        memory_layer.vector_store.query.assert_called_once_with("user1", "my query")

    @pytest.mark.asyncio
    async def test_read_calls_graph_memory_get_context(self, memory_layer):
        await memory_layer.read(user_id="user1", query="my query")
        memory_layer.graph_memory.get_context.assert_called_once_with("user1", "my query")

    @pytest.mark.asyncio
    async def test_read_merges_results(self, memory_layer):
        result = await memory_layer.read("user1", "test")
        assert len(result["semantic"]) == 1
        assert result["semantic"][0]["content"] == "past decision"
        assert len(result["graph"]) == 1
        assert result["graph"][0]["content"] == "relevant context"
