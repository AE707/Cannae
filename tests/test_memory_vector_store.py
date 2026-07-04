"""Tests for memory/vector_store.py"""
import os
import shutil
import tempfile
import pytest
from memory.vector_store import VectorStore


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB."""
    d = tempfile.mkdtemp(prefix="cannae_test_chroma_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create a VectorStore instance with temporary storage."""
    return VectorStore(chromadb_path=temp_chroma_dir)


class TestVectorStoreInit:
    def test_creates_client(self, vector_store):
        assert vector_store.client is not None

    def test_empty_collections_on_init(self, vector_store):
        assert vector_store.collections == {}


class TestVectorStoreGetCollection:
    def test_get_collection_creates_new(self, vector_store):
        collection = vector_store._get_collection("user_test")
        assert collection is not None
        assert "user_test" in vector_store.collections

    def test_get_collection_caches(self, vector_store):
        c1 = vector_store._get_collection("user_abc")
        c2 = vector_store._get_collection("user_abc")
        assert c1 is c2

    def test_separate_collections_per_user(self, vector_store):
        c1 = vector_store._get_collection("user_a")
        c2 = vector_store._get_collection("user_b")
        assert c1 is not c2


class TestVectorStoreAdd:
    @pytest.mark.asyncio
    async def test_add_returns_id(self, vector_store):
        doc_id = await vector_store.add(
            user_id="user1",
            content="Test document about strategy",
            metadata={"agent_id": "ceo", "type": "interaction"},
        )
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    @pytest.mark.asyncio
    async def test_add_generates_unique_ids(self, vector_store):
        id1 = await vector_store.add("user1", "doc one", {"agent_id": "ceo"})
        id2 = await vector_store.add("user1", "doc two", {"agent_id": "coach"})
        assert id1 != id2


class TestVectorStoreQuery:
    @pytest.mark.asyncio
    async def test_query_empty_collection(self, vector_store):
        results = await vector_store.query("user_empty", "anything")
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_query_returns_added_docs(self, vector_store):
        await vector_store.add("user1", "Strategic planning for Q4", {"agent_id": "ceo"})
        await vector_store.add("user1", "Weekly accountability check", {"agent_id": "coach"})

        results = await vector_store.query("user1", "strategy planning", n_results=5)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_query_result_structure(self, vector_store):
        await vector_store.add("user1", "Revenue growth strategy", {"agent_id": "ceo"})
        results = await vector_store.query("user1", "revenue", n_results=1)

        assert len(results) == 1
        result = results[0]
        assert "content" in result
        assert "metadata" in result
        assert "distance" in result

    @pytest.mark.asyncio
    async def test_query_respects_n_results(self, vector_store):
        for i in range(5):
            await vector_store.add("user1", f"Document {i} about growth", {"agent_id": "ceo"})

        results = await vector_store.query("user1", "growth", n_results=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_query_isolated_per_user(self, vector_store):
        await vector_store.add("user_a", "User A's strategy doc", {"agent_id": "ceo"})
        await vector_store.add("user_b", "User B's strategy doc", {"agent_id": "ceo"})

        results_a = await vector_store.query("user_a", "strategy")
        results_b = await vector_store.query("user_b", "strategy")

        # Each user should only see their own documents
        assert len(results_a) == 1
        assert len(results_b) == 1
        assert "User A" in results_a[0]["content"]
        assert "User B" in results_b[0]["content"]
