#!/bin/bash

# AlphaDuel - Quick Start Script
# Usage: ./run.sh [backend|frontend|all]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ___  _       _           ___            _ "
echo " / _ \| |_ __ | |__   __ _|   \ _  _ ___| |"
echo "| (_| | | '_ \| '_ \ / _\` | |) | || / -_) |"
echo " \__,_|_| .__/|_.__/\__,_|___/ \_,_\___|_|"
echo "        |_|                                "
echo -e "${NC}"
echo "🐂 vs 🐻 The On-Chain AI Debate Arena"
echo ""

run_backend() {
    echo -e "${GREEN}Starting Backend...${NC}"
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt -q
    
    # Create .env if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env from env.example...${NC}"
        cp env.example .env
        echo -e "${YELLOW}Please edit backend/.env with your API keys${NC}"
    fi
    
    # Run the server
    echo -e "${GREEN}Backend running at http://localhost:8000${NC}"
    uvicorn app.main:app --reload --port 8000
}

run_frontend() {
    echo -e "${GREEN}Starting Frontend...${NC}"
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Run the development server
    echo -e "${GREEN}Frontend running at http://localhost:3000${NC}"
    npm run dev
}

case "$1" in
    backend)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    all|"")
        echo "Starting both backend and frontend..."
        echo "Run './run.sh backend' and './run.sh frontend' in separate terminals"
        echo ""
        echo "Or use Docker:"
        echo "  docker-compose up"
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

