# Jarvis 2025 - User Guide & Test Commands

## 🚀 How to Start

1.  **Start the System**: Double-click `start_jarvis.bat`
2.  **Open Dashboard**: Go to [http://localhost:5173](http://localhost:5173)
3.  **Activate**: Click the **Microphone Icon** on the dashboard to start listening (or type in the terminal if running `main.py`).

---

## 🧪 Test Commands by Agent

### 1. 🕵️ Research Agent (Deep Research)

- "Research the future of Agentic AI."
- "Research the history of the Roman Empire."
- "Research latest trends in renewable energy."
- **What happens**: The agent creates a plan, searches multiple queries, and returns a synthesized summary.

### 2. 🌐 Web Agent (Quick Info)

- "Search for Python tutorials."
- "Search wikipedia for Isaac Newton."
- "Get me the latest news."
- **What happens**: Opens Google/Wikipedia/News directly or reads a summary.

### 3. 🎵 Media Agent (Entertainment)

- "Play Bohemian Rhapsody."
- "Play Despacito."
- **What happens**: Searches your `music.json` library (or YouTube) and plays the song.

### 4. ⚙️ System Agent (Control)

- "Open Google."
- "Open YouTube."
- "Mute volume."
- "Unmute volume."
- "Turn volume up."
- **What happens**: Controls your OS volume or opens applications.

---

## 🛠️ Troubleshooting

- **Microphone not working?** Ensure your browser has permission to access the mic.
- **Backend error?** Check the terminal window running `server.py` for error logs.
