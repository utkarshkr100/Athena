"""
Basic usage example of the Athena Research System

This example demonstrates how to use the Athena system to conduct
research on a topic and export the results in various formats.
"""

import asyncio
import os
from pathlib import Path

# Add the parent directory to the path so we can import athena_research
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from athena_research import AthenaResearchSystem, CitationStyle

async def basic_research_example():
    """Basic research example"""
    print("🔬 Starting Athena Research System Demo")
    print("=" * 50)

    # Initialize the system
    # Note: You'll need to set up your API keys in environment variables or .env file
    system = AthenaResearchSystem(
        citation_style=CitationStyle.APA
    )

    # Conduct research on a topic
    topic = "Machine Learning in Climate Change Prediction"
    print(f"📚 Researching: {topic}")
    print("This may take several minutes...")

    try:
        # Execute the research workflow
        result = await system.research(
            topic=topic,
            report_style="comprehensive",
            user_requirements="Focus on recent developments and practical applications"
        )

        if result["success"]:
            print("✅ Research completed successfully!")
            print(f"📄 Generated {result['metadata']['total_sections']} sections")
            print(f"🔗 Used {result['metadata']['total_sources']} sources")

            # Export the report in different formats
            print("\n📤 Exporting reports...")

            # Export as Markdown
            markdown_report = system.export_report(result, format="markdown")
            with open("research_report.md", "w", encoding="utf-8") as f:
                f.write(markdown_report)
            print("✅ Saved research_report.md")

            # Export as HTML
            html_report = system.export_report(result, format="html")
            with open("research_report.html", "w", encoding="utf-8") as f:
                f.write(html_report)
            print("✅ Saved research_report.html")

            # Export as JSON
            json_report = system.export_report(result, format="json")
            with open("research_report.json", "w", encoding="utf-8") as f:
                f.write(json_report)
            print("✅ Saved research_report.json")

            # Export multiple formats at once
            multi_format = system.export_multiple_formats(
                result,
                formats=["markdown", "html", "json", "latex"]
            )

            for filename, content in multi_format.items():
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Saved {filename}")

        else:
            print(f"❌ Research failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error during research: {str(e)}")
        print("Make sure you have configured your API keys properly!")

    print("\n" + "=" * 50)
    print("🏁 Demo completed!")

async def memory_system_example():
    """Example of using the memory system"""
    print("\n🧠 Memory System Demo")
    print("=" * 30)

    system = AthenaResearchSystem()

    # Check memory stats
    try:
        stats = await system.get_memory_stats()
        print(f"📊 Memory Stats: {stats}")

        # Search memory (if there's existing data)
        memory_results = await system.search_memory(
            query="machine learning",
            limit=5
        )
        print(f"🔍 Found {len(memory_results)} items in memory")

        for item in memory_results:
            print(f"  - {item['memory_type']}: {item['content'][:100]}...")

    except Exception as e:
        print(f"Memory system info: {e}")

if __name__ == "__main__":
    # Run the basic example
    asyncio.run(basic_research_example())

    # Run the memory example
    asyncio.run(memory_system_example())