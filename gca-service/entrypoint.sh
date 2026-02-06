#!/bin/bash
set -e

# Ensure the assets directory exists
mkdir -p /app/gca_assets

# Check if universal_basis.pt exists in the volume
if [ ! -f /app/gca_assets/universal_basis.pt ]; then
    echo "[Entrypoint] Basis vectors not found in volume. Copying from build..."
    if [ -f /app/gca_assets_build/universal_basis.pt ]; then
        cp -r /app/gca_assets_build/* /app/gca_assets/
        echo "[Entrypoint] Assets initialized."
    else
        echo "[Entrypoint] Warning: Build assets not found. Generating now..."
        python init_system.py
    fi
else
    echo "[Entrypoint] Assets found in volume."
fi

# Execute the main command
exec "$@"
