# Athena AI Research System - Interactive Chat

## Quick Start

### 1. Run Athena Interactive Chat
```bash
cd "D:\project agent\Athena"
.venv\Scripts\python.exe main.py
```

### 2. Test Individual Components
```bash
# Test integration
.venv\Scripts\python.exe test_success.py

# View demo
.venv\Scripts\python.exe demo.py
```

## Features

### 🔄 **Session Management**
- **Unique Session IDs**: Each chat gets an ID (e.g., `abc12345`)
- **Persistent History**: Conversations automatically saved
- **Session Loading**: Continue previous chats with `/load <session_id>`
- **Multiple Sessions**: Switch between different research topics

### 🧠 **AI Research Capabilities**
- **Deep Research**: `/research <topic>` - Complete research with sources
- **Quick Summaries**: `/quick <topic>` - Fast overviews
- **Conversational**: Ask follow-up questions naturally
- **Context Aware**: Remembers your conversation

### 💾 **Data Management**
- **Session Files**: `sessions/[session_id]/session.json`
- **Research Reports**: Auto-saved as markdown files
- **Source Tracking**: All sources cited and linked

## Commands

### Research Commands
- `/research <topic>` - Deep research with web search + AI analysis
- `/quick <topic>` - Quick research summary
- `[normal chat]` - Ask questions conversationally

### Session Commands
- `/sessions` - List all available sessions
- `/load <session_id>` - Load a previous session
- `/history [limit]` - Show conversation history
- `/save` - Manually save current session

### Utility Commands
- `/help` - Show all commands
- `/clear` - Clear screen (keeps conversation)
- `/exit` - End current session

## Example Usage

```
ATHENA AI RESEARCH SYSTEM
==================================================

> Your choice: [Enter for new session]

[abc12345] You: /research artificial intelligence in medicine

[Research] Deep Research Mode: artificial intelligence in medicine
[1/4] Generating research plan...
[2/4] Searching for information...
[3/4] AI analysis and synthesis...
[4/4] Finalizing research...

[Analysis] RESEARCH ANALYSIS
============================================================
## Executive Summary
Recent advances in AI for medical diagnosis show significant promise...

[abc12345] You: What about the ethical concerns?

Athena: Based on our research, the main ethical concerns include...

[abc12345] You: /quick quantum computing

[Summary] Quick Research Summary:
Quantum computing leverages quantum mechanics to solve problems...
```

## Configuration

### Environment Variables (`.env`)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### System Requirements
- Python 3.11+
- Virtual environment activated
- Required packages (see `requirements_minimal.txt`)

## File Structure

```
Athena/
├── main.py                    # Interactive chat interface
├── test_success.py           # Integration tests
├── demo.py                   # Usage demonstration
├── requirements_minimal.txt   # Essential dependencies
├── athena_research/
│   ├── .env                  # Configuration
│   ├── config/
│   ├── agents/               # AI agents
│   └── utils/                # LLM clients
└── sessions/                 # Chat sessions
    └── [session_id]/
        ├── session.json      # Conversation history
        └── research_*.md     # Research reports
```

## Technical Details

### Powered By
- **LLM**: Google Gemini Flash
- **Search**: Tavily real-time web search
- **Memory**: JSON-based session persistence

### Key Classes
- `AthenaSession`: Manages individual chat sessions
- `AthenaChat`: Main chat interface and command processing

### Research Process
1. **Planning**: AI generates focused research questions
2. **Search**: Multiple web searches using Tavily
3. **Analysis**: AI synthesizes sources into comprehensive report
4. **Storage**: Results saved as markdown reports

## Troubleshooting

### Common Issues
- **Unicode errors**: Use `main.py` (not `main_clean.py`)
- **API key errors**: Check `.env` file in `athena_research/` directory
- **Package errors**: Run in virtual environment: `.venv\Scripts\python.exe`

### Getting Help
- Type `/help` in chat for command reference
- Check `test_success.py` for component testing
- All sessions auto-save, safe to restart anytime

## Success Indicators
When working correctly, you should see:
- `[Athena] Session [id] initialized`
- `[OK] Research plan generated`
- `[OK] Found N sources`
- Research reports saved to `sessions/[id]/`

Your Athena AI Research System is ready for interactive research!