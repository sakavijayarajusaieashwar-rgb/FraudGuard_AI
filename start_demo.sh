#!/bin/bash

echo "=================================================="
echo " Starting FraudGuard AI - Multi-Agent Fraud Engine"
echo "=================================================="

# Function to kill child processes on exit
trap 'kill $(jobs -p)' EXIT

# 1. Start FastAPI Backend
echo "Starting Backend API on http://localhost:8000 ..."
cd backend
source venv/bin/activate
uvicorn app.main:app --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 2. Start Vite React Frontend
echo "Starting Frontend UI on http://localhost:5173 ..."
cd frontend
./node_modules/.bin/vite --port 5173 &
FRONTEND_PID=$!
cd ..

echo "--------------------------------------------------"
echo "FraudGuard AI is live!"
echo "Backend:  http://localhost:8000/api/health"
echo "Frontend: http://localhost:5173"
echo "--------------------------------------------------"
echo "Press Ctrl+C to stop all servers."

wait $BACKEND_PID $FRONTEND_PID
