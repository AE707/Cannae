import asyncio
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid


class VectorStore:
    """ChromaDB vector store for semantic search."""

    def __init__(self, chromadb_path: str):
        self.client = chromadb.PersistentClient(path=chromadb_path)
        self.collections: Dict[str, chromadb.Collection] = {}

    def _get_collection(self, user_id: str) -> chromadb.Collection:
        """Get or create collection for user."""
        if user_id not in self.collections:
            collection_name = f"user_{user_id}"
            try:
                self.collections[user_id] = self.client.get_collection(
                    name=collection_name
                )
            except Exception:
                # Collection doesn't exist, create it
                self.collections[user_id] = self.client.create_collection(
                    name=collection_name
                )
        return self.collections[user_id]

    async def add(
        self, user_id: str, content: str, metadata: Dict[str, Any]
    ) -> str:
        """Add document to vector store."""
        doc_id = str(uuid.uuid4())

        # Run ChromaDB operation in executor to avoid blocking
        loop = asyncio.get_event_loop()
        def _add():
            return self._get_collection(user_id).add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )
        await loop.run_in_executor(None, _add)

        return doc_id

    async def query(
        self, user_id: str, query: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Query vector store for similar content."""
        loop = asyncio.get_event_loop()
        def _query():
            return self._get_collection(user_id).query(
                query_texts=[query],
                n_results=n_results,
            )
        results = await loop.run_in_executor(None, _query)

        # Format results
        formatted = []
        if results and "documents" in results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted