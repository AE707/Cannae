import logging
import httpx
from typing import List, Dict, Any
from core.config import get_settings

logger = logging.getLogger(__name__)


class SearchServiceError(Exception):
    """Raised when a search operation fails."""


class SearchService:
    """Web search service using SearXNG or Tavily."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.tavily_api_key = getattr(self.settings, "tavily_api_key", None)
        self.searxng_url = getattr(self.settings, "searxng_url", "https://searx.be")
        self.use_tavily = bool(self.settings.tavily_api_key)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform web search and return results.

        Raises SearchServiceError if the search cannot be completed.
        """
        if self.tavily_api_key:
            return await self._search_tavily(query, max_results)
        return await self._search_searxng(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API.
        """Search using Tavily API."""
        api_key = self.settings.tavily_api_key
        if not api_key:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        Raises SearchServiceError on HTTP or connection failures.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "include_raw_content": False,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SearchServiceError(
                f"Tavily API returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            ) from exc
        except httpx.ConnectError as exc:
            raise SearchServiceError(
                f"Cannot connect to Tavily API: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise SearchServiceError(
                f"Tavily API request timed out: {exc}"
            ) from exc

        data = response.json()
        results: List[Dict[str, Any]] = []
        for result in data.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
            })
        return results
    async def _search_searxng(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using SearXNG instance."""
        searxng_url = self.settings.searxng_url

    async def _search_searxng(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using SearXNG instance.

        Raises SearchServiceError on HTTP or connection failures.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SearchServiceError(
                f"SearXNG returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            ) from exc
        except httpx.ConnectError as exc:
            raise SearchServiceError(
                f"Cannot connect to SearXNG at {self.searxng_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise SearchServiceError(
                f"SearXNG request timed out: {exc}"
            ) from exc

        data = response.json()
        raw_results = data.get("results", [])[:max_results]
        total = len(raw_results)

        results: List[Dict[str, Any]] = []
        for idx, result in enumerate(raw_results):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": 1.0 - (idx / total) if total > 0 else 0.5,
            })
        return results
            all_results = data.get("results", [])
            results = []
            for i, result in enumerate(all_results[:max_results]):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "score": 1.0 - (i / len(all_results)) if all_results else 0.5,
                    }
                )
            return results
