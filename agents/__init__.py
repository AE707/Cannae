"""Agents package for Cannae AI Command Center."""

from typing import Type

from core.constants import AgentId
from memory.memory_layer import MemoryLayer

from .base_agent import BaseAgent
from .ceo_agent import CEOAgent
from .coach_agent import CoachAgent
from .seo_agent import SEOAgent
from .cfo_agent import CFOAgent
from .council import Council

# Central registry — add new agents here only
AGENT_REGISTRY: dict[AgentId, Type[BaseAgent]] = {
    "ceo": CEOAgent,
    "coach": CoachAgent,
    "seo": SEOAgent,
    "cfo": CFOAgent,
}

AGENT_DESCRIPTIONS: dict[AgentId, str] = {
    "ceo": "Strategic advisor focused on high-leverage decisions",
    "coach": "Accountability partner focused on goal tracking and follow-through",
    "seo": "Search engine optimization and content strategy specialist",
    "cfo": "Financial analysis and strategic finance specialist",
}


def get_agent(agent_id: str, memory_layer: MemoryLayer, settings: object) -> BaseAgent:
    """Factory: instantiate an agent by its ID.

    Raises ValueError for unknown agent IDs.
    """
    cls = AGENT_REGISTRY.get(agent_id)  # type: ignore[arg-type]
    if cls is None:
        valid = ", ".join(sorted(AGENT_REGISTRY.keys()))
        raise ValueError(f"Unknown agent_id '{agent_id}'. Valid options: {valid}")
    return cls(memory_layer, settings)


__all__ = [
    "BaseAgent",
    "CEOAgent",
    "CoachAgent",
    "SEOAgent",
    "CFOAgent",
    "Council",
    "AGENT_REGISTRY",
    "AGENT_DESCRIPTIONS",
    "get_agent",
]