from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from jarvis_core.orchestrator import Orchestrator
import json
import asyncio

app = FastAPI(title="Jarvis Command Center API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = Orchestrator()

@app.get("/")
async def root():
    return {"message": "Jarvis Backend is Running"}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            print(f"Received: {data}")
            
            # Process command using route_command (not process_command)
            response = orchestrator.route_command(data)
            
            # Send response back
            await websocket.send_json({
                "type": "response",
                "text": response,
                "agent": orchestrator.state.active_agent or "System"
            })
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
