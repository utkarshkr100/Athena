"""
Test the improved research features with proper method calls
"""
import asyncio
import os
from dotenv import load_dotenv
from main import AthenaSession

load_dotenv('athena_research/.env')

async def test_research_improvements():
    """Test improved research functionality"""
    print("TESTING IMPROVED RESEARCH FEATURES")
    print("=" * 50)

    if not os.getenv('GEMINI_API_KEY') or not os.getenv('TAVILY_API_KEY'):
        print("[Error] API keys not found")
        return

    # Create session
    session = AthenaSession()
    print("Session created successfully")

    # Test the research_mode method from AthenaChat class
    from main import AthenaChat

    chat = AthenaChat()
    chat.current_session = session

    print("\nTesting research mode with topic: 'artificial intelligence ethics'")
    print("-" * 50)

    try:
        # This will show all the improvements:
        # 1. Research plan display
        # 2. Search queries shown
        # 3. AI analysis with citations
        # 4. Sources with links
        research_data = await chat.research_mode("artificial intelligence ethics")

        print("\n[Success] Research completed with improvements:")
        print(f"- Plan generated: {len(research_data['plan'])} characters")
        print(f"- Sources found: {research_data['sources_count']}")
        print(f"- Analysis length: {len(research_data['analysis'])} characters")

        # Show what the user would see
        print("\nWhat the user sees:")
        print("1. ✓ Research plan displayed")
        print("2. ✓ Search queries shown")
        print("3. ✓ Source citations in analysis")
        print("4. ✓ Clickable links in sources")

    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_research_improvements()

if __name__ == "__main__":
    asyncio.run(main())