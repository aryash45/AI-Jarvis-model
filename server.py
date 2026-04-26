from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Secure CORS configuration
# Use environment variable for production, fallback to localhost for development
ALLOWED_ORIGINS = os.getenv("JARVIS_FRONTEND_URL", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = Orchestrator()

# Constants
MAX_MESSAGE_LENGTH = 10000  # 10KB limit for messages
MAX_COMMAND_LENGTH = 500

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Jarvis Backend is Running",
        "status": "healthy",
        "version": "2.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }

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
    
    # Get host and port from environment variables with defaults
    host = os.getenv("JARVIS_HOST", "0.0.0.0")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    
    logging.info(f"Starting Jarvis API server on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port)
