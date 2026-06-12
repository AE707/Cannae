"""
Test script to validate CannaeC project structure without requiring API keys.
This tests imports and basic instantiation.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from core.config import get_settings
        print("[OK] core.config imported")
    except Exception as e:
        print(f"[FAIL] core.config import failed: {e}")
        return False

    try:
        from core.constants import CLAUDE_MODEL, MAX_TOKENS, CEO_AGENT, COACH_AGENT
        print("[OK] core.constants imported")
    except Exception as e:
        print(f"[FAIL] core.constants import failed: {e}")
        return False

    try:
        from core.database import get_db
        print("[OK] core.database imported")
    except Exception as e:
        print(f"[FAIL] core.database import failed: {e}")
        return False

    try:
        from memory.vector_store import VectorStore
        print("[OK] memory.vector_store imported")
    except Exception as e:
        print(f"[FAIL] memory.vector_store import failed: {e}")
        return False

    try:
        from memory.graph_memory import GraphMemory
        print("[OK] memory.graph_memory imported")
    except Exception as e:
        print(f"[FAIL] memory.graph_memory import failed: {e}")
        return False

    try:
        from memory.memory_layer import MemoryLayer
        print("[OK] memory.memory_layer imported")
    except Exception as e:
        print(f"[FAIL] memory.memory_layer import failed: {e}")
        return False

    try:
        from agents.base_agent import BaseAgent
        print("[OK] agents.base_agent imported")
    except Exception as e:
        print(f"[FAIL] agents.base_agent import failed: {e}")
        return False

    try:
        from agents.ceo_agent import CEOAgent
        print("[OK] agents.ceo_agent imported")
    except Exception as e:
        print(f"[FAIL] agents.ceo_agent import failed: {e}")
        return False

    try:
        from agents.coach_agent import CoachAgent
        print("[OK] agents.coach_agent imported")
    except Exception as e:
        print(f"[FAIL] agents.coach_agent import failed: {e}")
        return False

    try:
        from agents.council import Council
        print("[OK] agents.council imported")
    except Exception as e:
        print(f"[FAIL] agents.council import failed: {e}")
        return False

    try:
        from services.llm import LLMService
        print("[OK] services.llm imported")
    except Exception as e:
        print(f"[FAIL] services.llm import failed: {e}")
        return False

    try:
        from services.search import SearchService
        print("[OK] services.search imported")
    except Exception as e:
        print(f"[FAIL] services.search import failed: {e}")
        return False

    try:
        from routes.council import router as council_router
        print("[OK] routes.council imported")
    except Exception as e:
        print(f"[FAIL] routes.council import failed: {e}")
        return False

    try:
        from routes.chat import router as chat_router
        print("[OK] routes.chat imported")
    except Exception as e:
        print(f"[FAIL] routes.chat import failed: {e}")
        return False

    try:
        from routes.memory import router as memory_router
        print("[OK] routes.memory imported")
    except Exception as e:
        print(f"[FAIL] routes.memory import failed: {e}")
        return False

    try:
        from app import create_app
        print("[OK] app imported")
    except Exception as e:
        print(f"[FAIL] app import failed: {e}")
        return False

    return True

def test_instantiation():
    """Test that objects can be instantiated (without API calls)."""
    print("\nTesting instantiation...")

    try:
        from core.config import get_settings
        settings = get_settings()
        print("[OK] Settings instantiated")
    except Exception as e:
        print(f"[INFO] Settings instantiation failed (expected without .env): {e}")
        # This is expected to fail without .env file, but we'll continue
        pass

    try:
        from core.constants import CLAUDE_MODEL, MAX_TOKENS
        assert isinstance(CLAUDE_MODEL, str)
        assert isinstance(MAX_TOKENS, int)
        print("[OK] Constants validated")
    except Exception as e:
        print(f"[FAIL] Constants validation failed: {e}")
        return False

    try:
        from memory.vector_store import VectorStore
        # Just test that the class exists and can be referenced
        assert VectorStore is not None
        print("[OK] VectorStore class validated")
    except Exception as e:
        print(f"[FAIL] VectorStore validation failed: {e}")
        return False

    try:
        from memory.graph_memory import GraphMemory
        assert GraphMemory is not None
        print("[OK] GraphMemory class validated")
    except Exception as e:
        print(f"[FAIL] GraphMemory validation failed: {e}")
        return False

    try:
        from agents.base_agent import BaseAgent
        assert BaseAgent is not None
        print("[OK] BaseAgent class validated")
    except Exception as e:
        print(f"[FAIL] BaseAgent validation failed: {e}")
        return False

    return True

async def test_async_structure():
    """Test async structure without making actual API calls."""
    print("\nTesting async structure...")

    # We won't actually run the async methods since they require API keys
    # but we can verify the method signatures exist

    try:
        from agents.ceo_agent import CEOAgent
        from agents.coach_agent import CoachAgent
        from agents.council import Council

        # Check that methods exist
        assert hasattr(CEOAgent, 'invoke')
        assert hasattr(CoachAgent, 'invoke')
        assert hasattr(Council, 'invoke')
        print("[OK] Agent method signatures validated")
    except Exception as e:
        print(f"[FAIL] Agent method validation failed: {e}")
        return False

    return True

def main():
    """Run all tests."""
    print("=== CannaeC Structure Validation ===\n")

    success = True
    success &= test_imports()
    success &= test_instantiation()

    # Run async test
    try:
        success &= asyncio.run(test_async_structure())
    except Exception as e:
        print(f"[FAIL] Async structure test failed: {e}")
        success = False

    print(f"\n=== Results ===")
    if success:
        print("[OK] All structure tests passed!")
        print("The CannaeC project structure is valid.")
        return 0
    else:
        print("[FAIL] Some structure tests failed!")
        print("Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())