"""
Quick demo of Athena Interactive Chat System
"""
import asyncio
import subprocess
import sys
import time

async def demo_athena():
    """Demonstrate Athena's capabilities"""
    print("ATHENA INTERACTIVE CHAT SYSTEM DEMO")
    print("=" * 50)
    print("This demo shows how to use Athena's interactive chat interface.")
    print()

    print("Key Features:")
    print("- Interactive chat with session management")
    print("- Deep research mode with web search + AI analysis")
    print("- Quick research summaries")
    print("- Conversation history and session persistence")
    print("- Multiple commands and utilities")
    print()

    print("How to run Athena:")
    print("1. Basic command:")
    print("   .venv/Scripts/python.exe main.py")
    print()

    print("2. What you can do in chat:")
    print("   - Ask questions naturally")
    print("   - Use /research <topic> for deep research")
    print("   - Use /quick <topic> for quick summaries")
    print("   - Use /help to see all commands")
    print()

    print("Example session:")
    print("-" * 30)
    print("[abc12345] You: /research machine learning trends")
    print("Athena: [Starting deep research mode...]")
    print("        [Research complete! Generated comprehensive report]")
    print()
    print("[abc12345] You: What are the key applications?")
    print("Athena: Based on my research, the key applications include...")
    print()
    print("[abc12345] You: /quick quantum computing")
    print("Athena: [Quick research summary about quantum computing]")
    print()

    print("Session Management:")
    print("- Each chat gets a unique session ID (e.g., abc12345)")
    print("- Conversations are automatically saved")
    print("- Research reports saved as markdown files")
    print("- Use /load <session_id> to continue previous chats")
    print()

    print("File Structure:")
    print("sessions/")
    print("  abc12345/")
    print("    session.json              # Conversation history")
    print("    research_20240925_143022.md  # Research reports")
    print()

    print("Available Commands:")
    commands = [
        "/help - Show all commands",
        "/research <topic> - Deep research with sources",
        "/quick <topic> - Quick research summary",
        "/sessions - List all sessions",
        "/history - View conversation history",
        "/load <id> - Load previous session",
        "/save - Save current session",
        "/clear - Clear screen",
        "/exit - End session"
    ]

    for cmd in commands:
        print(f"  {cmd}")

    print()
    print("Ready to start Athena? Run:")
    print("  .venv/Scripts/python.exe main.py")
    print()
    print("Your Athena system is fully configured with:")
    print("[OK] Gemini Flash LLM")
    print("[OK] Tavily web search")
    print("[OK] Session persistence")
    print("[OK] Research report generation")
    print("=" * 50)

def main():
    """Run demo"""
    asyncio.run(demo_athena())

if __name__ == "__main__":
    main()