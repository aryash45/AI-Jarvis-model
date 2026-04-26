# Jarvis Project Structure

```
AI-Jarvis-model/
├── docs/                           # Documentation
│   ├── SECURITY.md                 # Security guidelines
│   └── USER_GUIDE.md               # User guide
│
├── jarvis_core/                    # Core application
│   ├── __init__.py
│   ├── orchestrator.py             # Main command router (Langchain)
│   ├── state.py                    # Application state
│   ├── ollama_manager.py           # Local LLM integration using Ollama
│   │
│   ├── agents/                     # Specialized agents
│   │   ├── __init__.py
│   │   ├── knowledge_agent.py      # Q&A with web search (Langchain ReAct)
│   │   ├── media_agent.py          # YouTube playback
│   │   ├── system_agent.py         # System control
│   │   └── web_agent.py            # Web search fallback
│   │
│   └── tools/                      # Utility tools
│       ├── __init__.py
│       ├── browser_tools.py        # Web scraping & search
│       ├── speech_tools.py         # Voice I/O
│       └── system_tools.py         # OS automation
│
├── frontend/                       # React UI
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── tests/                          # Test files
│   └── test_jarvis.py              # Integration tests
│
├── logs/                           # Log files (gitignored)
│   ├── jarvis_security.log
│   └── jarvis_api.log
│
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
├── README.md                       # Project overview
├── requirements.txt                # Python dependencies
├── main.py                         # CLI entry point
├── server.py                       # Web server entry
└── start_jarvis.bat                # Windows launcher

```

## Clean Structure Benefits

✅ **Organized by Purpose**: docs/, tests/, logs/ separated  
✅ **Clear Hierarchy**: Core logic in `jarvis_core/`  
✅ **Agentic Frameworks**: Powered by Langchain and local LLMs (Ollama)  
✅ **Professional**: Follows Python best practices  
✅ **Scalable**: Easy to add new agents/tools
