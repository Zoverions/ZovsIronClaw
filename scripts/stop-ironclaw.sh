#!/bin/bash
# Stop script for ZovsIronClaw (Hybrid Mode)

echo "======================================"
echo "Stopping ZovsIronClaw"
echo "======================================"

# Stop local Gateway
if [ -f .gateway.pid ]; then
    PID=$(cat .gateway.pid)
    echo "Stopping Gateway (PID $PID)..."
    kill $PID 2>/dev/null || true
    rm .gateway.pid
fi

# Stop any lingering node processes related to gateway
echo "Cleaning up node processes..."
pkill -f "openclaw gateway" || true

# Stop Docker services (GCA Brain)
echo "Stopping Docker services..."
docker-compose -f docker-compose.ironclaw.yml down

echo "======================================"
echo "ZovsIronClaw Stopped"
echo "======================================"
