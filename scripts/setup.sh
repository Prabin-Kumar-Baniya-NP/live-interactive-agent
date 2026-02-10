#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Live Interactive Agent environment...${NC}"

# Check for required tools
echo -e "${GREEN}Checking prerequisites...${NC}"
if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}pnpm is not installed. Please install it first.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}python3 is not installed. Please install it first.${NC}"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    # Try installing poetry via pip if not found
    echo -e "${GREEN}Installing poetry...${NC}"
    python3 -m pip install poetry
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Install Frontend Dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
pnpm install

# Install Backend Dependencies
echo -e "${GREEN}Installing backend dependencies...${NC}"
cd backend
python3 -m poetry install
cd ..

# Install Agent Runtime Dependencies
echo -e "${GREEN}Installing agent-runtime dependencies...${NC}"
cd agent-runtime
python3 -m poetry install
cd ..

# Setup Environment Variables
echo -e "${GREEN}Setting up environment variables...${NC}"
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env"
fi

if [ ! -f agent-runtime/.env ]; then
    cp agent-runtime/.env.example agent-runtime/.env
    echo "Created agent-runtime/.env"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    echo "Created frontend/.env.local"
fi

# Start Docker Services
echo -e "${GREEN}Starting local services...${NC}"
docker compose up -d

echo -e "${GREEN}Setup complete!${NC}"
echo -e "You can run the individual services with:"
echo -e "  Frontend: pnpm dev"
echo -e "  Backend: cd backend && python3 -m poetry run uvicorn main:app --reload"
echo -e "  Agent: cd agent-runtime && python3 -m poetry run python agent.py"
