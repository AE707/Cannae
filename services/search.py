import httpx
from typing import List, Dict, Any
from core.config import get_settings


class SearchService:
    """Web search service using SearXNG or Tavily."""

    def __init__(self):
        self.settings = get_settings()
        self.use_tavily = bool(self.settings.tavily_api_key)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform web search and return results."""
        if self.use_tavily:
            return await self._search_tavily(query, max_results)
        else:
            return await self._search_searxng(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
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

            results = []
            for result in data.get("results", []):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                    }
                )
            return results

    async def _search_searxng(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using SearXNG instance."""
        searxng_url = self.settings.searxng_url

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()

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
