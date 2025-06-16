#!/bin/bash

# Local development without Docker
# Usage: ./scripts/local-dev.sh

set -e

# Colors
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/app.py" ] || [ ! -f "frontend/package.json" ]; then
    echo "Please run this script from the project root directory"
    exit 1
fi

# Setup backend
log "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    log "Creating Python virtual environment..."
    python3 -m venv venv
fi

log "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

log "Initializing database..."
python app.py init

log "Starting backend server in background..."
python app.py run &
BACKEND_PID=$!
cd ..

# Setup frontend
log "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    log "Installing npm dependencies..."
    npm install
fi

log "Starting frontend development server..."
# Use the development-specific script
npm run dev &
FRONTEND_PID=$!
cd ..

# Function to cleanup background processes
cleanup() {
    log "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

log "Development servers started!"
log "Backend: http://localhost:5000"
log "Frontend: http://localhost:3000"
log ""
warn "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
wait