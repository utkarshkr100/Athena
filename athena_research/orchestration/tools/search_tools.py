from typing import Any, Dict, List, Optional
import asyncio
from ag2 import Tool
from ...data_sources import AzureSearchTool, TavilySearchTool, BingSearchTool
from ...agents.research.research_agent import SearchResult

class AthenaSearchTools:
    """AG2 tools wrapper for Athena search capabilities"""

    def __init__(self, search_tools: Optional[List[Any]] = None):
        self.search_tools = search_tools or []
        self.tools = self._create_tools()

    def _create_tools(self) -> List[Tool]:
        """Create AG2 tools from search tools"""
        tools = []

        # Web search tool
        web_search_tool = Tool(
            name="web_search",
            description="Search the web for information on a given topic",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search: web, news, academic",
                        "enum": ["web", "news", "academic"],
                        "default": "web"
                    }
                },
                "required": ["query"]
            }
        )(self._web_search)

        tools.append(web_search_tool)

        # Azure search tool
        azure_search_tool = Tool(
            name="azure_search",
            description="Search internal documents using Azure AI Search",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )(self._azure_search)

        tools.append(azure_search_tool)

        # Multi-source search tool
        multi_search_tool = Tool(
            name="multi_source_search",
            description="Search across multiple sources (web, Azure, etc.) for comprehensive results",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sources to search: web, azure, news",
                        "default": ["web", "azure"]
                    },
                    "max_results_per_source": {
                        "type": "integer",
                        "description": "Maximum results per source",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )(self._multi_source_search)

        tools.append(multi_search_tool)

        return tools

    async def _web_search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "web"
    ) -> Dict[str, Any]:
        """Execute web search using available tools"""
        results = []

        for tool in self.search_tools:
            try:
                if isinstance(tool, TavilySearchTool):
                    if search_type == "news":
                        tool_results = await tool.search_news(query, max_results)
                    else:
                        tool_results = await tool.search(query, max_results)
                elif isinstance(tool, BingSearchTool):
                    if search_type == "news":
                        tool_results = await tool.search_news(query, max_results)
                    elif search_type == "academic":
                        tool_results = await tool.search_academic(query, max_results)
                    else:
                        tool_results = await tool.search(query, max_results)
                else:
                    continue

                results.extend(tool_results)
                break  # Use first available web search tool

            except Exception as e:
                print(f"Web search tool error: {e}")
                continue

        return {
            "status": "success" if results else "no_results",
            "results": [self._serialize_search_result(r) for r in results],
            "total_results": len(results),
            "query": query,
            "search_type": search_type
        }

    async def _azure_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Execute Azure search"""
        results = []

        for tool in self.search_tools:
            if isinstance(tool, AzureSearchTool):
                try:
                    results = await tool.search(query, max_results)
                    break
                except Exception as e:
                    print(f"Azure search error: {e}")
                    continue

        return {
            "status": "success" if results else "no_results",
            "results": [self._serialize_search_result(r) for r in results],
            "total_results": len(results),
            "query": query,
            "source": "azure_search"
        }

    async def _multi_source_search(
        self,
        query: str,
        sources: List[str] = ["web", "azure"],
        max_results_per_source: int = 5
    ) -> Dict[str, Any]:
        """Search across multiple sources"""
        all_results = []
        source_results = {}

        # Create search tasks for each source
        tasks = []
        if "web" in sources:
            tasks.append(("web", self._web_search(query, max_results_per_source)))
        if "azure" in sources:
            tasks.append(("azure", self._azure_search(query, max_results_per_source)))
        if "news" in sources:
            tasks.append(("news", self._web_search(query, max_results_per_source, "news")))

        # Execute searches in parallel
        for source_name, task in tasks:
            try:
                result = await task
                source_results[source_name] = result
                if result["status"] == "success":
                    all_results.extend(result["results"])
            except Exception as e:
                print(f"Error searching {source_name}: {e}")
                source_results[source_name] = {"status": "error", "error": str(e)}

        return {
            "status": "success" if all_results else "no_results",
            "results": all_results,
            "total_results": len(all_results),
            "source_breakdown": source_results,
            "query": query,
            "sources_searched": sources
        }

    def _serialize_search_result(self, result: SearchResult) -> Dict[str, Any]:
        """Convert SearchResult to serializable dict"""
        return {
            "title": result.title,
            "content": result.content,
            "url": result.url,
            "source_type": result.source_type,
            "relevance_score": result.relevance_score,
            "metadata": result.metadata
        }

    def get_tools(self) -> List[Tool]:
        """Get all AG2 tools"""
        return self.tools