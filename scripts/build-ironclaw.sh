#!/bin/bash
# Build script for ZovsIronClaw
# Builds both OpenClaw and GCA service containers

set -e

echo "======================================"
echo "Building ZovsIronClaw"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.ironclaw exists
if [ ! -f .env.ironclaw ]; then
    echo -e "${YELLOW}Warning: .env.ironclaw not found${NC}"
    echo "Creating from example..."
    cp .env.ironclaw.example .env.ironclaw
    echo -e "${RED}Please edit .env.ironclaw with your API keys before continuing${NC}"
    exit 1
fi

# Check for required API keys
source .env.ironclaw
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo -e "${RED}Error: GEMINI_API_KEY not set in .env.ironclaw${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configuration found${NC}"
echo ""

# Build GCA Service
echo "======================================"
echo "Building GCA Service"
echo "======================================"
cd gca-service
docker build -t ironclaw-gca:latest .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GCA Service built successfully${NC}"
else
    echo -e "${RED}✗ GCA Service build failed${NC}"
    exit 1
fi
cd ..
echo ""

# Build OpenClaw
echo "======================================"
echo "Building OpenClaw"
echo "======================================"
docker build -t openclaw:local .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ OpenClaw built successfully${NC}"
else
    echo -e "${RED}✗ OpenClaw build failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "======================================"
echo "Build Complete"
echo "======================================"
echo ""
echo "Images built:"
echo "  - ironclaw-gca:latest"
echo "  - openclaw:local"
echo ""
echo "To start ZovsIronClaw, run:"
echo "  ./scripts/start-ironclaw.sh"
echo ""
