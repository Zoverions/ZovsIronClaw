#!/usr/bin/env bash
set -e
set -o pipefail

# ZovsIronClaw Local Installation Script

echo "=== ZovsIronClaw Installer ==="

# 1. Check Prerequisites
command -v node >/dev/null 2>&1 || { echo >&2 "Node.js is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is required but not installed. Aborting."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo >&2 "pnpm is required but not installed. Aborting."; exit 1; }

# Check for ffmpeg (Optional but recommended)
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Warning: ffmpeg is not installed. Audio/Video features may fail."
    echo "Please install ffmpeg via your package manager (brew, apt, choco)."
fi

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

        # Update/Append Environment Variables

        # Helper function to append or update env var
        update_env() {
            local key=$1
            local value=$2
            if grep -q "^${key}=" .env; then
                # Variable exists, update it (macOS compatible sed)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                     sed -i '' "s|^${key}=.*|${key}=${value}|" .env
                else
                     sed -i "s|^${key}=.*|${key}=${value}|" .env
                fi
            else
                # Variable missing, append it
                echo "${key}=${value}" >> .env
            fi
        }

        update_env "OPENCLAW_GATEWAY_TOKEN" "$TOKEN"
        # Match src/providers/gca-bridge.ts expectation (GCA_SERVICE_URL)
        update_env "GCA_SERVICE_URL" "http://localhost:8000"
        update_env "ENABLED_EXTENSIONS" "gca-brain,voice-call"

        # Set State Dir to Config Dir (Default to ~/.openclaw if not set)
        # We read OPENCLAW_CONFIG_DIR from .env if it exists, else default
        CONFIG_DIR=$(grep "^OPENCLAW_CONFIG_DIR=" .env | cut -d '=' -f2-)
        if [ -z "$CONFIG_DIR" ]; then
            CONFIG_DIR="$HOME/.openclaw"
        fi
        update_env "OPENCLAW_STATE_DIR" "$CONFIG_DIR"

        echo "Configured .env with local settings."
    else
        echo "Warning: No .env template found. Please create .env manually."
    fi
else
    echo ".env already exists. Skipping generation."

    # Check if critical vars are present, warn if not
    if ! grep -q "GCA_SERVICE_URL=" .env; then
        echo "Warning: GCA_SERVICE_URL is missing in .env. Recommend setting it to http://localhost:8000"
    fi
    if ! grep -q "OPENCLAW_STATE_DIR=" .env; then
        echo "Warning: OPENCLAW_STATE_DIR is missing in .env. Recommend setting it to match OPENCLAW_CONFIG_DIR."
    fi
fi

# Ensure assets directory exists
mkdir -p gca-service/gca_assets

echo "=== Installation Complete ==="
echo "Run './scripts/start.sh' (or 'npm run start:local') to start the system."
