"""Tests for services/search.py"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.search import SearchService


class TestSearchServiceInit:
    def test_uses_tavily_when_env_set(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()
            assert service.use_tavily is True

    def test_uses_searxng_when_no_tavily(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()
            assert service.use_tavily is False


class TestSearchServiceTavily:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()
            service.use_tavily = True  # Force tavily path
            results = await service._search_tavily("test query", 5)
            assert results == []

    @pytest.mark.asyncio
    async def test_formats_tavily_results(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://example.com",
                        "content": "Some content",
                        "score": 0.9,
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                MockClient.return_value = mock_client

                results = await service._search_tavily("test", 5)
                assert len(results) == 1
                assert results[0]["title"] == "Test Result"
                assert results[0]["url"] == "https://example.com"
                assert results[0]["content"] == "Some content"
                assert results[0]["score"] == 0.9


class TestSearchServiceSearch:
    @pytest.mark.asyncio
    async def test_delegates_to_tavily(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-key")
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()
            service._search_tavily = AsyncMock(return_value=[{"title": "result"}])
            service._search_searxng = AsyncMock(return_value=[])

            results = await service.search("query", max_results=3)
            service._search_tavily.assert_called_once_with("query", 3)
            service._search_searxng.assert_not_called()

    @pytest.mark.asyncio
    async def test_delegates_to_searxng(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with patch("services.search.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            service = SearchService()
            service._search_tavily = AsyncMock(return_value=[])
            service._search_searxng = AsyncMock(return_value=[{"title": "searx result"}])

            results = await service.search("query", max_results=5)
            service._search_searxng.assert_called_once_with("query", 5)
            service._search_tavily.assert_not_called()
