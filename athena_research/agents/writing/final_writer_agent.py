from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
from datetime import datetime
from ..base_agent import BaseAgent, AgentResponse, AgentMessage
from .section_writer_agent import SectionContent, Citation
from ...config import settings

class FinalReport(BaseModel):
    title: str
    executive_summary: str
    sections: List[SectionContent]
    bibliography: List[Citation]
    metadata: Dict[str, Any]
    generated_at: datetime
    total_word_count: int

class FinalWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FinalWriterAgent",
            model=settings.writing_model,
            temperature=settings.default_temperature
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            topic = input_data.get("topic", "")
            sections_data = input_data.get("sections", [])
            report_style = input_data.get("style", "academic")
            include_executive_summary = input_data.get("include_summary", True)

            # Convert section data back to objects
            sections = [
                SectionContent(**section) if isinstance(section, dict) else section
                for section in sections_data
            ]

            final_report = await self._compile_final_report(
                topic,
                sections,
                report_style,
                include_executive_summary
            )

            return AgentResponse(
                success=True,
                data=final_report.dict(),
                sources=[citation.dict() for citation in final_report.bibliography]
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                data=None,
                error=str(e)
            )

    async def _compile_final_report(
        self,
        topic: str,
        sections: List[SectionContent],
        style: str,
        include_summary: bool
    ) -> FinalReport:
        # Generate title
        title = await self._generate_title(topic, sections)

        # Compile bibliography from all sections
        bibliography = await self._compile_bibliography(sections)

        # Generate executive summary if requested
        executive_summary = ""
        if include_summary:
            executive_summary = await self._generate_executive_summary(topic, sections)

        # Calculate total word count
        total_words = sum(section.word_count for section in sections)
        if executive_summary:
            total_words += len(executive_summary.split())

        # Create metadata
        metadata = await self._generate_metadata(topic, sections, style)

        final_report = FinalReport(
            title=title,
            executive_summary=executive_summary,
            sections=sections,
            bibliography=bibliography,
            metadata=metadata,
            generated_at=datetime.now(),
            total_word_count=total_words
        )

        return final_report

    async def _generate_title(self, topic: str, sections: List[SectionContent]) -> str:
        # Simple title generation - in practice, this would use the LLM
        section_themes = [section.title for section in sections]
        return f"Comprehensive Analysis of {topic}: Insights and Implications"

    async def _compile_bibliography(self, sections: List[SectionContent]) -> List[Citation]:
        # Deduplicate citations across all sections
        all_citations = []
        seen_urls = set()
        seen_titles = set()

        citation_id_counter = 0

        for section in sections:
            for citation in section.citations:
                # Create unique identifiers
                url_key = citation.url or f"no_url_{hash(citation.title)}"
                title_key = citation.title.lower().strip()

                if url_key not in seen_urls and title_key not in seen_titles:
                    seen_urls.add(url_key)
                    seen_titles.add(title_key)

                    # Renumber citations for final bibliography
                    citation_id_counter += 1
                    updated_citation = citation.copy()
                    updated_citation.id = str(citation_id_counter)

                    all_citations.append(updated_citation)

        # Sort bibliography alphabetically by title
        all_citations.sort(key=lambda x: x.title.lower())

        return all_citations

    async def _generate_executive_summary(
        self,
        topic: str,
        sections: List[SectionContent]
    ) -> str:
        # Extract key points from all sections
        all_key_points = []
        for section in sections:
            all_key_points.extend(section.key_points)

        # Create summary prompt
        summary_prompt = f"""
        Generate a concise executive summary for a research report on: {topic}

        Key findings from sections:
        {chr(10).join(f"• {point}" for point in all_key_points[:15])}

        Section titles covered:
        {chr(10).join(f"- {section.title}" for section in sections)}

        Create a 3-4 paragraph executive summary that:
        1. Introduces the topic and scope
        2. Highlights the most important findings
        3. Discusses implications or conclusions
        4. Mentions the research methodology (multi-source analysis)
        """

        self.add_message(AgentMessage(role="user", content=summary_prompt))

        # Simplified summary generation
        summary = f"""**Executive Summary**

This comprehensive analysis of {topic} examines multiple dimensions through systematic research across various authoritative sources. The investigation covers {len(sections)} key areas, providing insights into current developments, applications, and future implications.

The research reveals several critical findings: {' '.join(all_key_points[:3])} These insights demonstrate the evolving nature of {topic} and its significance in contemporary contexts.

Key implications include the need for continued research, practical applications across different sectors, and strategic considerations for future development. The analysis synthesizes information from {sum(len(section.citations) for section in sections)} sources, ensuring comprehensive coverage of the topic.

This report serves as a foundation for understanding {topic} and provides actionable insights for stakeholders, researchers, and practitioners in related fields."""

        self.add_message(AgentMessage(role="assistant", content=summary))

        return summary

    async def _generate_metadata(
        self,
        topic: str,
        sections: List[SectionContent],
        style: str
    ) -> Dict[str, Any]:
        source_types = set()
        total_sources = 0

        for section in sections:
            for citation in section.citations:
                source_types.add(citation.source_type)
                total_sources += 1

        metadata = {
            "research_topic": topic,
            "report_style": style,
            "total_sections": len(sections),
            "total_sources": total_sources,
            "source_types": list(source_types),
            "sections_overview": [
                {
                    "title": section.title,
                    "word_count": section.word_count,
                    "citations": len(section.citations)
                }
                for section in sections
            ],
            "generation_method": "multi-agent-research-system",
            "version": "1.0"
        }

        return metadata

    async def format_as_markdown(self, report: FinalReport) -> str:
        """Format the final report as Markdown"""
        markdown_parts = []

        # Title
        markdown_parts.append(f"# {report.title}")
        markdown_parts.append(f"*Generated on {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*")
        markdown_parts.append("")

        # Executive Summary
        if report.executive_summary:
            markdown_parts.append("## Executive Summary")
            markdown_parts.append(report.executive_summary)
            markdown_parts.append("")

        # Table of Contents
        markdown_parts.append("## Table of Contents")
        for i, section in enumerate(report.sections, 1):
            markdown_parts.append(f"{i}. [{section.title}](#{section.title.lower().replace(' ', '-')})")
        markdown_parts.append("")

        # Sections
        for section in report.sections:
            markdown_parts.append(f"## {section.title}")
            markdown_parts.append(section.content)
            markdown_parts.append("")

        # Bibliography
        if report.bibliography:
            markdown_parts.append("## References")
            for citation in report.bibliography:
                ref_line = f"[{citation.id}] {citation.title}"
                if citation.url:
                    ref_line += f" - {citation.url}"
                ref_line += f" ({citation.source_type})"
                markdown_parts.append(ref_line)
            markdown_parts.append("")

        # Metadata
        markdown_parts.append("---")
        markdown_parts.append("## Report Metadata")
        markdown_parts.append(f"- **Total Word Count**: {report.total_word_count}")
        markdown_parts.append(f"- **Total Sources**: {report.metadata['total_sources']}")
        markdown_parts.append(f"- **Source Types**: {', '.join(report.metadata['source_types'])}")
        markdown_parts.append(f"- **Generated by**: Athena Multi-Agent Research System")

        return "\n".join(markdown_parts)

    async def format_as_json(self, report: FinalReport) -> str:
        """Format the final report as JSON"""
        return json.dumps(report.dict(), indent=2, default=str)