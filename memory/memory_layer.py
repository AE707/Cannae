from typing import Dict, Any, List
import asyncio

from core.config import get_settings
from memory.vector_store import VectorStore
from memory.graph_memory import GraphMemory


class MemoryLayer:
    """Unified memory interface - agents should only use this."""

    def __init__(self, settings):
        self.vector_store = VectorStore(settings.chromadb_path)
        self.graph_memory = GraphMemory(settings.mem0_api_key)

    async def write(
        self, user_id: str, content: str, agent_id: str, metadata: Dict[str, Any]
    ) -> None:
        """Write to both vector and graph memory simultaneously."""
        # Create tasks for both writes
        vector_task = self.vector_store.add(user_id, content, {
            **metadata,
            "agent_id": agent_id,
            "type": "interaction",
        })

        graph_task = self.graph_memory.add_decision(user_id, content, agent_id)

        # Run both concurrently
        await asyncio.gather(vector_task, graph_task)

    async def read(self, user_id: str, query: str) -> Dict[str, Any]:
        """Read from both memory stores and return merged results."""
        # Create tasks for both reads
        vector_task = self.vector_store.query(user_id, query)
        graph_task = self.graph_memory.get_context(user_id, query)

        # Run both concurrently
        semantic_results, graph_results = await asyncio.gather(
            vector_task, graph_task
        )

        return {
            "semantic": semantic_results,
            "graph": graph_results,
        }