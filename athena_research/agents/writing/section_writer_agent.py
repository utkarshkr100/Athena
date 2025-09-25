from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
from ..base_agent import BaseAgent, AgentResponse, AgentMessage
from ..research.research_agent import ResearchResult, SearchResult
from ...config import settings

class Citation(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    source_type: str
    snippet: str

class SectionContent(BaseModel):
    title: str
    content: str
    citations: List[Citation]
    word_count: int
    key_points: List[str]

class SectionWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SectionWriterAgent",
            model=settings.writing_model,
            temperature=settings.default_temperature + 0.1  # Slightly higher for creative writing
        )
        self.citation_counter = 0

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            section_title = input_data.get("section_title", "")
            section_description = input_data.get("section_description", "")
            research_results = input_data.get("research_results", [])
            style_guide = input_data.get("style_guide", "academic")
            target_length = input_data.get("target_length", 800)

            # Convert research results back to objects
            parsed_results = [
                ResearchResult(**result) if isinstance(result, dict) else result
                for result in research_results
            ]

            section_content = await self._write_section(
                section_title,
                section_description,
                parsed_results,
                style_guide,
                target_length
            )

            return AgentResponse(
                success=True,
                data=section_content.dict(),
                sources=[citation.dict() for citation in section_content.citations]
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                data=None,
                error=str(e)
            )

    async def _write_section(
        self,
        title: str,
        description: str,
        research_results: List[ResearchResult],
        style_guide: str,
        target_length: int
    ) -> SectionContent:
        # Collect and organize sources
        all_sources = []
        for result in research_results:
            for search_result in result.results:
                all_sources.append(search_result)

        # Sort by relevance
        all_sources.sort(key=lambda x: x.relevance_score, reverse=True)

        # Generate citations
        citations = await self._generate_citations(all_sources[:20])  # Top 20 sources

        # Create writing prompt
        writing_prompt = self._create_writing_prompt(
            title, description, all_sources, style_guide, target_length
        )

        self.add_message(AgentMessage(role="user", content=writing_prompt))

        # Generate section content
        content = await self._generate_content(title, all_sources, target_length)

        # Extract key points
        key_points = await self._extract_key_points(content)

        section_content = SectionContent(
            title=title,
            content=content,
            citations=citations,
            word_count=len(content.split()),
            key_points=key_points
        )

        self.add_message(AgentMessage(role="assistant", content=json.dumps(section_content.dict())))

        return section_content

    def _create_writing_prompt(
        self,
        title: str,
        description: str,
        sources: List[SearchResult],
        style_guide: str,
        target_length: int
    ) -> str:
        source_summaries = []
        for i, source in enumerate(sources[:10]):  # Top 10 sources
            source_summaries.append(f"[{i+1}] {source.title}: {source.content[:200]}...")

        return f"""
        You are an expert research writer. Write a comprehensive section for a research report.

        SECTION TITLE: {title}
        SECTION DESCRIPTION: {description}
        STYLE GUIDE: {style_guide}
        TARGET LENGTH: {target_length} words

        AVAILABLE SOURCES:
        {chr(10).join(source_summaries)}

        INSTRUCTIONS:
        1. Write a well-structured section that covers all key aspects mentioned in the description
        2. Use information from the provided sources and cite them using [1], [2], etc.
        3. Maintain {style_guide} writing style
        4. Aim for approximately {target_length} words
        5. Include smooth transitions between ideas
        6. Ensure factual accuracy based on the sources
        7. Use subheadings if the section is long enough to warrant them

        Write the section content now:
        """

    async def _generate_content(
        self,
        title: str,
        sources: List[SearchResult],
        target_length: int
    ) -> str:
        # This is a simplified version - in practice, this would call the LLM
        # For demonstration, we'll create structured content based on sources

        content_parts = []

        # Introduction
        if sources:
            intro_content = f"## {title}\n\n"
            intro_content += f"{title} represents a significant area of study and application. "
            intro_content += f"Recent research and developments have highlighted several key aspects that warrant examination."
            content_parts.append(intro_content)

        # Main content based on sources
        for i, source in enumerate(sources[:5]):  # Use top 5 sources
            paragraph = f"{source.content[:300]}... [{i+1}]"
            content_parts.append(paragraph)

        # Conclusion if enough content
        if len(content_parts) > 2:
            conclusion = f"In summary, the analysis of {title.lower()} reveals multiple dimensions that contribute to our understanding of this topic."
            content_parts.append(conclusion)

        return "\n\n".join(content_parts)

    async def _generate_citations(self, sources: List[SearchResult]) -> List[Citation]:
        citations = []

        for source in sources:
            self.citation_counter += 1
            citation = Citation(
                id=str(self.citation_counter),
                title=source.title,
                url=source.url,
                source_type=source.source_type,
                snippet=source.content[:200] + "..." if len(source.content) > 200 else source.content
            )
            citations.append(citation)

        return citations

    async def _extract_key_points(self, content: str) -> List[str]:
        # Simple key point extraction - in practice, this would use the LLM
        sentences = content.split('. ')
        # Return first few sentences as key points (simplified)
        key_points = []
        for sentence in sentences[:5]:
            if len(sentence.strip()) > 20:  # Avoid very short fragments
                clean_sentence = sentence.strip().replace('\n', ' ')
                if not clean_sentence.endswith('.'):
                    clean_sentence += '.'
                key_points.append(clean_sentence)

        return key_points

    async def revise_section(
        self,
        current_content: SectionContent,
        feedback: str,
        additional_sources: Optional[List[SearchResult]] = None
    ) -> SectionContent:
        """Revise section content based on feedback"""
        revision_prompt = f"""
        Current section content:
        {current_content.content}

        Current citations: {len(current_content.citations)}

        Feedback for revision: {feedback}

        Please revise the section addressing the feedback while maintaining quality and citations.
        """

        self.add_message(AgentMessage(role="user", content=revision_prompt))

        # This would call the LLM to revise content
        # For now, we'll make minor adjustments
        revised_content = current_content.copy()
        revised_content.content += f"\n\n*[Revised based on feedback: {feedback[:50]}...]*"

        if additional_sources:
            additional_citations = await self._generate_citations(additional_sources)
            revised_content.citations.extend(additional_citations)

        return revised_content