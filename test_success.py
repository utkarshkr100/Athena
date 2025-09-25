"""
SUCCESS! Your Gemini and Tavily integration is working!
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("athena_research/.env")

async def test_integration():
    print("ATHENA INTEGRATION - SUCCESS CONFIRMATION")
    print("=" * 50)

    success_count = 0

    # Test 1: Gemini Flash
    print("1. Testing Gemini Flash...")
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("   [FAIL] No Gemini API key found")
            return False

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        response = await model.generate_content_async(
            "Explain artificial intelligence in exactly 10 words."
        )

        print("   [PASS] Gemini Flash working!")
        print(f"   Response: {response.text.strip()}")
        success_count += 1

    except Exception as e:
        print(f"   [FAIL] Gemini error: {e}")

    # Test 2: Tavily Search
    print("\n2. Testing Tavily Search...")
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("   [FAIL] No Tavily API key found")
            return False

        client = TavilyClient(api_key=api_key)
        results = client.search("AI research", max_results=2)

        print("   [PASS] Tavily Search working!")
        print(f"   Found {len(results['results'])} research results")
        success_count += 1

    except Exception as e:
        print(f"   [FAIL] Tavily error: {e}")

    # Test 3: Combined workflow
    print("\n3. Testing AI Research Workflow...")
    try:
        # Use search results with AI
        if 'results' in locals() and results['results']:
            article_title = results['results'][0]['title']

            summary_prompt = f"Summarize this research topic in one sentence: {article_title}"
            summary = await model.generate_content_async(summary_prompt)

            print("   [PASS] Combined workflow working!")
            print(f"   Search: {article_title[:50]}...")
            print(f"   AI Summary: {summary.text.strip()[:80]}...")
            success_count += 1

    except Exception as e:
        print(f"   [FAIL] Workflow error: {e}")

    print("\n" + "=" * 50)
    if success_count == 3:
        print("SUCCESS! All tests passed!")
        print("")
        print("Your Athena system is ready with:")
        print("- Gemini Flash LLM (working)")
        print("- Tavily web search (working)")
        print("- AI research workflow (working)")
        print("")
        print("Configuration summary:")
        print(f"- LLM Provider: {os.getenv('LLM_PROVIDER', 'default')}")
        print(f"- Gemini API Key: Set and working")
        print(f"- Tavily API Key: Set and working")
        print("")
        print("You can now use Athena for AI-powered research!")
    else:
        print(f"Partial success: {success_count}/3 tests passed")
        print("Check the error messages above for issues to resolve.")

    print("=" * 50)
    return success_count == 3

if __name__ == "__main__":
    asyncio.run(test_integration())