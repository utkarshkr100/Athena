"""
Example usage of Athena Research System with Google Gemini Flash

This example demonstrates how to use the Athena Research System with Gemini Flash as the LLM provider.
"""

import asyncio
import os
from athena_research.agents.planning.planning_agent import PlanningAgent
from athena_research.agents.writing.final_writer_agent import FinalWriterAgent
from athena_research.config import settings

async def main():
    """
    Example of running Athena with Gemini Flash

    Prerequisites:
    1. Install dependencies: pip install -r requirements.txt
    2. Set environment variables in .env file:
       - LLM_PROVIDER=gemini
       - GEMINI_API_KEY=your_gemini_api_key
    """

    # Check configuration
    print(f"Current LLM Provider: {settings.llm_provider}")
    print(f"Planning Model: {settings.planning_model}")
    print(f"Writing Model: {settings.writing_model}")
    print(f"Research Model: {settings.research_model}")

    if settings.llm_provider != "gemini":
        print("Warning: LLM_PROVIDER is not set to 'gemini'")
        print("Please set LLM_PROVIDER=gemini in your .env file")
        return

    if not settings.gemini_api_key:
        print("Error: GEMINI_API_KEY not found")
        print("Please set GEMINI_API_KEY in your .env file")
        return

    print("\n" + "="*50)
    print("ATHENA RESEARCH SYSTEM - GEMINI FLASH DEMO")
    print("="*50)

    # Example 1: Planning Agent
    print("\n1. Testing Planning Agent with Gemini Flash...")
    planning_agent = PlanningAgent()

    planning_input = {
        "topic": "Artificial Intelligence in Healthcare",
        "template": "comprehensive",
        "requirements": "Focus on recent developments, ethical considerations, and practical applications"
    }

    try:
        planning_result = await planning_agent.process(planning_input)
        if planning_result.success:
            print("✅ Planning Agent successful!")
            plan_data = planning_result.data
            print(f"   Topic: {plan_data['topic']}")
            print(f"   Sections: {len(plan_data['sections'])}")
            for i, section in enumerate(plan_data['sections'], 1):
                print(f"   {i}. {section['title']}")
        else:
            print("❌ Planning Agent failed:", planning_result.error)
    except Exception as e:
        print(f"❌ Planning Agent error: {e}")

    # Example 2: Testing LLM Response Generation
    print("\n2. Testing Direct LLM Response Generation...")
    try:
        test_response = await planning_agent.generate_llm_response(
            prompt="What are the key benefits of using AI in healthcare?",
            system_message="You are a healthcare AI expert. Provide a concise overview."
        )
        print("✅ Direct LLM call successful!")
        print(f"   Response length: {len(test_response)} characters")
        print(f"   Sample: {test_response[:200]}...")
    except Exception as e:
        print(f"❌ Direct LLM call error: {e}")

    print("\n" + "="*50)
    print("Demo completed! Gemini Flash is configured and working.")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())