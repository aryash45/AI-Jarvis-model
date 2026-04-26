# 🤖 Jarvis 2025 - Local Hierarchical Agent System

A modern, modular AI assistant powered by specialized agents for autonomous task execution. Built with local-first architecture for privacy and offline capability.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61dafb)](https://react.dev/)

---

## 🌟 Features

### 🧠 **Intelligent Agent System**

- **KnowledgeAgent**: Quick answers via Wikipedia + Bing search
- **MediaAgent**: Dynamic YouTube music/video playback with genre support
- **SystemAgent**: Volume control, app launching, media keys
- **WebAgent**: General web search and news (fallback)

### 🎨 **Premium Command Center UI**

- Real-time WebSocket communication
- Glassmorphism dark mode design
- Live agent status visualization
- Voice input via browser's Web Speech API

### 🔒 **Privacy-First Architecture**

- Local execution (no cloud dependency)
- Powered by LangChain and Ollama
- Modular design for easy customization
- Bing search integration (no API keys needed)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Windows OS (for system control features)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/AI-Jarvis-model.git
cd AI-Jarvis-model
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies**

```bash
cd frontend
npm install
cd ..
```

### Running the System

#### Option 1: Full System (Recommended)

```bash
./start_jarvis.bat
```

Then open `http://localhost:5173` in your browser.

#### Option 2: Voice-Only Mode

```bash
python main.py
```

#### Option 3: Test Agents

```bash
python test_jarvis.py
```

---

## 📖 Usage Examples

### Voice Commands

**Knowledge Queries:**

- "Who is Elon Musk?"
- "What is quantum computing?"
- "Tell me about the Eiffel Tower"

**Media Control:**

- "Play Shape of You"
- "Play some rock music"
- "Play romantic songs playlist"

**System Control:**

- "Mute volume"
- "Open notepad"
- "Launch calculator"

### Web UI

1. Click the microphone button
2. Speak your command
3. See real-time agent processing
4. Get instant responses

---

## 🏗️ Architecture

```
jarvis_core/
├── orchestrator.py      # Routes commands to agents using Ollama
├── state.py            # Shared agent state
├── ollama_manager.py   # Ollama LLM integration
├── agents/
│   ├── knowledge_agent.py   # Wikipedia + Bing search (Langchain ReAct)
│   ├── media_agent.py       # YouTube playback
│   ├── system_agent.py      # System control
│   └── web_agent.py         # General web (fallback)
└── tools/
    ├── browser_tools.py     # Bing search, URL handling
    ├── speech_tools.py      # Voice I/O
    └── system_tools.py      # OS automation
```

### Agent Routing Logic

```python
Command → Orchestrator (Ollama Manager) → {
    {"agent": "SystemAgent"}     → SystemAgent
    {"agent": "MediaAgent"}      → MediaAgent
    {"agent": "KnowledgeAgent"}  → KnowledgeAgent
    *                            → WebAgent (fallback)
}
```

---

## 🛠️ Configuration

### Search Provider

Currently uses **Bing** (via web scraping). No API key required.

### Voice Settings

Modify `jarvis_core/tools/speech_tools.py`:

```python
# Change voice speed
engine.setProperty('rate', 150)  # Default: 150

# Change voice
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # 0=male, 1=female
```

### Security Configuration

**CORS Settings** (Production):

```bash
# Set allowed frontend origins
export JARVIS_FRONTEND_URL="https://yourdomain.com"

# For multiple origins
export JARVIS_FRONTEND_URL="https://yourdomain.com,https://backup.com"
```

**Application Whitelist**:

Edit `jarvis_core/tools/system_tools.py` to customize allowed applications:

```python
ALLOWED_APPS = {
    "Windows": [
        "notepad", "calc", "chrome", "firefox", # ... add your apps
    ]
}
```

**Network Binding**:

```bash
# Localhost only (most secure)
export JARVIS_HOST="127.0.0.1"

# All interfaces (if needed for network access)
export JARVIS_HOST="0.0.0.0"
```

For more details, see [SECURITY.md](docs/SECURITY.md).

---

## 🧪 Testing

### Run All Tests

```bash
python test_jarvis.py
```

### Test Individual Agents

```python
from jarvis_core.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.route_command("who is Albert Einstein")
print(result)
```

---

## 📦 Dependencies

**Core:**

- `pydantic` - Data validation
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing

**Voice:**

- `speechrecognition` - Speech-to-text
- `pyttsx3` - Text-to-speech

**System:**

- `pyautogui` - System automation

**Web:**

- `wikipedia` - Wikipedia API
- `fastapi` - Backend API
- `uvicorn` - ASGI server

**Frontend:**

- `react` - UI framework
- `vite` - Build tool
- `tailwindcss` - Styling

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by modern agentic AI systems
- Built with privacy and local execution in mind
- Designed for extensibility and customization

---

## 📞 Support

For issues, questions, or suggestions:

- Open an [Issue](https://github.com/yourusername/AI-Jarvis-model/issues)
- Check the [User Guide](docs/USER_GUIDE.md)

---

**Made with ❤️ for the AI community**
