from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from tavily import TavilyClient
from ..base_search import BaseSearchTool
from ...agents.research.research_agent import SearchResult
from ...config import settings

class TavilySearchTool(BaseSearchTool):
    def __init__(self, api_key: str = None):
        super().__init__("TavilySearch")

        self.api_key = api_key or settings.tavily_api_key
        if not self.api_key:
            raise ValueError("Tavily API key is required")

        self.client = TavilyClient(api_key=self.api_key)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search the web using Tavily"""
        try:
            # Tavily search parameters
            search_params = {
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": True,
                "include_domains": None,
                "exclude_domains": None
            }

            # Perform the search (Tavily client handles async internally)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(**search_params)
            )

            return self._convert_tavily_results(response)

        except Exception as e:
            print(f"Tavily search error: {e}")
            return []

    async def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search for recent news using Tavily"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_answer=True,
                    days=7  # Recent news within 7 days
                )
            )

            return self._convert_tavily_results(response, source_type="news")

        except Exception as e:
            print(f"Tavily news search error: {e}")
            return []

    async def get_search_context(self, query: str, max_results: int = 5) -> str:
        """Get a contextual answer for a query using Tavily"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_search_context(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results
                )
            )

            return response.get("context", "")

        except Exception as e:
            print(f"Tavily context search error: {e}")
            return ""

    def _convert_tavily_results(
        self,
        response: Dict[str, Any],
        source_type: str = "web"
    ) -> List[SearchResult]:
        """Convert Tavily API response to our SearchResult format"""
        search_results = []

        # Process search results
        results = response.get("results", [])
        for result in results:
            title = result.get("title", "Untitled")
            content = result.get("content", "")
            url = result.get("url", "")

            # Use raw_content if available (more detailed)
            if "raw_content" in result and result["raw_content"]:
                content = result["raw_content"]

            metadata = {
                "published_date": result.get("published_date", ""),
                "score": result.get("score", 0.0),
                "tavily_id": result.get("id", ""),
                "domain": self._extract_domain(url)
            }

            search_result = self._create_search_result(
                title=title,
                content=content,
                url=url,
                source_type=source_type,
                metadata=metadata
            )

            search_results.append(search_result)

        # If Tavily provided a direct answer, include it as the first result
        if "answer" in response and response["answer"]:
            answer_result = self._create_search_result(
                title=f"Direct Answer: {response.get('query', 'Query')}",
                content=response["answer"],
                url=None,
                source_type="tavily_answer",
                metadata={"type": "direct_answer", "confidence": "high"}
            )
            search_results.insert(0, answer_result)

        return search_results

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""

    async def is_available(self) -> bool:
        """Check if Tavily API is accessible"""
        try:
            # Test with a simple query
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(query="test", max_results=1)
            )
            return "results" in response
        except Exception as e:
            print(f"Tavily availability check failed: {e}")
            return False

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics if available"""
        # Tavily doesn't provide usage stats in the basic API
        return {
            "tool": "tavily",
            "status": "active" if await self.is_available() else "inactive"
        }