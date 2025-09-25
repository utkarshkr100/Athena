"""
Athena Multi-Agent Deep Research System

A comprehensive research system that uses multiple AI agents to conduct thorough
research, synthesize information from various sources, and generate well-structured
reports with proper citations.

Key Features:
- Multi-agent architecture using AG2 (AutoGen successor)
- Integration with Azure AI Search, Tavily, and Bing Search
- Vector memory with ChromaDB and Redis caching
- Multiple citation styles (APA, MLA, Chicago, IEEE, Harvard)
- Export to various formats (Markdown, HTML, JSON, LaTeX, Word)
- Comprehensive source tracking and bibliography generation

Example Usage:
    from athena_research import AthenaResearchSystem

    # Initialize the system
    system = AthenaResearchSystem()

    # Conduct research
    result = await system.research("Artificial Intelligence in Healthcare")

    # Export report
    markdown_report = system.export_report(result, format="markdown")
"""

from .agents import (
    PlanningAgent, ResearchAgent, SectionWriterAgent, FinalWriterAgent,
    ResearchPlan, SectionContent, Citation
)
from .data_sources import (
    AzureSearchTool, TavilySearchTool, BingSearchTool
)
from .memory import (
    MemoryManager, ChromaMemoryStore, RedisCacheStore,
    MemoryItem, MemoryQuery
)
from .orchestration import (
    AthenaResearchWorkflow, AthenaSearchTools, AthenaMemoryTools
)
from .utils import (
    CitationManager, CitationStyle, OutputFormatter
)
from .config import settings

__version__ = "1.0.0"
__author__ = "Athena Research System"
__description__ = "Multi-Agent Deep Research System with AG2"

__all__ = [
    # Core system
    "AthenaResearchSystem",

    # Agents
    "PlanningAgent",
    "ResearchAgent",
    "SectionWriterAgent",
    "FinalWriterAgent",
    "ResearchPlan",
    "SectionContent",
    "Citation",

    # Data sources
    "AzureSearchTool",
    "TavilySearchTool",
    "BingSearchTool",

    # Memory
    "MemoryManager",
    "ChromaMemoryStore",
    "RedisCacheStore",
    "MemoryItem",
    "MemoryQuery",

    # Orchestration
    "AthenaResearchWorkflow",
    "AthenaSearchTools",
    "AthenaMemoryTools",

    # Utilities
    "CitationManager",
    "CitationStyle",
    "OutputFormatter",

    # Configuration
    "settings"
]

class AthenaResearchSystem:
    """Main interface for the Athena Research System"""

    def __init__(
        self,
        azure_search_config: dict = None,
        tavily_api_key: str = None,
        bing_api_key: str = None,
        citation_style: CitationStyle = CitationStyle.APA
    ):
        """
        Initialize the Athena Research System

        Args:
            azure_search_config: Configuration for Azure AI Search
            tavily_api_key: API key for Tavily search
            bing_api_key: API key for Bing search
            citation_style: Citation style for reports
        """
        self.search_tools = []
        self.memory_manager = None
        self.workflow = None
        self.output_formatter = OutputFormatter(citation_style)

        # Initialize search tools
        self._initialize_search_tools(azure_search_config, tavily_api_key, bing_api_key)

        # Initialize memory management
        self._initialize_memory()

        # Initialize workflow
        self._initialize_workflow()

    def _initialize_search_tools(self, azure_config, tavily_key, bing_key):
        """Initialize available search tools"""
        try:
            if azure_config or settings.azure_search_api_key:
                self.search_tools.append(AzureSearchTool())
        except Exception as e:
            print(f"Azure Search not available: {e}")

        try:
            if tavily_key or settings.tavily_api_key:
                self.search_tools.append(TavilySearchTool(tavily_key))
        except Exception as e:
            print(f"Tavily Search not available: {e}")

        try:
            if bing_key or settings.bing_search_api_key:
                self.search_tools.append(BingSearchTool(bing_key))
        except Exception as e:
            print(f"Bing Search not available: {e}")

    def _initialize_memory(self):
        """Initialize memory management"""
        try:
            self.memory_manager = MemoryManager()
        except Exception as e:
            print(f"Memory initialization warning: {e}")
            self.memory_manager = None

    def _initialize_workflow(self):
        """Initialize the research workflow"""
        if self.search_tools:
            self.workflow = AthenaResearchWorkflow(
                self.search_tools,
                self.memory_manager
            )

    async def research(
        self,
        topic: str,
        report_style: str = "comprehensive",
        user_requirements: str = ""
    ) -> dict:
        """
        Conduct comprehensive research on a topic

        Args:
            topic: The research topic
            report_style: Style of report ("comprehensive", "brief", "detailed")
            user_requirements: Additional user requirements

        Returns:
            Dictionary containing the research results and report
        """
        if not self.workflow:
            raise ValueError("No search tools available. Please configure at least one search service.")

        return await self.workflow.execute_research(
            topic,
            report_style,
            user_requirements
        )

    def export_report(
        self,
        research_result: dict,
        format: str = "markdown",
        include_metadata: bool = True
    ) -> str:
        """
        Export research report in specified format

        Args:
            research_result: Result from research() method
            format: Output format ("markdown", "html", "json", "latex", "word")
            include_metadata: Whether to include metadata

        Returns:
            Formatted report as string
        """
        if not research_result.get("success"):
            raise ValueError("Cannot export failed research result")

        report_data = research_result.get("report", {})

        if format == "markdown":
            return self.output_formatter.format_as_markdown(report_data, include_metadata)
        elif format == "html":
            return self.output_formatter.format_as_html(report_data)
        elif format == "json":
            return self.output_formatter.format_as_json(report_data)
        elif format == "latex":
            return self.output_formatter.format_as_latex(report_data)
        elif format == "word":
            return self.output_formatter.format_as_word_xml(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_multiple_formats(
        self,
        research_result: dict,
        formats: list = ["markdown", "html", "json"]
    ) -> dict:
        """
        Export research report in multiple formats

        Args:
            research_result: Result from research() method
            formats: List of formats to export

        Returns:
            Dictionary mapping format names to formatted content
        """
        if not research_result.get("success"):
            raise ValueError("Cannot export failed research result")

        report_data = research_result.get("report", {})
        return self.output_formatter.generate_report_package(report_data, formats)

    async def get_memory_stats(self) -> dict:
        """Get memory system statistics"""
        if self.memory_manager:
            return await self.memory_manager.get_memory_stats()
        return {"error": "Memory system not available"}

    async def search_memory(
        self,
        query: str,
        memory_types: list = None,
        limit: int = 10
    ) -> list:
        """
        Search the memory system

        Args:
            query: Search query
            memory_types: Types of memory to search
            limit: Maximum results

        Returns:
            List of memory items
        """
        if self.memory_manager:
            return await self.memory_manager.search_all(query, memory_types, limit)
        return []