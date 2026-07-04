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
import uuid

# Log to stdout so Render can display it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Jarvis Command Center API")

# ── CORS ─────────────────────────────────────────────────────────────────────
# Fix: removed allow_credentials=True (incompatible with wildcard origins).
# Origins are read from ALLOWED_ORIGINS env var (comma-separated) so production
# deployments can lock this down without code changes.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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

    Query param: ?session_id=<uuid>  (optional; generated if absent)
    """
    client_id = id(websocket)

    # ── Session ID ────────────────────────────────────────────────────────────
    session_id = websocket.query_params.get("session_id") or str(uuid.uuid4())

    await websocket.accept()
    logging.info(f"Client {client_id} connected (session={session_id})")

    # Send session ID back so the frontend can persist it
    await websocket.send_json({"type": "session", "session_id": session_id})

    # ── Per-connection orchestrator (isolated history per user) ───────────────
    try:
        orchestrator = Orchestrator(session_id=session_id)
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
                # Detect whether the active agent supports streaming
                # (routing decision is needed first, so we call route_command
                # which now returns either a complete response or a generator)
                loop = asyncio.get_event_loop()

                # Check if streaming is available for this command
                routing_info = await loop.run_in_executor(
                    _thread_pool,
                    orchestrator.get_routing_decision,
                    command,
                )

                agent_name = routing_info.get("agent", "KnowledgeAgent")
                orchestrator.state.active_agent = agent_name

                if agent_name in ("KnowledgeAgent", "WebAgent"):
                    # ── Streaming path ────────────────────────────────────────
                    chunk_queue: asyncio.Queue = asyncio.Queue()

                    def stream_worker():
                        """Runs in thread pool; pushes chunks onto the async queue."""
                        try:
                            for chunk in orchestrator.stream_agent(command, routing_info):
                                loop.call_soon_threadsafe(chunk_queue.put_nowait, ("chunk", chunk))
                        except Exception as exc:
                            loop.call_soon_threadsafe(chunk_queue.put_nowait, ("error", str(exc)))
                        finally:
                            loop.call_soon_threadsafe(chunk_queue.put_nowait, ("done", None))

                    future = loop.run_in_executor(_thread_pool, stream_worker)

                    while True:
                        kind, payload = await chunk_queue.get()
                        if kind == "chunk":
                            await websocket.send_json({"type": "chunk", "text": payload, "agent": agent_name})
                        elif kind == "error":
                            await websocket.send_json({"type": "error", "text": payload, "agent": "System"})
                            break
                        elif kind == "done":
                            await websocket.send_json({"type": "done", "agent": agent_name})
                            break

                    await future  # propagate any thread exception

                else:
                    # ── Non-streaming path (MediaAgent, SystemAgent) ──────────
                    response = await loop.run_in_executor(
                        _thread_pool,
                        orchestrator.run_agent,
                        command,
                        routing_info,
                    )
                    await websocket.send_json({
                        "type": "response",
                        "text": response,
                        "agent": agent_name,
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


# ── Fix 1: static mount and catch-all MUST be above the __main__ guard ───────
# When the app is started via `python server.py`, uvicorn.run() blocks, so
# anything after it is never executed.  Moving these here ensures they're
# registered regardless of how the module is loaded.
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


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("JARVIS_HOST", "0.0.0.0")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    logging.info(f"Starting Jarvis API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
