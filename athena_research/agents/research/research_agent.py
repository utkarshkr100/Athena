from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import asyncio
from ..base_agent import BaseAgent, AgentResponse, AgentMessage
from ...config import settings

class SearchResult(BaseModel):
    title: str
    content: str
    url: Optional[str] = None
    source_type: str  # "web", "azure_search", "document"
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = {}

class ResearchResult(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float

class ResearchAgent(BaseAgent):
    def __init__(self, search_tools: List[Any]):
        super().__init__(
            name="ResearchAgent",
            model=settings.research_model,
            temperature=settings.default_temperature
        )
        self.search_tools = search_tools

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            queries = input_data.get("queries", [])
            section_title = input_data.get("section_title", "")
            max_results_per_query = input_data.get("max_results", 10)

            research_results = await self._conduct_research(
                queries, section_title, max_results_per_query
            )

            return AgentResponse(
                success=True,
                data={
                    "section_title": section_title,
                    "research_results": [result.dict() for result in research_results]
                },
                sources=self._extract_sources(research_results)
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                data=None,
                error=str(e)
            )

    async def _conduct_research(
        self,
        queries: List[str],
        section_title: str,
        max_results: int
    ) -> List[ResearchResult]:
        research_results = []

        # Process queries in parallel
        tasks = [
            self._search_query(query, max_results)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log the error and continue
                print(f"Error searching query '{queries[i]}': {result}")
                continue

            research_results.append(result)

        return research_results

    async def _search_query(self, query: str, max_results: int) -> ResearchResult:
        """Search across all available search tools"""
        import time
        start_time = time.time()

        all_results = []

        # Search across all available tools
        for tool in self.search_tools:
            try:
                tool_results = await tool.search(query, max_results // len(self.search_tools))
                all_results.extend(tool_results)
            except Exception as e:
                print(f"Error with search tool {tool.__class__.__name__}: {e}")
                continue

        # Rank and deduplicate results
        ranked_results = await self._rank_and_deduplicate(all_results, query)

        search_time = time.time() - start_time

        return ResearchResult(
            query=query,
            results=ranked_results[:max_results],
            total_results=len(ranked_results),
            search_time=search_time
        )

    async def _rank_and_deduplicate(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Rank results by relevance and remove duplicates"""
        # Simple deduplication by URL and title
        seen_urls = set()
        seen_titles = set()
        unique_results = []

        for result in results:
            url_key = result.url or f"no_url_{hash(result.content[:100])}"
            title_key = result.title.lower().strip()

            if url_key not in seen_urls and title_key not in seen_titles:
                seen_urls.add(url_key)
                seen_titles.add(title_key)
                unique_results.append(result)

        # Simple relevance scoring based on query terms
        query_terms = query.lower().split()
        for result in unique_results:
            score = 0
            content_lower = (result.title + " " + result.content).lower()

            for term in query_terms:
                score += content_lower.count(term)

            result.relevance_score = score

        # Sort by relevance score
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return unique_results

    def _extract_sources(self, research_results: List[ResearchResult]) -> List[Dict[str, Any]]:
        """Extract source information for citations"""
        sources = []

        for research_result in research_results:
            for result in research_result.results:
                source = {
                    "title": result.title,
                    "url": result.url,
                    "source_type": result.source_type,
                    "query": research_result.query,
                    "relevance_score": result.relevance_score
                }

                if result.metadata:
                    source.update(result.metadata)

                sources.append(source)

        return sources

    async def validate_research_quality(self, research_results: List[ResearchResult]) -> Dict[str, Any]:
        """Assess the quality and completeness of research results"""
        total_results = sum(len(result.results) for result in research_results)
        avg_relevance = sum(
            result.relevance_score
            for research_result in research_results
            for result in research_result.results
        ) / max(total_results, 1)

        source_types = set()
        for research_result in research_results:
            for result in research_result.results:
                source_types.add(result.source_type)

        quality_assessment = {
            "total_results": total_results,
            "average_relevance": avg_relevance,
            "source_diversity": len(source_types),
            "source_types": list(source_types),
            "queries_processed": len(research_results),
            "recommendation": self._get_quality_recommendation(total_results, avg_relevance, len(source_types))
        }

        return quality_assessment

    def _get_quality_recommendation(self, total_results: int, avg_relevance: float, source_diversity: int) -> str:
        """Provide recommendations based on research quality"""
        if total_results < 5:
            return "Consider expanding search queries or adding more search sources"
        elif avg_relevance < 2.0:
            return "Results have low relevance - consider refining search queries"
        elif source_diversity < 2:
            return "Limited source diversity - consider adding more data sources"
        else:
            return "Research quality is good"