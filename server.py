from dotenv import load_dotenv
load_dotenv()

import os
os.makedirs("logs", exist_ok=True)  # Ensure logs dir exists (required on Render)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jarvis_core.orchestrator import Orchestrator
import json
import asyncio
import logging
import os

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Jarvis Command Center API")

# CORS — allow all origins (same-origin in prod, localhost in dev)
ALLOWED_ORIGINS = os.getenv("JARVIS_FRONTEND_URL", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = Orchestrator()

# Constants
MAX_MESSAGE_LENGTH = 10000  # 10KB limit for messages
MAX_COMMAND_LENGTH = 500

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0"}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with input validation."""
    client_id = id(websocket)
    await websocket.accept()
    logging.info(f"Client {client_id} connected")
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            
            # Validate message size
            if len(data) > MAX_MESSAGE_LENGTH:
                logging.warning(f"Client {client_id} sent oversized message ({len(data)} bytes)")
                await websocket.send_json({
                    "type": "error",
                    "text": "Message too long. Please keep commands under 500 characters.",
                    "agent": "System"
                })
                continue
            
            # Sanitize and validate input
            command = data.strip()
            
            if not command:
                await websocket.send_json({
                    "type": "error",
                    "text": "Empty command received.",
                    "agent": "System"
                })
                continue
            
            if len(command) > MAX_COMMAND_LENGTH:
                logging.warning(f"Client {client_id} sent long command: {len(command)} chars")
                command = command[:MAX_COMMAND_LENGTH]
            
            logging.info(f"Client {client_id} command: {command[:100]}")
            
            try:
                # Process command using route_command
                response = orchestrator.route_command(command)
                
                # Send response back
                await websocket.send_json({
                    "type": "response",
                    "text": response,
                    "agent": orchestrator.state.active_agent or "System"
                })
                
                logging.info(f"Client {client_id} response sent via {orchestrator.state.active_agent}")
                
            except Exception as e:
                logging.error(f"Error processing command from client {client_id}: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "text": "An error occurred processing your command.",
                    "agent": "System"
                })
            
    except WebSocketDisconnect:
        logging.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logging.error(f"Unexpected error with client {client_id}: {str(e)}")
        try:
            await websocket.close()
        except:
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
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)
else:
    @app.get("/")
    async def root():
        return {"message": "Jarvis Backend is Running", "status": "healthy", "version": "2.0"}
