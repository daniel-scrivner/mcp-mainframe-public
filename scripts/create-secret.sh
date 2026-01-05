#!/bin/bash
# Create a new encrypted secret file

set -e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service-name>"
    exit 1
fi

SECRET_FILE="$MCP_HUB_DIR/secrets/$SERVICE.enc.yaml"

if [ -f "$SECRET_FILE" ]; then
    echo "Secret file already exists: $SECRET_FILE"
    echo "Use 'make secrets-edit SERVICE=$SERVICE' to edit it"
    exit 1
fi

# Create template
cat > "$SECRET_FILE.tmp" << EOF
# $SERVICE secrets
# Add your secrets below as key: value pairs
# Example:
# API_KEY: your_api_key_here
# API_SECRET: your_api_secret_here
EOF

# Encrypt it
cd "$MCP_HUB_DIR/secrets"
sops -e "$SECRET_FILE.tmp" > "$SECRET_FILE"
rm "$SECRET_FILE.tmp"

echo "Created: $SECRET_FILE"
echo "Edit with: make secrets-edit SERVICE=$SERVICE"
