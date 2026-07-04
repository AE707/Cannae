from typing import Literal

# Claude Model
CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
MAX_TOKENS: int = 4096

# Agent ID type — single source of truth for all agent identifiers
AgentId = Literal["ceo", "coach", "seo", "cfo"]

# Handoff marker format used in agent responses
HANDOFF_PREFIX = "[HANDOFF→"
HANDOFF_SUFFIX = "]"

# Map from handoff marker target to AgentId
HANDOFF_TARGETS: dict[str, "AgentId"] = {
    "CEO": "ceo",
    "COACH": "coach",
    "SEO": "seo",
    "CFO": "cfo",
}