#!/bin/bash
# Start script for ZovsIronClaw
# Starts all services with GCA integration

set -e

echo "======================================"
echo "Starting ZovsIronClaw"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env.ironclaw exists
if [ ! -f .env.ironclaw ]; then
    echo -e "${YELLOW}Error: .env.ironclaw not found${NC}"
    echo "Please run ./scripts/build-ironclaw.sh first"
    exit 1
fi

# Start services
echo "Starting services with docker-compose..."
docker-compose -f docker-compose.ironclaw.yml --env-file .env.ironclaw up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check GCA service health
echo "Checking GCA service..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ GCA service is healthy${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${YELLOW}Warning: GCA service health check failed${NC}"
        echo "Check logs with: docker-compose -f docker-compose.ironclaw.yml logs gca-service"
    fi
    sleep 2
done

echo ""
echo "======================================"
echo "ZovsIronClaw Started"
echo "======================================"
echo ""
echo "Services:"
echo "  - OpenClaw Gateway: http://localhost:18789"
echo "  - GCA Service: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.ironclaw.yml logs -f"
echo "  - Stop services: ./scripts/stop-ironclaw.sh"
echo "  - Test GCA: curl http://localhost:8000/health"
echo "  - Run Arena: curl http://localhost:8000/v1/arena/run?rounds=10"
echo ""
