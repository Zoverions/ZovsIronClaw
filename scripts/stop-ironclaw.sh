#!/bin/bash
# Stop script for ZovsIronClaw

set -e

echo "======================================"
echo "Stopping ZovsIronClaw"
echo "======================================"
echo ""

docker-compose -f docker-compose.ironclaw.yml --env-file .env.ironclaw down

echo ""
echo "ZovsIronClaw stopped"
echo ""
