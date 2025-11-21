@echo off
echo Starting Jarvis Command Center...

echo Starting Backend (Port 8000)...
start cmd /k "uvicorn server:app --reload"

echo Starting Frontend (Port 5173)...
cd frontend
start cmd /k "npm run dev"

echo Done! Access the UI at http://localhost:5173
