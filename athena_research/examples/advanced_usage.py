"""
Advanced usage examples of the Athena Research System

This example demonstrates advanced features like custom configurations,
memory management, and specialized research workflows.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from athena_research import (
    AthenaResearchSystem,
    CitationStyle,
    MemoryManager,
    AzureSearchTool,
    TavilySearchTool,
    BingSearchTool
)

async def custom_configuration_example():
    """Example of custom system configuration"""
    print("⚙️ Custom Configuration Demo")
    print("=" * 35)

    # Custom search tool configuration
    search_tools = []

    try:
        # Configure Azure Search with custom parameters
        if os.getenv("AZURE_SEARCH_API_KEY"):
            azure_tool = AzureSearchTool(
                service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
                api_key=os.getenv("AZURE_SEARCH_API_KEY"),
                index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
            )
            if await azure_tool.is_available():
                search_tools.append(azure_tool)
                print("✅ Azure Search configured")
    except Exception as e:
        print(f"Azure Search configuration failed: {e}")

    try:
        # Configure Tavily
        if os.getenv("TAVILY_API_KEY"):
            tavily_tool = TavilySearchTool(os.getenv("TAVILY_API_KEY"))
            if await tavily_tool.is_available():
                search_tools.append(tavily_tool)
                print("✅ Tavily Search configured")
    except Exception as e:
        print(f"Tavily configuration failed: {e}")

    try:
        # Configure Bing
        if os.getenv("BING_SEARCH_API_KEY"):
            bing_tool = BingSearchTool(os.getenv("BING_SEARCH_API_KEY"))
            if await bing_tool.is_available():
                search_tools.append(bing_tool)
                print("✅ Bing Search configured")
    except Exception as e:
        print(f"Bing configuration failed: {e}")

    print(f"📊 Total search tools available: {len(search_tools)}")

    # Initialize system with IEEE citation style
    system = AthenaResearchSystem(citation_style=CitationStyle.IEEE)

    return system

async def specialized_research_workflow():
    """Example of specialized research workflow"""
    print("\n🎯 Specialized Research Workflow")
    print("=" * 40)

    system = await custom_configuration_example()

    # Define multiple related research topics
    research_topics = [
        "Natural Language Processing in Healthcare",
        "Computer Vision for Medical Diagnosis",
        "AI Ethics in Medical Applications"
    ]

    results = {}

    for topic in research_topics:
        print(f"\n🔍 Researching: {topic}")

        try:
            result = await system.research(
                topic=topic,
                report_style="detailed",
                user_requirements=f"Focus on recent developments in {topic.lower()}, include case studies and practical implementations"
            )

            if result["success"]:
                results[topic] = result
                print(f"✅ Completed research on {topic}")

                # Save individual report
                markdown_report = system.export_report(result, format="markdown")
                filename = f"report_{topic.lower().replace(' ', '_')}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(markdown_report)
                print(f"📄 Saved {filename}")

            else:
                print(f"❌ Failed to research {topic}: {result.get('error')}")

        except Exception as e:
            print(f"❌ Error researching {topic}: {str(e)}")

    # Create a combined summary report
    if results:
        await create_combined_report(results, system)

    return results

async def create_combined_report(results: Dict[str, Any], system: AthenaResearchSystem):
    """Create a combined report from multiple research results"""
    print("\n📋 Creating Combined Report")
    print("=" * 30)

    combined_sections = []
    total_sources = 0

    # Combine all sections from different reports
    for topic, result in results.items():
        if result["success"] and "report" in result:
            report = result["report"]
            total_sources += len(result.get("metadata", {}).get("total_sources", 0))

            # Add topic as a main section
            combined_sections.append({
                "title": topic,
                "content": report.get("executive_summary", f"Research on {topic}"),
                "citations": []
            })

            # Add subsections
            for section in report.get("sections", []):
                section_copy = section.copy()
                section_copy["title"] = f"{topic}: {section['title']}"
                combined_sections.append(section_copy)

    # Create combined report structure
    combined_report = {
        "title": "Comprehensive AI in Healthcare Research Report",
        "executive_summary": "This comprehensive report examines multiple aspects of artificial intelligence applications in healthcare, covering natural language processing, computer vision, and ethical considerations.",
        "sections": combined_sections,
        "metadata": {
            "topics_covered": len(results),
            "total_sections": len(combined_sections),
            "total_sources": total_sources,
            "report_type": "combined_analysis"
        }
    }

    # Export combined report
    formats = ["markdown", "html", "json"]
    for format_type in formats:
        try:
            formatted_content = system.output_formatter.format_as_markdown(combined_report) if format_type == "markdown" else \
                               system.output_formatter.format_as_html(combined_report) if format_type == "html" else \
                               system.output_formatter.format_as_json(combined_report)

            filename = f"combined_report.{format_type}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            print(f"✅ Saved {filename}")

        except Exception as e:
            print(f"❌ Error saving {format_type} format: {e}")

async def memory_management_example():
    """Example of advanced memory management"""
    print("\n🧠 Advanced Memory Management")
    print("=" * 35)

    system = AthenaResearchSystem()

    if not system.memory_manager:
        print("❌ Memory system not available")
        return

    try:
        # Store some facts manually
        await system.memory_manager.store_fact(
            "Machine learning models can analyze medical images with accuracy comparable to human radiologists",
            metadata={"importance": "high", "domain": "medical_ai", "source": "research_study"}
        )

        await system.memory_manager.store_fact(
            "Natural language processing can extract key information from clinical notes and medical records",
            metadata={"importance": "high", "domain": "medical_ai", "source": "literature_review"}
        )

        # Retrieve facts
        facts = await system.memory_manager.retrieve_facts(
            "machine learning medical imaging",
            limit=5
        )

        print(f"📊 Retrieved {len(facts)} relevant facts:")
        for fact in facts:
            print(f"  - {fact.content[:100]}...")
            print(f"    Importance: {fact.metadata.get('importance', 'unknown')}")

        # Get memory statistics
        stats = await system.memory_manager.get_memory_stats()
        print(f"\n📈 Memory Statistics:")
        for store_name, store_stats in stats.items():
            print(f"  {store_name}: {store_stats}")

    except Exception as e:
        print(f"❌ Memory management error: {e}")

async def citation_styles_example():
    """Example of different citation styles"""
    print("\n📚 Citation Styles Demo")
    print("=" * 25)

    # Sample research data
    sample_report = {
        "title": "Sample Research Report",
        "sections": [{
            "title": "Introduction",
            "content": "This is sample content with citations.",
            "citations": [{
                "id": "1",
                "title": "Machine Learning in Healthcare",
                "url": "https://example.com/ml-healthcare",
                "authors": ["Smith, J.", "Johnson, A."],
                "publication_date": "2024",
                "source_type": "academic"
            }]
        }]
    }

    citation_styles = [
        CitationStyle.APA,
        CitationStyle.MLA,
        CitationStyle.IEEE,
        CitationStyle.CHICAGO
    ]

    for style in citation_styles:
        print(f"\n📖 {style.value.upper()} Style:")
        system = AthenaResearchSystem(citation_style=style)

        try:
            formatted = system.export_report(
                {"success": True, "report": sample_report},
                format="markdown"
            )

            # Extract just the citation part for display
            lines = formatted.split('\n')
            ref_section = False
            for line in lines:
                if line.startswith("## References"):
                    ref_section = True
                elif ref_section and line.strip() and not line.startswith("---"):
                    print(f"  {line.strip()}")
                    break

        except Exception as e:
            print(f"  Error with {style.value}: {e}")

async def main():
    """Run all advanced examples"""
    print("🚀 Athena Research System - Advanced Examples")
    print("=" * 50)

    # Run all examples
    await custom_configuration_example()
    await specialized_research_workflow()
    await memory_management_example()
    await citation_styles_example()

    print("\n🏆 All advanced examples completed!")
    print("\nNote: Make sure to configure your API keys in environment variables:")
    print("  - AZURE_OPENAI_API_KEY")
    print("  - AZURE_SEARCH_API_KEY")
    print("  - TAVILY_API_KEY")
    print("  - BING_SEARCH_API_KEY")

if __name__ == "__main__":
    asyncio.run(main())