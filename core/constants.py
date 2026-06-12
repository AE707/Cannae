from typing import Literal

# Claude Model
CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
MAX_TOKENS: int = 4096

# Agent names
CEO_AGENT: Literal["ceo"] = "ceo"
COACH_AGENT: Literal["coach"] = "coach"

# Agent ID type
AgentId = Literal["ceo", "coach"]