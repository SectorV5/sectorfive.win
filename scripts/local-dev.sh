#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

echo -e "${BLUE}Sectorfive Website - Local Development Setup${NC}"
echo "=============================================="

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}Starting MongoDB...${NC}"
    sudo systemctl start mongod
fi

# Setup Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd "$ROOT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cd backend
pip install -r requirements.txt

# Start backend in background
echo -e "${YELLOW}Starting backend server...${NC}"
cd "$ROOT_DIR/backend"
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd "$ROOT_DIR/frontend"
yarn install

# Start frontend
echo -e "${YELLOW}Starting frontend server...${NC}"
REACT_APP_BACKEND_URL=http://localhost:8001/api yarn start &
FRONTEND_PID=$!

echo -e "${GREEN}Development servers started!${NC}"
echo ""
echo -e "${BLUE}Your website is now available at:${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}  Backend API: http://localhost:8001${NC}"
echo -e "${GREEN}  MongoDB: localhost:27017${NC}"
echo ""
echo -e "${YELLOW}Default admin credentials:${NC}"
echo -e "  Username: admin"
echo -e "  Password: admin"
echo -e "  ${RED}(You will be asked to change these on first login)${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Handle Ctrl+C
trap cleanup SIGINT SIGTERM

echo -e "${YELLOW}Press Ctrl+C to stop the development servers${NC}"

# Wait for processes
wait