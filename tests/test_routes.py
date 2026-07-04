"""Tests for routes/ — API endpoint tests using FastAPI TestClient."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create the FastAPI app with mocked dependencies."""
    with patch("core.config.get_settings") as mock_settings, \
         patch("core.config.Settings") as MockSettingsClass:
        settings = MagicMock()
        settings.debug = True
        settings.anthropic_api_key = "test-key"
        settings.jwt_secret = "test-secret"
        settings.chromadb_path = "/tmp/test_chroma"
        settings.database_url = "sqlite:///test.db"
        settings.mem0_api_key = None
        settings.app_host = "127.0.0.1"
        settings.app_port = 8000
        mock_settings.return_value = settings
        MockSettingsClass.return_value = settings

        import core.config
        core.config.settings = settings

        from app import create_app
        application = create_app()
        yield application


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRootEndpoints:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Cannae" in data["message"]

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestChatAgentsEndpoint:
    def test_list_agents(self, client):
        response = client.get("/chat/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "ceo" in data["agents"]
        assert "coach" in data["agents"]
        assert "descriptions" in data


class TestMemoryRoutes:
    @patch("routes.memory.MemoryLayer")
    @patch("routes.memory.get_settings")
    def test_search_memory(self, mock_settings, MockML, client):
        mock_settings.return_value = MagicMock()
        mock_ml = MagicMock()
        mock_ml.read = AsyncMock(return_value={"semantic": [], "graph": []})
        MockML.return_value = mock_ml

        response = client.post("/memory/search", json={
            "user_id": "user1",
            "query": "test query",
            "n_results": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @patch("routes.memory.MemoryLayer")
    @patch("routes.memory.get_settings")
    def test_get_memory_stats(self, mock_settings, MockML, client):
        mock_settings.return_value = MagicMock()
        mock_ml = MagicMock()
        mock_ml.read = AsyncMock(return_value={"semantic": [{"x": 1}], "graph": [{"y": 2}]})
        MockML.return_value = mock_ml

        response = client.get("/memory/stats/user1")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user1"
        assert "total_entries" in data

    def test_clear_memory(self, client):
        response = client.delete("/memory/user1")
        assert response.status_code == 200
        data = response.json()
        assert "user1" in data["user_id"]


class TestCouncilRoutes:
    def test_get_council_memory(self, client):
        with patch("routes.council.MemoryLayer") as MockML, \
             patch("routes.council.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_ml = MagicMock()
            mock_ml.read = AsyncMock(return_value={
                "semantic": [{"content": "past item", "metadata": {}}],
                "graph": [],
            })
            MockML.return_value = mock_ml

            response = client.get("/council/memory/user1?query=test")
            assert response.status_code == 200
            data = response.json()
            assert "semantic" in data
            assert "graph" in data

    def test_clear_council_memory(self, client):
        response = client.delete("/council/memory/user1")
        assert response.status_code == 200
