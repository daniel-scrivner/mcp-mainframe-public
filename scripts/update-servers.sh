#!/bin/bash
# Update all MCP servers to their specified versions

set -e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Updating MCP servers..."
echo ""

# Update npm global packages
echo "Updating npm packages..."
npm update -g slack-mcp-server mcp-remote 2>/dev/null || true
echo -e "${GREEN}✓${NC} npm packages updated"

# Update pip packages
echo "Updating pip packages..."
pip install --upgrade mcp-server-dagster 2>/dev/null || true
echo -e "${GREEN}✓${NC} pip packages updated"

# Update Docker images
echo "Updating Docker images..."
docker pull ghcr.io/github/github-mcp-server:latest 2>/dev/null || true
echo -e "${GREEN}✓${NC} Docker images updated"

# Update local servers
echo "Updating local servers..."
for server_dir in "$MCP_HUB_DIR/servers"/*; do
    if [ -d "$server_dir/.git" ]; then
        name=$(basename "$server_dir")
        echo "  Updating $name..."
        cd "$server_dir"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true

        # Rebuild if package.json exists
        if [ -f "package.json" ]; then
            npm install && npm run build 2>/dev/null || true
        fi

        # Reinstall if requirements.txt exists
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt 2>/dev/null || true
        fi
    fi
done
echo -e "${GREEN}✓${NC} Local servers updated"

echo ""
echo "Update complete. Run 'make generate' to regenerate Claude config."
