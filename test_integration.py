"""
Test script for Gemini and Tavily integration
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project path to sys.path
sys.path.insert(0, str(Path(__file__).parent))

async def test_gemini():
    """Test Gemini Flash integration"""
    print("🧪 Testing Gemini Flash...")

    try:
        import google.generativeai as genai
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async("What is artificial intelligence? Keep it brief.")

        print("✅ Gemini Flash working!")
        print(f"Response: {response.text[:200]}...")
        return True

    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

async def test_tavily():
    """Test Tavily search integration"""
    print("\n🔍 Testing Tavily Search...")

    try:
        from tavily import TavilyClient
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Get API key
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY not found in environment")
            return False

        # Create client and test search
        client = TavilyClient(api_key=api_key)
        response = client.search("artificial intelligence latest news", max_results=3)

        print("✅ Tavily Search working!")
        print(f"Found {len(response['results'])} results")
        for i, result in enumerate(response['results'][:2], 1):
            print(f"  {i}. {result['title'][:60]}...")
        return True

    except Exception as e:
        print(f"❌ Tavily test failed: {e}")
        return False

async def test_athena_config():
    """Test Athena configuration"""
    print("\n⚙️  Testing Athena Configuration...")

    try:
        from athena_research.config import settings

        print(f"✅ Configuration loaded!")
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   Planning Model: {settings.planning_model}")
        print(f"   Writing Model: {settings.writing_model}")
        print(f"   Research Model: {settings.research_model}")
        print(f"   Has Gemini Key: {'Yes' if settings.gemini_api_key else 'No'}")
        print(f"   Has Tavily Key: {'Yes' if settings.tavily_api_key else 'No'}")
        return True

    except Exception as e:
        print(f"❌ Athena config test failed: {e}")
        return False

async def test_llm_client():
    """Test the LLM client factory"""
    print("\n🤖 Testing LLM Client...")

    try:
        from athena_research.utils.llm_client import LLMClientFactory

        # Create client based on configuration
        client = LLMClientFactory.create_client()
        print(f"✅ LLM Client created: {type(client).__name__}")

        # Test a simple generation
        test_messages = [
            {"role": "user", "content": "Say 'Hello from Gemini!' if you're working correctly."}
        ]

        response = await client.generate_response(test_messages, temperature=0.1, max_tokens=50)
        print(f"✅ LLM Response: {response}")
        return True

    except Exception as e:
        print(f"❌ LLM Client test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 ATHENA INTEGRATION TEST")
    print("=" * 50)

    # Run tests
    gemini_ok = await test_gemini()
    tavily_ok = await test_tavily()
    config_ok = await test_athena_config()
    client_ok = await test_llm_client()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Gemini Flash:     {'✅ PASS' if gemini_ok else '❌ FAIL'}")
    print(f"   Tavily Search:    {'✅ PASS' if tavily_ok else '❌ FAIL'}")
    print(f"   Athena Config:    {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   LLM Client:       {'✅ PASS' if client_ok else '❌ FAIL'}")
    print("=" * 50)

    if all([gemini_ok, tavily_ok, config_ok, client_ok]):
        print("🎉 ALL TESTS PASSED! Your integration is ready!")
    else:
        print("⚠️  Some tests failed. Check your API keys and configuration.")

if __name__ == "__main__":
    asyncio.run(main())