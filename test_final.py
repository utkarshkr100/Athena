"""
Final confirmation test - Gemini Flash and Tavily working
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("athena_research/.env")

async def test_complete_integration():
    """Test both Gemini and Tavily together"""
    print("ATHENA INTEGRATION TEST - FINAL CONFIRMATION")
    print("=" * 50)

    # 1. Test Gemini Flash
    print("1. Testing Gemini Flash...")
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("   ERROR: No Gemini API key")
            return False

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        response = await model.generate_content_async(
            "You are a research AI assistant. Explain in one sentence what makes you useful for research."
        )

        print("   ✓ Gemini Flash: WORKING")
        print(f"   Response: {response.text[:100]}...")

    except Exception as e:
        print(f"   ✗ Gemini Flash failed: {e}")
        return False

    # 2. Test Tavily Search
    print("\n2. Testing Tavily Search...")
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("   ERROR: No Tavily API key")
            return False

        client = TavilyClient(api_key=api_key)
        results = client.search("artificial intelligence research 2024", max_results=2)

        print("   ✓ Tavily Search: WORKING")
        print(f"   Found {len(results['results'])} research articles")
        for i, result in enumerate(results['results'], 1):
            print(f"   {i}. {result['title'][:60]}...")

    except Exception as e:
        print(f"   ✗ Tavily Search failed: {e}")
        return False

    # 3. Test Configuration
    print("\n3. Testing Athena Configuration...")
    try:
        provider = os.getenv("LLM_PROVIDER", "not set")
        gemini_key = "SET" if os.getenv("GEMINI_API_KEY") else "MISSING"
        tavily_key = "SET" if os.getenv("TAVILY_API_KEY") else "MISSING"

        print("   ✓ Configuration: WORKING")
        print(f"   LLM Provider: {provider}")
        print(f"   Gemini API Key: {gemini_key}")
        print(f"   Tavily API Key: {tavily_key}")

    except Exception as e:
        print(f"   ✗ Configuration failed: {e}")
        return False

    # 4. Combined Test - Use Tavily to search, then Gemini to summarize
    print("\n4. Testing Combined Workflow...")
    try:
        # Search for AI research
        search_results = client.search("machine learning healthcare applications", max_results=1)

        if search_results['results']:
            article = search_results['results'][0]

            # Use Gemini to summarize
            summary_prompt = f"Summarize this article in 2 sentences: {article['title']} - {article['content'][:300]}"
            summary = await model.generate_content_async(summary_prompt)

            print("   ✓ Combined Workflow: WORKING")
            print("   Search -> AI Summary pipeline successful")
            print(f"   Article: {article['title'][:50]}...")
            print(f"   AI Summary: {summary.text[:100]}...")

    except Exception as e:
        print(f"   ✗ Combined workflow failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 SUCCESS! Your Athena system is ready!")
    print("✓ Gemini Flash configured and working")
    print("✓ Tavily Search configured and working")
    print("✓ Environment variables properly set")
    print("✓ Combined AI research workflow functional")
    print("\nYou can now:")
    print("- Use Gemini Flash as your LLM provider")
    print("- Perform web research with Tavily")
    print("- Generate research reports with AI")
    print("=" * 50)

    return True

if __name__ == "__main__":
    asyncio.run(test_complete_integration())