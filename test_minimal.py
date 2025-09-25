"""
Minimal test of Gemini Flash integration
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project path to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv("athena_research/.env")

async def test_gemini_direct():
    """Test Gemini Flash directly"""
    print("Testing Gemini Flash API directly...")

    try:
        import google.generativeai as genai

        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY not found!")
            return False

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Create model and test
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async("What are 3 benefits of AI? Keep it very brief.")

        print("SUCCESS: Gemini Flash API working!")
        print(f"Response: {response.text}")
        return True

    except Exception as e:
        print(f"ERROR: Gemini direct test failed: {e}")
        return False

async def test_athena_llm_client():
    """Test Athena LLM client directly"""
    print("\nTesting Athena LLM Client...")

    try:
        # Import just the client components we need
        import sys
        import os

        # Add the athena_research path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'athena_research'))

        # Import config first
        from config.settings import settings
        print(f"Config loaded: Provider={settings.llm_provider}, Model={settings.planning_model}")

        # Import and test LLM client
        from utils.llm_client import GeminiClient

        client = GeminiClient()
        messages = [
            {"role": "user", "content": "Say 'Hello from Gemini in Athena!' if working correctly"}
        ]

        response = await client.generate_response(messages, temperature=0.1, max_tokens=50)
        print("SUCCESS: Athena LLM client working!")
        print(f"Response: {response}")
        return True

    except Exception as e:
        print(f"ERROR: Athena LLM client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_planning_agent_direct():
    """Test planning agent with direct imports"""
    print("\nTesting Planning Agent...")

    try:
        import sys
        import os

        # Add the athena_research path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'athena_research'))

        from agents.planning.planning_agent import PlanningAgent

        agent = PlanningAgent()
        print(f"Planning agent created with model: {agent.model}")

        # Test with simple input
        input_data = {
            "topic": "Benefits of AI",
            "template": "brief",
            "requirements": "List 3 key benefits"
        }

        result = await agent.process(input_data)

        if result.success:
            print("SUCCESS: Planning Agent working!")
            plan = result.data
            print(f"Topic: {plan['topic']}")
            print(f"Sections: {len(plan['sections'])}")
            for i, section in enumerate(plan['sections'][:2], 1):
                print(f"  {i}. {section['title']}")
            return True
        else:
            print(f"ERROR: Planning failed: {result.error}")
            return False

    except Exception as e:
        print(f"ERROR: Planning agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run minimal tests"""
    print("MINIMAL GEMINI INTEGRATION TEST")
    print("=" * 50)

    # Environment check
    llm_provider = os.getenv('LLM_PROVIDER', 'not set')
    api_key = os.getenv('GEMINI_API_KEY', '')
    print(f"LLM Provider: {llm_provider}")
    print(f"Gemini API Key: {'***' + api_key[-4:] if api_key else 'NOT SET'}")
    print()

    # Run tests
    direct_ok = await test_gemini_direct()
    client_ok = await test_athena_llm_client()
    agent_ok = await test_planning_agent_direct()

    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"   Gemini Direct:    {'PASS' if direct_ok else 'FAIL'}")
    print(f"   Athena Client:    {'PASS' if client_ok else 'FAIL'}")
    print(f"   Planning Agent:   {'PASS' if agent_ok else 'FAIL'}")
    print("=" * 50)

    if all([direct_ok, client_ok, agent_ok]):
        print("🎉 SUCCESS: Your Gemini Flash integration is working perfectly!")
        print("You can now use Athena with Gemini Flash as your LLM provider.")
    else:
        print("⚠️  Some components need attention. Check errors above.")

if __name__ == "__main__":
    asyncio.run(main())