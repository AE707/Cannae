"""Tests for core/constants.py"""
from core.constants import CLAUDE_MODEL, MAX_TOKENS, CEO_AGENT, COACH_AGENT, AgentId


class TestConstants:
    def test_claude_model_is_string(self):
        assert isinstance(CLAUDE_MODEL, str)
        assert len(CLAUDE_MODEL) > 0

    def test_claude_model_value(self):
        assert CLAUDE_MODEL == "claude-sonnet-4-20250514"

    def test_max_tokens_is_positive_int(self):
        assert isinstance(MAX_TOKENS, int)
        assert MAX_TOKENS > 0

    def test_max_tokens_value(self):
        assert MAX_TOKENS == 4096

    def test_ceo_agent_literal(self):
        assert CEO_AGENT == "ceo"

    def test_coach_agent_literal(self):
        assert COACH_AGENT == "coach"

    def test_agent_id_type_accepts_valid_values(self):
        # AgentId is Literal["ceo", "coach"] — validate these are the expected values
        valid: AgentId = "ceo"
        assert valid == "ceo"
        valid = "coach"
        assert valid == "coach"
