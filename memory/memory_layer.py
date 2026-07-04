from typing import Dict, Any, List, Optional
import asyncio
import logging

from core.config import get_settings
from memory.vector_store import VectorStore
from memory.graph_memory import GraphMemory

logger = logging.getLogger(__name__)


class MemoryLayer:
    """Unified memory interface - agents should only use this."""

    def __init__(self, settings: Any) -> None:
        self.vector_store = VectorStore(settings.chromadb_path)
        self.graph_memory = GraphMemory(settings.mem0_api_key)

    async def write(
        self, user_id: str, content: str, agent_id: str, metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Write to both vector and graph memory simultaneously.

        Partial failures are logged but do not crash the caller — if one
        store fails, the other write still completes.

        Returns:
            The vector store document ID on success, or None if vector write failed.
        """
        vector_task = self.vector_store.add(user_id, content, {
            **metadata,
            "agent_id": agent_id,
            "type": "interaction",
        })
        graph_task = self.graph_memory.add_decision(user_id, content, agent_id)

        results = await asyncio.gather(vector_task, graph_task, return_exceptions=True)

        doc_id: Optional[str] = None
        if isinstance(results[0], BaseException):
            logger.error(
                "Vector store write failed for user=%s agent=%s: %s",
                user_id, agent_id, results[0],
            )
        else:
            doc_id = results[0]

        if isinstance(results[1], BaseException):
            logger.error(
                "Graph memory write failed for user=%s agent=%s: %s",
                user_id, agent_id, results[1],
            )

        return doc_id

    async def read(self, user_id: str, query: str) -> Dict[str, Any]:
        """Read from both memory stores and return merged results.

        Partial failures are logged and the failing store returns an empty
        list rather than crashing the entire read operation.
        """
        vector_task = self.vector_store.query(user_id, query)
        graph_task = self.graph_memory.get_context(user_id, query)

        results = await asyncio.gather(vector_task, graph_task, return_exceptions=True)

        semantic_results: List[Dict[str, Any]] = []
        graph_results: List[Dict[str, Any]] = []

        if isinstance(results[0], BaseException):
            logger.error(
                "Vector store read failed for user=%s: %s", user_id, results[0]
            )
        else:
            semantic_results = results[0]

        if isinstance(results[1], BaseException):
            logger.error(
                "Graph memory read failed for user=%s: %s", user_id, results[1]
            )
        else:
            graph_results = results[1]

        return {
            "semantic": semantic_results,
            "graph": graph_results,
        }