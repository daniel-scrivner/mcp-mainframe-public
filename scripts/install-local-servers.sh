#!/bin/bash
# Install local MCP servers from git repositories

set -e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVERS_DIR="$MCP_HUB_DIR/servers"

mkdir -p "$SERVERS_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

install_server() {
    local name=$1
    local repo=$2
    local commit=$3
    local setup_cmd=$4

    echo "Installing $name..."

    if [ -d "$SERVERS_DIR/$name" ]; then
        echo "  Already exists, updating..."
        cd "$SERVERS_DIR/$name"
        git fetch origin
        git checkout "$commit" 2>/dev/null || git checkout "origin/$commit"
    else
        echo "  Cloning from $repo..."
        git clone "$repo" "$SERVERS_DIR/$name"
        cd "$SERVERS_DIR/$name"
        git checkout "$commit" 2>/dev/null || true
    fi

    # Run setup command
    if [ -n "$setup_cmd" ]; then
        echo "  Running setup: $setup_cmd"
        eval "$setup_cmd"
    fi

    echo -e "  ${GREEN}✓${NC} $name installed"
}

# Namecheap MCP
install_server "namecheap" \
    "https://github.com/johnsorrentino/mcp-namecheap" \
    "main" \
    "npm install && npm run build"

# Front MCP (TypeScript)
install_server "front" \
    "https://github.com/zqushair/frontapp-mcp" \
    "main" \
    "npm install && npm run build 2>/dev/null || true"

# Interactive Brokers MCP (just clone, user must set up manually)
if [ ! -d "$SERVERS_DIR/ibkr" ]; then
    echo "Installing ibkr..."
    git clone "https://github.com/rcontesti/IB_MCP" "$SERVERS_DIR/ibkr"
    echo -e "  ${YELLOW}○${NC} ibkr cloned - requires manual setup:"
    echo "    1. cd $SERVERS_DIR/ibkr"
    echo "    2. cp .env.example .env"
    echo "    3. docker compose up --build -d"
    echo "    4. Open https://localhost:5055/ and authenticate"
else
    echo "  ibkr already exists"
fi

echo ""
echo -e "${GREEN}✓${NC} Local servers installed"
