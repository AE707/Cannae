import asyncio
from typing import List, Dict, Any, Optional
import json


class GraphMemory:
    """Mem0 graph memory for storing decisions and relationships."""

    def __init__(self, mem0_api_key: Optional[str] = None):
        self.mem0_api_key = mem0_api_key
        self._stub_mode = mem0_api_key is None

    async def add_decision(
        self, user_id: str, content: str, agent_id: str
    ) -> str:
        """Add a decision to graph memory."""
        if self._stub_mode:
            # Stub mode - just return a mock ID
            return f"stub_decision_{user_id}_{agent_id}"

        # TODO: Implement actual Mem0 integration
        # For now, we'll stub it
        decision_id = f"decision_{user_id}_{agent_id}"

        # Store in memory (in production, this would go to Mem0)
        if not hasattr(self, "_decisions"):
            self._decisions = {}
        if user_id not in self._decisions:
            self._decisions[user_id] = []

        self._decisions[user_id].append({
            "id": decision_id,
            "content": content,
            "agent_id": agent_id,
            "timestamp": asyncio.get_event_loop().time(),
        })

        return decision_id

    async def get_context(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Get context from graph memory relevant to query."""
        if self._stub_mode:
            # Return some mock context
            return [
                {
                    "id": "stub_context_1",
                    "content": "Past decision: Chosen to focus on organic growth",
                    "agent_id": "ceo",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                {
                    "id": "stub_context_2",
                    "content": "Accountability plan: Weekly revenue reviews",
                    "agent_id": "coach",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            ]

        # TODO: Implement actual Mem0 integration
        # For now, return empty list
        return []