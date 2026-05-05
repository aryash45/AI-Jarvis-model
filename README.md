# 🤖 Jarvis 2.0 - Advanced Contextual AI Assistant

**Jarvis 2.0** is a sophisticated, highly contextual AI assistant engineered for seamless, natural conversations and autonomous task execution. Evolving into a powerful web application, Jarvis now features a robust, low-latency multi-LLM architecture utilizing **Groq** and **OpenRouter**, integrated real-time **DuckDuckGo** web search, and deep conversational memory. 

Whether deployed locally for system automation or hosted in the cloud (Render-ready) with its premium, ChatGPT-inspired dark mode UI, Jarvis provides lightning-fast, highly accurate responses and an unparalleled user experience.




<br/>

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61dafb)](https://react.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-AI-orange)](https://langchain.com/)

---

## 💻 Tech Stack

- **Frontend:** React, Vite, TailwindCSS (Glassmorphic dark-mode UI)
- **Backend:** Python, FastAPI, WebSockets (Real-time bidirectional streaming)
- **AI/ML:** LangChain, Groq API (Llama-3.3, Mixtral), OpenRouter API, DuckDuckGo Search
- **Deployment:** Render (Cloud), Local execution (Windows OS Automation)

---

## 🌟 Key Features

### 🧠 **Conversational Intelligence & Memory**
- **Deep Contextual Awareness:** Maintains conversation history to understand follow-up questions intuitively.
- **Query Contextualization:** Dynamically rewrites questions based on past context for highly accurate web searches.
- **Natural Persona:** Responds in an articulate, human-like manner without rigid robotic formatting.

### ⚡ **Multi-LLM Architecture**
- **Primary Groq Integration:** Ultra-low latency inference using models like `Llama-3.3-70b-versatile`, `Mixtral-8x7b`, and `Gemma2-9b`.
- **OpenRouter Fallback:** Automatic failover to OpenRouter's free tier (Llama 3.3, Nemotron 120B) ensures maximum uptime and reliability when primary providers rate-limit.

### 🔍 **Live Search & Specialized Agents**
- **KnowledgeAgent:** Synthesizes live internet data using LangChain and DuckDuckGo search integration.
- **MediaAgent:** Dynamic YouTube music/video playback with genre support.
- **SystemAgent:** Volume control, application launching, and media keys (for local Windows deployments).

### 🎨 **Premium ChatGPT-Style UI**
- **Immersive Design:** Modern, glassmorphic dark-mode interface.
- **Typewriter Effect:** Dynamic text generation mimicking natural typing.
- **WebSocket Communication:** Real-time bidirectional streaming between the React frontend and FastAPI backend.

### 🚀 **Production-Ready Deployment**
- **Unified Server:** A single `server.py` FastAPI instance serves both the API/WebSockets and the compiled React SPA.
- **Non-Blocking Execution:** Uses ThreadPoolExecutors for LLM calls so the event loop is never blocked, allowing multiple clients simultaneously.
- **Render Compatible:** Out-of-the-box support for Render deployments with automatic log directory provisioning.

---

## 💡 Technical Achievements

- **Thread-Pool Concurrency:** Designed a non-blocking WebSocket backend using `concurrent.futures.ThreadPoolExecutor` to handle intensive LLM inference without freezing the FastAPI event loop, enabling multi-tenant usage.
- **Resilient AI Pipeline:** Implemented an automatic failover mechanism routing requests to OpenRouter models if Groq encounters rate-limiting (HTTP 429), ensuring maximum conversational uptime.
- **Stateful Conversational Memory:** Built a custom context-sliding window that feeds the last N messages back into the LLM, coupled with an AI-driven query contextualization pre-step for highly accurate web scraping.
- **Unified Full-Stack Deployment:** Engineered a single FastAPI instance capable of serving both the compiled React Single Page Application (SPA) static files and WebSocket APIs concurrently, dramatically simplifying CI/CD and deployment on Render.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend building)
- API Keys: [Groq](https://console.groq.com/) (Required) and [OpenRouter](https://openrouter.ai/) (Optional Fallback)

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

3. **Install and build frontend**

```bash
cd frontend
npm install
npm run build
cd ..
```

4. **Environment Configuration**

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
JARVIS_HOST=0.0.0.0
JARVIS_PORT=8000
```

### Running the System

#### Option 1: Full Unified Server (Production/Local)

```bash
python server.py
```
*Then open `http://localhost:8000` in your browser. The single server hosts both the React UI and the WebSocket API.*

#### Option 2: Development Mode

You can run the backend and frontend separately for hot-reloading:
- Backend: `uvicorn server:app --reload`
- Frontend: `cd frontend && npm run dev`

---

## 🏗️ Architecture

```text
AI-Jarvis-model/
├── jarvis_core/
│   ├── orchestrator.py      # Core router and conversational state manager
│   ├── agents/
│   │   ├── knowledge_agent.py   # LangChain + Groq + DuckDuckGo + Memory
│   │   ├── media_agent.py       # YouTube playback controls
│   │   ├── system_agent.py      # OS automation (Windows)
│   │   └── web_agent.py         # Fallback web tasks
│   └── tools/
│       ├── browser_tools.py     # URL handling
│       ├── speech_tools.py      # Voice I/O handling
│       └── system_tools.py      # System apps and volume logic
├── frontend/                # React SPA (Vite + TailwindCSS)
└── server.py                # Unified FastAPI Backend & Static File Server
```

---

## 📖 Usage Examples

### Voice & Text Commands

**Knowledge & Context:**
- *User:* "Who is the CEO of Tesla?"
- *Jarvis:* "Elon Musk is the CEO of Tesla."
- *User:* "How old is he?" *(Jarvis seamlessly understands 'he' refers to Elon Musk using conversation memory)*

**Media Control:**
- "Play some rock music"
- "Play Shape of You on YouTube"

**System Control (Local Run Only):**
- "Mute the system volume"
- "Open calculator"

---

## 🛠️ Configuration & Security

- **Multi-Tenant WebSockets:** Each WebSocket connection spawns an isolated Orchestrator, ensuring user conversation histories never overlap.
- **Allowed Apps:** You can customize the whitelist of applications Jarvis is permitted to open by modifying `ALLOWED_APPS` in `jarvis_core/tools/system_tools.py`.

For more details on network binding and CORS, refer to the [SECURITY.md](docs/SECURITY.md).

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
