"""
Direct test of Gemini Flash with Athena agents
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

async def test_gemini_agent():
    """Test PlanningAgent with Gemini Flash"""
    print("Testing Gemini Flash with Planning Agent...")

    try:
        from athena_research.agents.planning.planning_agent import PlanningAgent

        # Create planning agent
        agent = PlanningAgent()
        print(f"Agent created with model: {agent.model}")

        # Test agent processing
        planning_input = {
            "topic": "Machine Learning in Healthcare",
            "template": "comprehensive",
            "requirements": "Focus on current applications and future potential"
        }

        result = await agent.process(planning_input)

        if result.success:
            print("SUCCESS: Planning Agent with Gemini Flash working!")
            plan = result.data
            print(f"Generated plan for: {plan['topic']}")
            print(f"Number of sections: {len(plan['sections'])}")

            for i, section in enumerate(plan['sections'], 1):
                print(f"  {i}. {section['title']}")
                print(f"     Queries: {len(section['queries'])} planned")

            return True
        else:
            print(f"ERROR: Planning failed: {result.error}")
            return False

    except Exception as e:
        print(f"ERROR: Planning agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_llm():
    """Test direct LLM client"""
    print("\nTesting direct LLM client...")

    try:
        from athena_research.utils.llm_client import GeminiClient

        # Create Gemini client directly
        client = GeminiClient()

        # Test simple generation
        messages = [
            {"role": "user", "content": "List 3 benefits of AI in healthcare. Keep it very brief."}
        ]

        response = await client.generate_response(messages, temperature=0.1)
        print("SUCCESS: Direct Gemini client working!")
        print(f"Response: {response}")
        return True

    except Exception as e:
        print(f"ERROR: Direct LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run Gemini-focused tests"""
    print("GEMINI FLASH INTEGRATION TEST")
    print("=" * 50)

    # Check environment
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found!")
        return

    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'not set')}")
    print(f"Gemini API Key: {'***' + (os.getenv('GEMINI_API_KEY') or '')[-4:]}")

    # Run tests
    agent_ok = await test_gemini_agent()
    direct_ok = await test_direct_llm()

    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"   Planning Agent:   {'PASS' if agent_ok else 'FAIL'}")
    print(f"   Direct Client:    {'PASS' if direct_ok else 'FAIL'}")
    print("=" * 50)

    if agent_ok and direct_ok:
        print("SUCCESS: Gemini Flash fully integrated with Athena!")
        print("You can now use Athena with Gemini Flash as your LLM provider.")
    else:
        print("Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())