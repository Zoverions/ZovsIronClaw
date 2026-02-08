#!/bin/bash
# Start script for ZovsIronClaw
# Starts all services with GCA integration
# HYBRID MODE: GCA runs in Docker, Gateway runs locally

set -e

echo "======================================"
echo "Starting ZovsIronClaw (Hybrid Mode)"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env.ironclaw exists
if [ ! -f .env.ironclaw ]; then
    echo -e "${YELLOW}Error: .env.ironclaw not found${NC}"
    echo "Please run ./scripts/build-ironclaw.sh first"
    exit 1
fi

# Load .env variables
export $(grep -v '^#' .env.ironclaw | xargs)

# Check for local dependencies
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required for Hybrid Mode.${NC}"
    exit 1
fi
if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}Error: pnpm is required for Hybrid Mode.${NC}"
    exit 1
fi

# Create logs directory
mkdir -p .logs

# Start GCA Brain (Docker)
echo "Starting GCA Brain with docker-compose..."
docker-compose -f docker-compose.ironclaw.yml --env-file .env.ironclaw up -d gca-service

echo ""
echo "Waiting for GCA Brain to be healthy..."
sleep 5

# Check GCA service health
echo "Checking GCA service..."
GCA_HEALTHY=false
for i in {1..15}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ GCA service is healthy${NC}"
        GCA_HEALTHY=true
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "${YELLOW}Warning: GCA service health check timed out. Proceeding anyway...${NC}"
    fi
    sleep 2
done

# Start OpenClaw Gateway (Local)
echo ""
echo "Starting OpenClaw Gateway (Local)..."

# Ensure dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing local dependencies..."
    pnpm install
fi

# Configure Gateway for GCA
export GCA_API_URL="http://localhost:8000"
export ENABLED_EXTENSIONS="gca-brain,voice-call"
# Use default ~/.openclaw state directory unless overridden

# Run in background
nohup pnpm start -- gateway --allow-unconfigured > .logs/gateway.log 2>&1 &
GATEWAY_PID=$!
echo $GATEWAY_PID > .gateway.pid
echo "Gateway started with PID $GATEWAY_PID"

echo ""
echo "======================================"
echo "ZovsIronClaw Started (Hybrid)"
echo "======================================"
echo ""
echo "Services:"
echo "  - OpenClaw Gateway (Local): http://localhost:18789"
echo "  - GCA Brain (Docker): http://localhost:8000"
echo ""
echo "Logs:"
echo "  - Gateway: tail -f .logs/gateway.log"
echo "  - GCA Brain: docker-compose -f docker-compose.ironclaw.yml logs -f gca-service"
echo ""
echo "To stop: ./scripts/stop-ironclaw.sh"
echo ""
