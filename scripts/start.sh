#!/usr/bin/env bash
echo "Starting ZovsIronClaw locally..."
# Use pnpm if available, else npm
if command -v pnpm >/dev/null 2>&1; then
    pnpm run start:local
else
    npm run start:local
fi
