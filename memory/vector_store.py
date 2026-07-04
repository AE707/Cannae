import asyncio
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.errors import InvalidCollectionException
import uuid

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised when a vector store operation fails."""


class VectorStore:
    """ChromaDB vector store for semantic search."""

    def __init__(self, chromadb_path: str) -> None:
        try:
            self.client = chromadb.PersistentClient(path=chromadb_path)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to initialize ChromaDB at '{chromadb_path}': {exc}"
            ) from exc
        self.collections: Dict[str, chromadb.Collection] = {}

    def _get_collection(self, user_id: str) -> chromadb.Collection:
        """Get or create collection for user.

        Raises VectorStoreError on unexpected failures (permission errors,
        disk full, etc.) rather than silently swallowing them.
        """
        if user_id not in self.collections:
            collection_name = f"user_{user_id}"
            try:
                self.collections[user_id] = self.client.get_collection(
                    name=collection_name
                )
            except (InvalidCollectionException, ValueError):
                # Collection doesn't exist yet — create it
                try:
                    self.collections[user_id] = self.client.create_collection(
                        name=collection_name
                    )
                except Exception as exc:
                    raise VectorStoreError(
                        f"Failed to create collection '{collection_name}': {exc}"
                    ) from exc
            except Exception as exc:
                raise VectorStoreError(
                    f"Failed to access collection '{collection_name}': {exc}"
                ) from exc
        return self.collections[user_id]

    async def add(
        self, user_id: str, content: str, metadata: Dict[str, Any]
    ) -> str:
        """Add document to vector store.

        Raises VectorStoreError if the write fails.
        """
        doc_id = str(uuid.uuid4())

        loop = asyncio.get_event_loop()

        def _add() -> None:
            self._get_collection(user_id).add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )

        try:
            await loop.run_in_executor(None, _add)
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to add document for user '{user_id}': {exc}"
            ) from exc

        return doc_id

    async def query(
        self, user_id: str, query: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Query vector store for similar content.

        Returns an empty list and logs a warning if the query fails
        (e.g. empty collection), rather than crashing the caller.
        """
        loop = asyncio.get_event_loop()

        def _query() -> Any:
            return self._get_collection(user_id).query(
                query_texts=[query],
                n_results=n_results,
            )

        try:
            results = await loop.run_in_executor(None, _query)
        except Exception as exc:
            logger.warning(
                "Vector store query failed for user=%s query=%r: %s",
                user_id, query[:50], exc,
            )
            return []

        formatted: List[Dict[str, Any]] = []
        if results and "documents" in results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted