from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..agents.research.research_agent import SearchResult

class BaseSearchTool(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform a search and return structured results"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the search tool is properly configured and available"""
        pass

    def _create_search_result(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        source_type: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """Helper method to create consistent SearchResult objects"""
        return SearchResult(
            title=title,
            content=content,
            url=url,
            source_type=source_type,
            relevance_score=0.0,  # Will be calculated later
            metadata=metadata or {}
        )