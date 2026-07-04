"""Tests for core/config.py"""
import os
import pytest
from core.config import Settings, get_settings


class TestSettings:
    def test_settings_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")
        monkeypatch.setenv("JWT_SECRET", "my-jwt-secret")
        monkeypatch.setenv("CHROMADB_PATH", "/custom/chroma")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("APP_HOST", "0.0.0.0")
        monkeypatch.setenv("APP_PORT", "9000")
        monkeypatch.setenv("DEBUG", "false")

        s = Settings()
        assert s.anthropic_api_key == "sk-ant-test-123"
        assert s.jwt_secret == "my-jwt-secret"
        assert s.chromadb_path == "/custom/chroma"
        assert s.database_url == "sqlite:///test.db"
        assert s.app_host == "0.0.0.0"
        assert s.app_port == 9000
        assert s.debug is False

    def test_settings_defaults(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("JWT_SECRET", "secret")
        monkeypatch.delenv("CHROMADB_PATH", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("APP_HOST", raising=False)
        monkeypatch.delenv("APP_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("MEM0_API_KEY", raising=False)

        s = Settings()
        assert s.chromadb_path == "./data/chroma"
        assert s.database_url == "sqlite:///./data/cannae.db"
        assert s.app_host == "127.0.0.1"
        assert s.app_port == 8000
        assert s.debug is True
        assert s.mem0_api_key is None

    def test_settings_mem0_optional(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("JWT_SECRET", "secret")
        monkeypatch.setenv("MEM0_API_KEY", "mem0-key-123")

        s = Settings()
        assert s.mem0_api_key == "mem0-key-123"


class TestGetSettings:
    def test_get_settings_returns_settings_instance(self):
        s = get_settings()
        assert isinstance(s, Settings)

    def test_get_settings_caches_instance(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_get_settings_reset_creates_new(self):
        import core.config
        s1 = get_settings()
        core.config.settings = None
        s2 = get_settings()
        # After reset, should still get a valid Settings
        assert isinstance(s2, Settings)
