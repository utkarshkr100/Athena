"""
How to run Athena AI Research System

This demonstrates the core functionality of Athena with Gemini Flash
"""
import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai
from tavily import TavilyClient

load_dotenv('athena_research/.env')

async def athena_research(topic, detailed=True):
    """
    Main Athena research function
    This is how you run Athena research with Gemini Flash
    """
    print(f"ATHENA AI RESEARCH SYSTEM")
    print("=" * 50)
    print(f"Topic: {topic}")
    print("LLM: Google Gemini Flash")
    print("Search: Tavily")
    print("=" * 50)

    # Configure Gemini Flash
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Step 1: Generate research plan
    print("\n[STEP 1] Generating research plan...")
    plan_prompt = f"""
    Create a research plan for: {topic}

    Generate:
    1. 3 key research questions
    2. 3 search queries to find current information
    3. Main areas to investigate

    Keep it concise and focused.
    """

    plan = await model.generate_content_async(plan_prompt)
    print("Research Plan Generated:")
    print(plan.text)

    # Step 2: Conduct web search
    print("\n[STEP 2] Searching for current information...")
    client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

    # Search with multiple queries for better coverage
    search_queries = [
        f"{topic} latest research 2024",
        f"{topic} current developments",
        f"{topic} applications examples"
    ]

    all_results = []
    for query in search_queries:
        results = client.search(query, max_results=2)
        all_results.extend(results['results'])

    print(f"Found {len(all_results)} articles from web search")

    # Step 3: AI analysis and synthesis
    print("\n[STEP 3] AI analysis and synthesis...")

    # Prepare sources for analysis
    sources_text = ""
    for i, result in enumerate(all_results[:6], 1):  # Limit to 6 sources
        sources_text += f"\nSource {i}: {result['title']}\n{result['content'][:300]}...\n"

    analysis_prompt = f"""
    You are an expert researcher. Analyze these sources about {topic} and create a comprehensive research report.

    Sources:
    {sources_text}

    Create a structured report with:

    ## Executive Summary
    [2-3 sentence overview of key findings]

    ## Key Findings
    [3-4 main insights from the sources]

    ## Current Applications
    [Real-world examples and use cases]

    ## Future Outlook
    [Trends and predictions]

    ## Conclusion
    [Summary and implications]

    Be specific, cite insights from the sources, and make it professional.
    """

    report = await model.generate_content_async(analysis_prompt)

    # Display results
    print("\n" + "=" * 60)
    print("ATHENA RESEARCH REPORT")
    print("=" * 60)
    print(report.text)

    print("\n" + "=" * 60)
    print("SOURCES CONSULTED:")
    print("=" * 60)
    for i, result in enumerate(all_results[:6], 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print()

    return {
        'topic': topic,
        'plan': plan.text,
        'report': report.text,
        'sources': all_results[:6]
    }

async def quick_research(topic):
    """Quick research mode - faster, less detailed"""
    print(f"ATHENA QUICK RESEARCH: {topic}")
    print("=" * 40)

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Quick search
    client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    results = client.search(f"{topic} overview", max_results=3)

    # Quick analysis
    sources_text = "\n".join([f"- {r['title']}: {r['content'][:150]}..." for r in results['results']])

    quick_prompt = f"""
    Provide a concise overview of {topic} based on these sources:
    {sources_text}

    Include: key points, current status, and why it matters.
    Keep it under 200 words.
    """

    summary = await model.generate_content_async(quick_prompt)
    print(summary.text)
    print(f"\nSources: {len(results['results'])} articles consulted")

# Example usage
async def main():
    """Demonstrate how to use Athena"""

    print("ATHENA AI RESEARCH SYSTEM DEMO")
    print("Using: Gemini Flash + Tavily Search")
    print("=" * 50)

    # Example 1: Full research
    topic1 = "artificial intelligence in medical diagnosis"
    result1 = await athena_research(topic1)

    print("\n\n" + "=" * 80)

    # Example 2: Quick research
    topic2 = "quantum computing advantages"
    await quick_research(topic2)

if __name__ == "__main__":
    # This is how you run Athena!
    asyncio.run(main())