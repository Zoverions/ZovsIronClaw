#!/bin/bash

# ZovsIronClaw Interactive Setup Script
# This script helps configure the environment variables for ZovsIronClaw.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   ZovsIronClaw Interactive Setup      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ENV_FILE=".env"
EXAMPLE_ENV=".env.example"

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}A .env file already exists.${NC}"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Keeping existing .env file. Exiting setup.${NC}"
        exit 0
    fi
fi

# Create .env from example if it exists, otherwise start fresh
if [ -f "$EXAMPLE_ENV" ]; then
    echo -e "${GREEN}Found .env.example, using it as a template...${NC}"
    cp "$EXAMPLE_ENV" "$ENV_FILE"
else
    echo -e "${YELLOW}No .env.example found. Creating a new .env file.${NC}"
    touch "$ENV_FILE"
fi

echo ""
echo -e "${BLUE}Please provide the following configuration values:${NC}"
echo "(Press Enter to leave blank if optional or to keep default if editing)"

# Function to prompt and update/append to .env
prompt_and_save() {
    local key=$1
    local description=$2
    local required=$3

    local current_value=""
    if grep -q "^${key}=" "$ENV_FILE"; then
        current_value=$(grep "^${key}=" "$ENV_FILE" | cut -d '=' -f2-)
    fi

    echo ""
    echo -e "${YELLOW}${description}${NC}"
    if [ -n "$current_value" ]; then
        echo -e "Current value: ${GREEN}${current_value}${NC}"
    fi

    read -p "${key}: " user_input

    if [ -n "$user_input" ]; then
        # If key exists, replace it
        if grep -q "^${key}=" "$ENV_FILE"; then
            # Escape special characters for sed
            escaped_input=$(printf '%s\n' "$user_input" | sed -e 's/[\/&]/\\&/g')
            sed -i "s/^${key}=.*/${key}=${escaped_input}/" "$ENV_FILE"
        else
            echo "${key}=${user_input}" >> "$ENV_FILE"
        fi
    elif [ -z "$current_value" ] && [ "$required" = "true" ]; then
        echo -e "${RED}Error: ${key} is required!${NC}"
        prompt_and_save "$key" "$description" "$required"
    fi
}

# --- Configuration Prompts ---

# Gateway Token
prompt_and_save "OPENCLAW_GATEWAY_TOKEN" "Enter a secure token for the OpenClaw Gateway (Required):" "true"

# AI Service Keys
prompt_and_save "GEMINI_API_KEY" "Enter your Gemini API Key (Required for GCA):" "false"
prompt_and_save "OPENAI_API_KEY" "Enter your OpenAI API Key (Optional):" "false"
prompt_and_save "ANTHROPIC_API_KEY" "Enter your Anthropic API Key (Optional):" "false"

# GCA Configuration
prompt_and_save "GCA_RISK_TOLERANCE" "Enter GCA Risk Tolerance (0.1 - 1.0, Default: 0.3):" "false"

# Directories (Defaults usually work, but good to confirm)
prompt_and_save "OPENCLAW_CONFIG_DIR" "Config Directory (Default: ./.config/openclaw):" "false"
if ! grep -q "^OPENCLAW_CONFIG_DIR=" "$ENV_FILE"; then
    echo "OPENCLAW_CONFIG_DIR=./.config/openclaw" >> "$ENV_FILE"
fi

prompt_and_save "OPENCLAW_WORKSPACE_DIR" "Workspace Directory (Default: ./workspace):" "false"
if ! grep -q "^OPENCLAW_WORKSPACE_DIR=" "$ENV_FILE"; then
    echo "OPENCLAW_WORKSPACE_DIR=./workspace" >> "$ENV_FILE"
fi

echo ""
echo -e "${GREEN}Configuration saved to ${ENV_FILE}!${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Setup Complete!                     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "You can now start the services using Docker:"
echo -e "${GREEN}docker-compose up -d${NC}"
echo ""
