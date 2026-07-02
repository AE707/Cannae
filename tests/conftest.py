"""Shared test fixtures for the Cannae test suite."""
import os
import sys
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required env vars before any imports that trigger Settings instantiation
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing")
os.environ.setdefault("CHROMADB_PATH", "/tmp/cannae_test_chroma")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/cannae_test.db")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset the global settings singleton between tests."""
    import core.config
    core.config.settings = None
    yield
    core.config.settings = None
