#!/usr/bin/env bash
set -e

# ZovsIronClaw Local Installation Script

echo "=== ZovsIronClaw Installer ==="

# 1. Check Prerequisites
command -v node >/dev/null 2>&1 || { echo >&2 "Node.js is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is required but not installed. Aborting."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo >&2 "pnpm is required but not installed. Aborting."; exit 1; }

echo "Prerequisites checked."

# 2. Install Node Dependencies
echo "Installing Node.js dependencies..."
pnpm install

# 3. Setup Python Environment
echo "Setting up Python environment..."
cd gca-service
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created virtual environment in gca-service/.venv"
fi

# Activate venv
source .venv/bin/activate
echo "Installing Python dependencies (this may take a while)..."
pip install -r requirements.txt
cd ..

# 4. Configure Environment
echo "Configuring environment..."
if [ ! -f ".env" ]; then
    SOURCE_ENV=".env.ironclaw.example"
    if [ ! -f "$SOURCE_ENV" ]; then
        SOURCE_ENV=".env.example"
    fi

    if [ -f "$SOURCE_ENV" ]; then
        cp "$SOURCE_ENV" .env
        echo "Created .env from $SOURCE_ENV"

        # Generate a random token
        if command -v openssl >/dev/null 2>&1; then
            TOKEN=$(openssl rand -hex 32)
        else
            TOKEN="change_me_$(date +%s)"
        fi

        # Update token using sed (handling macOS diffs)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/OPENCLAW_GATEWAY_TOKEN=.*/OPENCLAW_GATEWAY_TOKEN=$TOKEN/" .env
            # If the token line didn't exist (e.g. .env.example), append it
            if ! grep -q "OPENCLAW_GATEWAY_TOKEN=" .env; then
                echo "OPENCLAW_GATEWAY_TOKEN=$TOKEN" >> .env
            fi
        else
            sed -i "s/OPENCLAW_GATEWAY_TOKEN=.*/OPENCLAW_GATEWAY_TOKEN=$TOKEN/" .env
            if ! grep -q "OPENCLAW_GATEWAY_TOKEN=" .env; then
                echo "OPENCLAW_GATEWAY_TOKEN=$TOKEN" >> .env
            fi
        fi
        echo "Generated OPENCLAW_GATEWAY_TOKEN in .env"
    else
        echo "Warning: No .env template found. Please create .env manually."
    fi
else
    echo ".env already exists. Skipping generation."
fi

# Ensure assets directory exists
mkdir -p gca-service/gca_assets

echo "=== Installation Complete ==="
echo "Run './scripts/start.sh' (or 'npm run start:local') to start the system."
