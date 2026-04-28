from dotenv import load_dotenv
load_dotenv()

import os
os.makedirs("logs", exist_ok=True)  # Ensure logs dir exists (required on Render)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jarvis_core.orchestrator import Orchestrator
import asyncio
import logging
import concurrent.futures

# Log to stdout so Render can display it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Jarvis Command Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running blocking LLM calls without freezing the event loop
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Constants
MAX_MESSAGE_LENGTH = 10000
MAX_COMMAND_LENGTH = 500
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0"}


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint — one Orchestrator per connection so users
    don't share conversation history, and LLM calls run in a thread
    pool so they never block other connections.
    """
    client_id = id(websocket)
    await websocket.accept()
    logging.info(f"Client {client_id} connected")

    # ── Per-connection orchestrator (isolated history per user) ──────────────
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        logging.error(f"Failed to create Orchestrator for client {client_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "text": "Server initialisation failed. Please try again.",
            "agent": "System"
        })
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()

            # Size guard
            if len(data) > MAX_MESSAGE_LENGTH:
                await websocket.send_json({
                    "type": "error",
                    "text": "Message too long. Please keep commands under 500 characters.",
                    "agent": "System"
                })
                continue

            command = data.strip()
            if not command:
                continue

            if len(command) > MAX_COMMAND_LENGTH:
                command = command[:MAX_COMMAND_LENGTH]

            logging.info(f"Client {client_id} → {command[:80]}")

            try:
                # ── Run blocking LLM call in thread pool ─────────────────────
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    _thread_pool,
                    orchestrator.route_command,
                    command
                )

                await websocket.send_json({
                    "type": "response",
                    "text": response,
                    "agent": orchestrator.state.active_agent or "System"
                })
                logging.info(f"Client {client_id} ← sent via {orchestrator.state.active_agent}")

            except Exception as e:
                logging.error(f"Error for client {client_id}: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "text": "An error occurred processing your command. Please try again.",
                    "agent": "System"
                })

    except WebSocketDisconnect:
        logging.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logging.error(f"Unexpected WS error for client {client_id}: {e}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("JARVIS_HOST", "0.0.0.0")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    logging.info(f"Starting Jarvis API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


# Mount React frontend — must be AFTER all API routes
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        """Serve React SPA — return index.html for all non-API routes."""
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Jarvis Backend is Running", "status": "healthy", "version": "2.0"}
