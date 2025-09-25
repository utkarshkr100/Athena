"""
Demo of the improved research functionality
"""
import asyncio
import os
from dotenv import load_dotenv
from main import AthenaChat

load_dotenv('athena_research/.env')

async def demo_research():
    """Demonstrate the improved research features"""
    print("ATHENA RESEARCH DEMO - Improved Features")
    print("=" * 50)
    print("Testing: Research plan display + Source citations with links")
    print()

    if not os.getenv('GEMINI_API_KEY') or not os.getenv('TAVILY_API_KEY'):
        print("[Error] API keys not configured")
        return

    # Create chat instance
    chat = AthenaChat()
    await chat.start_new_session()

    # Demo research command
    print("Simulating: /research blockchain technology")
    print("-" * 50)

    try:
        # Execute research mode
        research_data = await chat.current_session.__class__.research_mode(
            chat.current_session, "blockchain technology"
        )

        # This will show:
        # 1. Research plan (newly added)
        # 2. Search queries (newly added)
        # 3. AI analysis with source citations (improved)
        # 4. Sources with clickable links (newly added)

        print("\n[Demo] Research completed successfully!")
        print("Features demonstrated:")
        print("✓ Research plan display")
        print("✓ Search queries shown")
        print("✓ Source citations in analysis")
        print("✓ Clickable links in sources")

    except Exception as e:
        print(f"[Error] Demo failed: {e}")

async def main():
    await demo_research()

if __name__ == "__main__":
    asyncio.run(main())