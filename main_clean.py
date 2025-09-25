"""
Athena AI Research System - Interactive Chat Interface
Main entry point for conversational research with session management
"""
import asyncio
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from tavily import TavilyClient

# Load environment variables
load_dotenv('athena_research/.env')

class AthenaSession:
    """Manages individual chat sessions with conversation history"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.conversation_history: List[Dict] = []
        self.research_history: List[Dict] = []
        self.session_dir = Path(f"sessions/{self.session_id}")
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Configure AI services
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.search_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        print(f"[Athena] Session {self.session_id} initialized")
        print(f"[Data] Session saved to: {self.session_dir}")

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'content': content,
            'metadata': metadata or {}
        }
        self.conversation_history.append(message)
        self.save_session()

    def save_session(self):
        """Save session data to file"""
        session_data = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'conversation_history': self.conversation_history,
            'research_history': self.research_history
        }

        with open(self.session_dir / 'session.json', 'w') as f:
            json.dump(session_data, f, indent=2)

    @classmethod
    def load_session(cls, session_id: str) -> 'AthenaSession':
        """Load existing session"""
        session_dir = Path(f"sessions/{session_id}")
        if not (session_dir / 'session.json').exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_dir / 'session.json', 'r') as f:
            data = json.load(f)

        session = cls(session_id)
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.conversation_history = data.get('conversation_history', [])
        session.research_history = data.get('research_history', [])

        print(f"[Load] Session {session_id} loaded with {len(session.conversation_history)} messages")
        return session

    def get_conversation_context(self, limit: int = 10) -> str:
        """Get recent conversation context for AI"""
        recent_messages = self.conversation_history[-limit:]
        context = []

        for msg in recent_messages:
            if msg['role'] == 'user':
                context.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                context.append(f"Athena: {msg['content']}")

        return "\n".join(context)

class AthenaChat:
    """Main chat interface for Athena AI Research System"""

    def __init__(self):
        self.current_session: Optional[AthenaSession] = None
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)

    async def start_new_session(self) -> AthenaSession:
        """Start a new chat session"""
        self.current_session = AthenaSession()

        welcome_msg = """
ATHENA AI RESEARCH SYSTEM

I'm your AI research assistant powered by:
- Gemini Flash for intelligent analysis
- Tavily for real-time web search
- Session memory for continuous conversations

How can I help you research today?

Commands:
- Type your question normally for research
- '/help' - Show available commands
- '/history' - View conversation history
- '/research <topic>' - Deep research mode
- '/quick <topic>' - Quick research summary
- '/sessions' - List all sessions
- '/load <session_id>' - Load previous session
- '/exit' - End session
"""

        print(welcome_msg)
        self.current_session.add_message('system', welcome_msg.strip())
        return self.current_session

    async def load_session(self, session_id: str) -> AthenaSession:
        """Load existing session"""
        try:
            self.current_session = AthenaSession.load_session(session_id)
            print(f"[OK] Session {session_id} loaded successfully")
            print("[History] Recent conversation:")
            await self.show_history(limit=3)
            return self.current_session
        except FileNotFoundError:
            print(f"[Error] Session {session_id} not found")
            return None

    async def list_sessions(self):
        """List all available sessions"""
        sessions = []
        for session_dir in self.sessions_dir.glob("*/"):
            if (session_dir / "session.json").exists():
                with open(session_dir / "session.json", 'r') as f:
                    data = json.load(f)
                sessions.append({
                    'id': data['session_id'],
                    'created': data['created_at'][:16],
                    'messages': len(data.get('conversation_history', []))
                })

        if sessions:
            print("\n[Sessions] Available Sessions:")
            print("ID       | Created          | Messages")
            print("-" * 40)
            for s in sorted(sessions, key=lambda x: x['created'], reverse=True):
                print(f"{s['id']:<8} | {s['created']:<15} | {s['messages']}")
        else:
            print("[Sessions] No previous sessions found")

    async def show_history(self, limit: int = 10):
        """Show conversation history"""
        if not self.current_session or not self.current_session.conversation_history:
            print("[History] No conversation history yet")
            return

        recent = self.current_session.conversation_history[-limit:]
        print(f"\n[History] Last {len(recent)} messages:")
        print("-" * 50)

        for msg in recent:
            timestamp = msg['timestamp'][:16]
            role = msg['role'].title()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"[{timestamp}] {role}: {content}")

    async def research_mode(self, topic: str) -> Dict:
        """Comprehensive research mode"""
        print(f"\n[Research] Deep Research Mode: {topic}")
        print("=" * 50)

        session = self.current_session

        # Step 1: Generate research plan
        print("[1/4] Generating research plan...")
        plan_prompt = f"""
        Create a focused research plan for: {topic}

        Based on our conversation history:
        {session.get_conversation_context(5)}

        Generate:
        1. 3 specific research questions
        2. Key areas to investigate
        3. Search strategy

        Keep it concise and actionable.
        """

        plan_response = await session.model.generate_content_async(plan_prompt)
        plan = plan_response.text
        print("[OK] Research plan generated")

        # Step 2: Conduct searches
        print("[2/4] Searching for information...")
        search_queries = [
            f"{topic} latest research 2024",
            f"{topic} current applications",
            f"{topic} future trends"
        ]

        all_sources = []
        for query in search_queries:
            try:
                results = session.search_client.search(query, max_results=3)
                all_sources.extend(results['results'])
            except Exception as e:
                print(f"[Warning] Search error for '{query}': {e}")

        print(f"[OK] Found {len(all_sources)} sources")

        # Step 3: AI analysis
        print("[3/4] AI analysis and synthesis...")
        sources_text = ""
        for i, source in enumerate(all_sources[:8], 1):
            sources_text += f"\nSource {i}: {source['title']}\n{source['content'][:400]}...\n"

        analysis_prompt = f"""
        Research Topic: {topic}

        Research Plan:
        {plan}

        Conversation Context:
        {session.get_conversation_context(3)}

        Sources Found:
        {sources_text}

        Create a comprehensive research report with:

        ## Executive Summary
        ## Key Findings
        ## Current Applications
        ## Future Implications
        ## Recommendations

        Make it relevant to our conversation and cite specific sources.
        """

        analysis_response = await session.model.generate_content_async(analysis_prompt)
        analysis = analysis_response.text

        # Step 4: Save and present results
        print("[4/4] Finalizing research...")

        research_data = {
            'timestamp': datetime.now().isoformat(),
            'topic': topic,
            'plan': plan,
            'sources_count': len(all_sources),
            'analysis': analysis,
            'sources': all_sources[:8]
        }

        session.research_history.append(research_data)

        # Save detailed research report
        report_file = session.session_dir / f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Research Report: {topic}\n\n")
            f.write(f"**Session:** {session.session_id}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Research Plan\n{plan}\n\n")
            f.write(f"## Analysis\n{analysis}\n\n")
            f.write(f"## Sources ({len(all_sources[:8])})\n")
            for i, source in enumerate(all_sources[:8], 1):
                f.write(f"{i}. [{source['title']}]({source.get('url', 'N/A')})\n")

        print(f"[OK] Research complete! Report saved to: {report_file}")
        return research_data

    async def quick_research(self, topic: str) -> str:
        """Quick research summary"""
        print(f"[Quick] Quick Research: {topic}")

        session = self.current_session

        # Quick search
        try:
            results = session.search_client.search(f"{topic} overview", max_results=3)
            sources_text = "\n".join([
                f"- {r['title']}: {r['content'][:200]}..."
                for r in results['results']
            ])
        except Exception as e:
            sources_text = f"Search error: {e}"

        # Quick analysis
        prompt = f"""
        Provide a concise summary of: {topic}

        Context from our conversation:
        {session.get_conversation_context(3)}

        Recent sources:
        {sources_text}

        Give a focused 150-word overview covering key points and current status.
        """

        response = await session.model.generate_content_async(prompt)
        return response.text

    async def chat_response(self, user_input: str) -> str:
        """Generate conversational response"""
        session = self.current_session

        # Build context-aware prompt
        prompt = f"""
        You are Athena, an AI research assistant. Respond to the user's message in a helpful, conversational way.

        Recent conversation:
        {session.get_conversation_context(5)}

        User's current message: {user_input}

        Guidelines:
        - Be conversational and helpful
        - If they ask about research topics, offer to do deep research with /research command
        - Reference previous conversation when relevant
        - Keep responses concise but informative
        - Suggest specific next steps when appropriate
        """

        response = await session.model.generate_content_async(prompt)
        return response.text

    async def process_command(self, command: str, args: str = ""):
        """Process special commands"""
        command = command.lower()

        if command == "help":
            help_text = """
[Help] Athena Commands:

Research Commands:
* /research <topic>    - Deep research with sources and analysis
* /quick <topic>       - Quick research summary

Session Commands:
* /sessions            - List all available sessions
* /load <session_id>   - Load a previous session
* /history [limit]     - Show conversation history
* /save               - Manually save current session

Utility Commands:
* /help               - Show this help message
* /clear              - Clear screen (conversation stays saved)
* /exit               - End current session

Examples:
* /research artificial intelligence in healthcare
* /quick quantum computing
* /load ab12cd34
            """
            print(help_text)

        elif command == "sessions":
            await self.list_sessions()

        elif command == "history":
            limit = int(args) if args.isdigit() else 10
            await self.show_history(limit)

        elif command == "load":
            if args:
                await self.load_session(args)
            else:
                print("[Error] Please specify session ID: /load <session_id>")

        elif command == "research":
            if args:
                research_data = await self.research_mode(args)
                self.current_session.add_message('assistant',
                    f"Completed deep research on: {args}",
                    {'type': 'research', 'data': research_data})

                # Show the analysis
                print("\n" + "=" * 60)
                print("[Analysis] RESEARCH ANALYSIS")
                print("=" * 60)
                print(research_data['analysis'])
            else:
                print("[Error] Please specify research topic: /research <topic>")

        elif command == "quick":
            if args:
                summary = await self.quick_research(args)
                print(f"\n[Summary] Quick Research Summary:\n{summary}")
                self.current_session.add_message('assistant', summary,
                    {'type': 'quick_research', 'topic': args})
            else:
                print("[Error] Please specify topic: /quick <topic>")

        elif command == "save":
            self.current_session.save_session()
            print("[OK] Session saved successfully")

        elif command == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"[Athena] Session {self.current_session.session_id}")
            print("Screen cleared. Conversation history preserved.")

        else:
            print(f"[Error] Unknown command: /{command}. Type /help for available commands.")

    async def run(self):
        """Main chat loop"""
        print("ATHENA AI RESEARCH SYSTEM")
        print("=" * 50)

        # Check for existing sessions
        await self.list_sessions()

        # Session selection
        print("\nOptions:")
        print("1. Start new session (press Enter)")
        print("2. Load existing session (type session ID)")

        try:
            choice = input("\n> Your choice: ").strip()
        except EOFError:
            print("\n[Exit] Goodbye!")
            return

        if choice and len(choice) == 8:  # Session ID format
            session = await self.load_session(choice)
            if not session:
                print("Starting new session instead...")
                await self.start_new_session()
        else:
            await self.start_new_session()

        # Main chat loop
        print(f"\n[Chat] Chat started! Session: {self.current_session.session_id}")
        print("Type your message or use commands (type /help for help)")
        print("-" * 50)

        while True:
            try:
                user_input = input(f"\n[{self.current_session.session_id}] You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['/exit', 'quit', 'bye']:
                    print("[Exit] Goodbye! Your session has been saved.")
                    break

                # Add user message to history
                self.current_session.add_message('user', user_input)

                # Process commands or generate response
                if user_input.startswith('/'):
                    parts = user_input[1:].split(' ', 1)
                    command = parts[0]
                    args = parts[1] if len(parts) > 1 else ""
                    await self.process_command(command, args)
                else:
                    # Generate AI response
                    print("Athena: ", end="", flush=True)
                    response = await self.chat_response(user_input)
                    print(response)

                    # Add response to history
                    self.current_session.add_message('assistant', response)

            except KeyboardInterrupt:
                print("\n\n[Pause] Session paused. Type /exit to quit or continue chatting.")
            except EOFError:
                print("\n[Exit] Session ended.")
                break
            except Exception as e:
                print(f"\n[Error] {e}")
                print("Session continues...")

async def main():
    """Entry point"""
    # Check environment setup
    if not os.getenv('GEMINI_API_KEY'):
        print("[Error] GEMINI_API_KEY not found in athena_research/.env")
        return

    if not os.getenv('TAVILY_API_KEY'):
        print("[Error] TAVILY_API_KEY not found in athena_research/.env")
        return

    # Start chat interface
    chat = AthenaChat()
    await chat.run()

if __name__ == "__main__":
    asyncio.run(main())