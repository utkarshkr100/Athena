from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import re
import json

class CitationStyle(Enum):
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    HARVARD = "harvard"

@dataclass
class Source:
    title: str
    url: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    source_type: str = "web"  # web, academic, book, news, etc.
    access_date: Optional[str] = None
    doi: Optional[str] = None
    pages: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None

class CitationManager:
    """Manages citations and bibliography generation for research reports"""

    def __init__(self, style: CitationStyle = CitationStyle.APA):
        self.style = style
        self.sources = {}  # source_id -> Source
        self.citation_counter = 0
        self.inline_citations = {}  # text_location -> citation_id

    def add_source(
        self,
        title: str,
        url: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publication_date: Optional[str] = None,
        publisher: Optional[str] = None,
        source_type: str = "web",
        **kwargs
    ) -> str:
        """Add a source and return its citation ID"""

        self.citation_counter += 1
        citation_id = f"ref_{self.citation_counter}"

        # Set access date for web sources
        access_date = kwargs.get('access_date')
        if source_type == "web" and not access_date:
            access_date = datetime.now().strftime("%Y-%m-%d")

        source = Source(
            title=title,
            url=url,
            authors=authors,
            publication_date=publication_date,
            publisher=publisher,
            source_type=source_type,
            access_date=access_date,
            doi=kwargs.get('doi'),
            pages=kwargs.get('pages'),
            volume=kwargs.get('volume'),
            issue=kwargs.get('issue')
        )

        self.sources[citation_id] = source
        return citation_id

    def get_inline_citation(self, citation_id: str) -> str:
        """Generate inline citation for the given source"""
        if citation_id not in self.sources:
            return f"[Unknown source: {citation_id}]"

        source = self.sources[citation_id]

        if self.style == CitationStyle.APA:
            return self._format_apa_inline(source, citation_id)
        elif self.style == CitationStyle.MLA:
            return self._format_mla_inline(source, citation_id)
        elif self.style == CitationStyle.CHICAGO:
            return self._format_chicago_inline(source, citation_id)
        elif self.style == CitationStyle.IEEE:
            return self._format_ieee_inline(citation_id)
        elif self.style == CitationStyle.HARVARD:
            return self._format_harvard_inline(source, citation_id)
        else:
            return f"[{citation_id}]"

    def get_bibliography_entry(self, citation_id: str) -> str:
        """Generate bibliography entry for the given source"""
        if citation_id not in self.sources:
            return f"Unknown source: {citation_id}"

        source = self.sources[citation_id]

        if self.style == CitationStyle.APA:
            return self._format_apa_bibliography(source)
        elif self.style == CitationStyle.MLA:
            return self._format_mla_bibliography(source)
        elif self.style == CitationStyle.CHICAGO:
            return self._format_chicago_bibliography(source)
        elif self.style == CitationStyle.IEEE:
            return self._format_ieee_bibliography(source, citation_id)
        elif self.style == CitationStyle.HARVARD:
            return self._format_harvard_bibliography(source)
        else:
            return f"{source.title}. {source.url}"

    def generate_bibliography(self) -> List[str]:
        """Generate complete bibliography sorted appropriately"""
        entries = []

        if self.style == CitationStyle.IEEE:
            # IEEE uses numerical order
            sorted_ids = sorted(self.sources.keys(), key=lambda x: int(x.split('_')[1]))
        else:
            # Most styles use alphabetical order by author/title
            sorted_ids = sorted(
                self.sources.keys(),
                key=lambda x: self._get_sort_key(self.sources[x])
            )

        for citation_id in sorted_ids:
            entry = self.get_bibliography_entry(citation_id)
            entries.append(entry)

        return entries

    def add_inline_citation_to_text(self, text: str, citation_id: str, position: int = None) -> str:
        """Add inline citation to text at specified position or at the end of sentence"""
        if citation_id not in self.sources:
            return text

        inline_citation = self.get_inline_citation(citation_id)

        if position is not None:
            # Insert at specific position
            return text[:position] + inline_citation + text[position:]
        else:
            # Add at end of last sentence
            # Find the last sentence ending
            sentence_endings = ['.', '!', '?']
            last_ending = -1

            for ending in sentence_endings:
                pos = text.rfind(ending)
                if pos > last_ending:
                    last_ending = pos

            if last_ending != -1:
                return text[:last_ending] + inline_citation + text[last_ending:]
            else:
                return text + " " + inline_citation

    def extract_and_cite_sources(self, content: str, sources_data: List[Dict[str, Any]]) -> str:
        """Extract sources from content and add citations"""
        cited_content = content

        for source_data in sources_data:
            # Add source to manager
            citation_id = self.add_source(
                title=source_data.get('title', 'Untitled'),
                url=source_data.get('url'),
                authors=source_data.get('authors'),
                publication_date=source_data.get('publication_date'),
                publisher=source_data.get('publisher'),
                source_type=source_data.get('source_type', 'web')
            )

            # Look for content that should be cited
            title_words = source_data.get('title', '').split()[:3]  # First 3 words
            if len(title_words) >= 2:
                search_pattern = ' '.join(title_words)
                if search_pattern.lower() in content.lower():
                    # Add citation near this content
                    pattern = re.compile(re.escape(search_pattern), re.IGNORECASE)
                    matches = list(pattern.finditer(content))

                    if matches:
                        # Add citation after the first match
                        match = matches[0]
                        citation = self.get_inline_citation(citation_id)
                        insert_pos = match.end()
                        cited_content = (
                            cited_content[:insert_pos] +
                            citation +
                            cited_content[insert_pos:]
                        )

        return cited_content

    def get_citation_summary(self) -> Dict[str, Any]:
        """Get summary of all citations"""
        source_types = {}
        for source in self.sources.values():
            source_types[source.source_type] = source_types.get(source.source_type, 0) + 1

        return {
            "total_sources": len(self.sources),
            "citation_style": self.style.value,
            "source_types": source_types,
            "sources_by_id": {
                citation_id: {
                    "title": source.title,
                    "source_type": source.source_type,
                    "url": source.url
                }
                for citation_id, source in self.sources.items()
            }
        }

    def export_citations(self, format_type: str = "json") -> str:
        """Export citations in specified format"""
        if format_type == "json":
            return json.dumps(self.get_citation_summary(), indent=2)
        elif format_type == "bibtex":
            return self._export_bibtex()
        elif format_type == "ris":
            return self._export_ris()
        else:
            return str(self.get_citation_summary())

    # Style-specific formatting methods
    def _format_apa_inline(self, source: Source, citation_id: str) -> str:
        """Format APA inline citation"""
        if source.authors:
            author = source.authors[0].split()[-1]  # Last name
            year = self._extract_year(source.publication_date) if source.publication_date else "n.d."
            return f"({author}, {year})"
        else:
            title_short = source.title.split()[0] if source.title else "Unknown"
            year = self._extract_year(source.publication_date) if source.publication_date else "n.d."
            return f"({title_short}, {year})"

    def _format_apa_bibliography(self, source: Source) -> str:
        """Format APA bibliography entry"""
        parts = []

        # Author
        if source.authors:
            authors_formatted = []
            for author in source.authors:
                if ', ' in author:
                    authors_formatted.append(author)  # Already in Last, F. format
                else:
                    name_parts = author.split()
                    if len(name_parts) >= 2:
                        last_name = name_parts[-1]
                        initials = '. '.join([n[0] for n in name_parts[:-1]]) + '.'
                        authors_formatted.append(f"{last_name}, {initials}")
            parts.append(', '.join(authors_formatted))

        # Year
        year = self._extract_year(source.publication_date) if source.publication_date else "n.d."
        parts.append(f"({year})")

        # Title
        if source.source_type in ['book', 'report']:
            parts.append(f"*{source.title}*")
        else:
            parts.append(source.title)

        # Publisher/URL
        if source.publisher:
            parts.append(source.publisher)
        if source.url:
            parts.append(f"Retrieved from {source.url}")

        return '. '.join(parts) + '.'

    def _format_ieee_inline(self, citation_id: str) -> str:
        """Format IEEE inline citation (numerical)"""
        number = citation_id.split('_')[1]
        return f"[{number}]"

    def _format_ieee_bibliography(self, source: Source, citation_id: str) -> str:
        """Format IEEE bibliography entry"""
        number = citation_id.split('_')[1]
        parts = [f"[{number}]"]

        # Authors
        if source.authors:
            if len(source.authors) == 1:
                parts.append(source.authors[0])
            else:
                parts.append(', '.join(source.authors))

        # Title
        if source.source_type == 'book':
            parts.append(f'*{source.title}*')
        else:
            parts.append(f'"{source.title}"')

        # Publisher/URL
        if source.publisher:
            parts.append(source.publisher)

        # Date
        if source.publication_date:
            year = self._extract_year(source.publication_date)
            parts.append(year)

        # URL
        if source.url:
            access_date = source.access_date or datetime.now().strftime("%Y-%m-%d")
            parts.append(f"[Online]. Available: {source.url}. [Accessed: {access_date}]")

        return ', '.join(parts) + '.'

    def _format_mla_inline(self, source: Source, citation_id: str) -> str:
        """Format MLA inline citation"""
        if source.authors:
            author = source.authors[0].split()[-1]  # Last name
            if source.pages:
                return f"({author} {source.pages})"
            else:
                return f"({author})"
        else:
            title_short = source.title.split()[0] if source.title else "Unknown"
            return f"({title_short})"

    def _format_mla_bibliography(self, source: Source) -> str:
        """Format MLA bibliography entry"""
        parts = []

        # Author
        if source.authors:
            parts.append(source.authors[0])  # MLA uses first author only in works cited

        # Title
        if source.source_type in ['book']:
            parts.append(f"*{source.title}*")
        else:
            parts.append(f'"{source.title}"')

        # Publisher and date
        if source.publisher:
            parts.append(source.publisher)

        if source.publication_date:
            year = self._extract_year(source.publication_date)
            parts.append(year)

        # URL and access date for web sources
        if source.url and source.source_type == 'web':
            parts.append(f"Web. {source.access_date}")
            parts.append(source.url)

        return ', '.join(parts) + '.'

    def _format_chicago_inline(self, source: Source, citation_id: str) -> str:
        """Format Chicago inline citation"""
        number = citation_id.split('_')[1]
        return f"^{number}"

    def _format_chicago_bibliography(self, source: Source) -> str:
        """Format Chicago bibliography entry"""
        # Similar to APA but with different punctuation
        return self._format_apa_bibliography(source)

    def _format_harvard_inline(self, source: Source, citation_id: str) -> str:
        """Format Harvard inline citation"""
        return self._format_apa_inline(source, citation_id)  # Very similar to APA

    def _format_harvard_bibliography(self, source: Source) -> str:
        """Format Harvard bibliography entry"""
        return self._format_apa_bibliography(source)  # Very similar to APA

    def _extract_year(self, date_string: str) -> str:
        """Extract year from date string"""
        if not date_string:
            return "n.d."

        # Try to extract 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
        if year_match:
            return year_match.group()

        return date_string[:4] if len(date_string) >= 4 else "n.d."

    def _get_sort_key(self, source: Source) -> str:
        """Get sorting key for bibliography"""
        if source.authors:
            return source.authors[0].lower()
        else:
            return source.title.lower()

    def _export_bibtex(self) -> str:
        """Export citations in BibTeX format"""
        bibtex_entries = []

        for citation_id, source in self.sources.items():
            entry_type = "article" if source.source_type in ["web", "news"] else "book"

            bibtex_entry = f"@{entry_type}{{{citation_id},\n"
            bibtex_entry += f"  title={{{source.title}}},\n"

            if source.authors:
                bibtex_entry += f"  author={{{' and '.join(source.authors)}}},\n"

            if source.publication_date:
                year = self._extract_year(source.publication_date)
                bibtex_entry += f"  year={{{year}}},\n"

            if source.url:
                bibtex_entry += f"  url={{{source.url}}},\n"

            if source.publisher:
                bibtex_entry += f"  publisher={{{source.publisher}}},\n"

            bibtex_entry += "}\n"
            bibtex_entries.append(bibtex_entry)

        return "\n".join(bibtex_entries)

    def _export_ris(self) -> str:
        """Export citations in RIS format"""
        ris_entries = []

        for citation_id, source in self.sources.items():
            ris_entry = []

            # Type
            if source.source_type == "book":
                ris_entry.append("TY  - BOOK")
            else:
                ris_entry.append("TY  - ELEC")

            # Title
            ris_entry.append(f"TI  - {source.title}")

            # Authors
            if source.authors:
                for author in source.authors:
                    ris_entry.append(f"AU  - {author}")

            # Year
            if source.publication_date:
                year = self._extract_year(source.publication_date)
                ris_entry.append(f"PY  - {year}")

            # URL
            if source.url:
                ris_entry.append(f"UR  - {source.url}")

            # Publisher
            if source.publisher:
                ris_entry.append(f"PB  - {source.publisher}")

            # End of record
            ris_entry.append("ER  - ")

            ris_entries.append("\n".join(ris_entry))

        return "\n\n".join(ris_entries)