from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import json
from ..base_search import BaseSearchTool
from ...agents.research.research_agent import SearchResult
from ...config import settings

class BingSearchTool(BaseSearchTool):
    def __init__(self, api_key: str = None):
        super().__init__("BingSearch")

        self.api_key = api_key or settings.bing_search_api_key
        if not self.api_key:
            raise ValueError("Bing Search API key is required")

        self.search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.news_url = "https://api.bing.microsoft.com/v7.0/news/search"

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search the web using Bing Search API"""
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "count": max_results,
                "responseFilter": "webpages",
                "textDecorations": False,
                "textFormat": "Raw"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_bing_results(data)
                    else:
                        print(f"Bing Search API error: {response.status}")
                        return []

        except Exception as e:
            print(f"Bing search error: {e}")
            return []

    async def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search for news using Bing News Search API"""
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "count": max_results,
                "freshness": "Week",  # Recent news within a week
                "textFormat": "Raw"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.news_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_bing_news_results(data)
                    else:
                        print(f"Bing News API error: {response.status}")
                        return []

        except Exception as e:
            print(f"Bing news search error: {e}")
            return []

    async def search_academic(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search for academic content using site-specific search"""
        # Add academic site filters
        academic_query = f"{query} site:arxiv.org OR site:scholar.google.com OR site:researchgate.net OR site:pubmed.ncbi.nlm.nih.gov"

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {
            "q": academic_query,
            "count": max_results,
            "responseFilter": "webpages",
            "textFormat": "Raw"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._convert_bing_results(data)
                        # Mark as academic sources
                        for result in results:
                            result.source_type = "academic"
                            result.metadata["academic_source"] = True
                        return results
                    else:
                        return []

        except Exception as e:
            print(f"Bing academic search error: {e}")
            return []

    def _convert_bing_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Convert Bing Search API response to our SearchResult format"""
        search_results = []

        web_pages = data.get("webPages", {})
        results = web_pages.get("value", [])

        for result in results:
            title = result.get("name", "Untitled")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            date_published = result.get("datePublished", "")

            metadata = {
                "date_published": date_published,
                "display_url": result.get("displayUrl", ""),
                "domain": self._extract_domain(url),
                "bing_id": result.get("id", "")
            }

            search_result = self._create_search_result(
                title=title,
                content=snippet,
                url=url,
                source_type="web",
                metadata=metadata
            )

            search_results.append(search_result)

        return search_results

    def _convert_bing_news_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Convert Bing News API response to our SearchResult format"""
        search_results = []

        news_results = data.get("value", [])

        for result in news_results:
            title = result.get("name", "Untitled")
            description = result.get("description", "")
            url = result.get("url", "")
            date_published = result.get("datePublished", "")
            provider = result.get("provider", [{}])[0].get("name", "Unknown") if result.get("provider") else "Unknown"

            metadata = {
                "date_published": date_published,
                "provider": provider,
                "category": result.get("category", ""),
                "domain": self._extract_domain(url),
                "news_source": True
            }

            # Try to get more content from the article
            content = description
            if "body" in result:
                content = result["body"]

            search_result = self._create_search_result(
                title=title,
                content=content,
                url=url,
                source_type="news",
                metadata=metadata
            )

            search_results.append(search_result)

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
        """Check if Bing Search API is accessible"""
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": "test", "count": 1}

            async with aiohttp.ClientSession() as session:
                async with session.get(self.search_url, headers=headers, params=params) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Bing Search availability check failed: {e}")
            return False

    async def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for a query"""
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            suggestion_url = "https://api.bing.microsoft.com/v7.0/suggestions"
            params = {"q": query}

            async with aiohttp.ClientSession() as session:
                async with session.get(suggestion_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        suggestions = []
                        suggestion_groups = data.get("suggestionGroups", [])
                        for group in suggestion_groups:
                            for suggestion in group.get("searchSuggestions", []):
                                suggestions.append(suggestion.get("query", ""))
                        return suggestions[:10]  # Limit to 10 suggestions
                    else:
                        return []

        except Exception as e:
            print(f"Bing suggestions error: {e}")
            return []