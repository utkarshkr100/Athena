"""
Custom research workflow test
"""
import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai
from tavily import TavilyClient

load_dotenv('athena_research/.env')

async def custom_research_workflow(topic):
    """Custom AI research workflow"""
    print(f"🔍 Researching: {topic}")
    print("=" * 50)

    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Step 1: Search with Tavily
    print("1. Searching for latest information...")
    client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    search_results = client.search(f"{topic} latest developments 2024", max_results=3)

    articles = []
    for result in search_results['results']:
        articles.append({
            'title': result['title'],
            'snippet': result['content'][:200] + '...'
        })

    print(f"   Found {len(articles)} relevant articles")

    # Step 2: Use AI to generate research questions
    print("\n2. Generating research questions...")
    questions_prompt = f"Generate 3 specific research questions about {topic} based on current trends."
    questions_response = await model.generate_content_async(questions_prompt)
    print(f"   AI Questions: {questions_response.text}")

    # Step 3: Analyze search results with AI
    print("\n3. Analyzing search results...")
    articles_text = "\n".join([f"- {art['title']}: {art['snippet']}" for art in articles])
    analysis_prompt = f"""
    Analyze these recent articles about {topic}:

    {articles_text}

    Provide a 2-paragraph summary of the key insights and trends.
    """

    analysis = await model.generate_content_async(analysis_prompt)

    # Results
    print("\n" + "=" * 50)
    print("🎯 RESEARCH SUMMARY")
    print("=" * 50)
    print(analysis.text)
    print("\n📚 Sources:")
    for i, article in enumerate(articles, 1):
        print(f"   {i}. {article['title']}")

    return {
        'topic': topic,
        'questions': questions_response.text,
        'analysis': analysis.text,
        'sources': articles
    }

async def main():
    # Test with different topics
    topics = [
        "artificial intelligence in healthcare",
        "quantum computing applications"
    ]

    for topic in topics:
        result = await custom_research_workflow(topic)
        print("\n" + "🔄" * 20)
        print()

if __name__ == "__main__":
    asyncio.run(main())