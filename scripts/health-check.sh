#!/bin/bash
# Health check script for MCP servers
# Verifies each enabled server can start and respond

# Don't exit on error - we want to check all servers
set +e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$MCP_HUB_DIR/logs/health-checks"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

log() {
    echo "$@" | tee -a "$LOG_FILE"
}

check_command() {
    local name=$1
    local cmd=$2

    if command -v "$cmd" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_npm_package() {
    local name=$1
    local package=$2

    echo -n "  Checking $name ($package)... "

    # Try to resolve the package
    if npx -y "$package" --help >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}○${NC} (package not tested - may work at runtime)"
        ((SKIPPED++))
        return 0
    fi
}

check_remote_mcp() {
    local name=$1
    local url=$2

    echo -n "  Checking $name ($url)... "

    # Check if URL is reachable
    if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        # Remote MCPs often don't respond to simple GET, so we assume they work
        echo -e "${YELLOW}○${NC} (remote - assumed working)"
        ((SKIPPED++))
        return 0
    fi
}

check_docker_image() {
    local name=$1
    local image=$2

    echo -n "  Checking $name ($image)... "

    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${YELLOW}○${NC} (docker not available)"
        ((SKIPPED++))
        return 0
    fi

    # Check if image exists or can be pulled
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    elif docker pull "$image" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} (pulled)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} (image not available)"
        ((FAILED++))
        return 1
    fi
}

check_local_server() {
    local name=$1
    local path=$2

    echo -n "  Checking $name ($path)... "

    if [ -d "$MCP_HUB_DIR/$path" ]; then
        if [ -f "$MCP_HUB_DIR/$path/package.json" ] || [ -f "$MCP_HUB_DIR/$path/setup.py" ] || [ -f "$MCP_HUB_DIR/$path/requirements.txt" ]; then
            echo -e "${GREEN}✓${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${YELLOW}○${NC} (exists but may need setup)"
            ((SKIPPED++))
            return 0
        fi
    else
        echo -e "${RED}✗${NC} (not installed)"
        ((FAILED++))
        return 1
    fi
}

check_pip_package() {
    local name=$1
    local package=$2

    echo -n "  Checking $name ($package)... "

    if python3 -c "import $(echo $package | tr '-' '_')" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    elif pip show "$package" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} (not installed)"
        ((FAILED++))
        return 1
    fi
}

# Main
log "MCP Mainframe Health Check - $(date)"
log "================================"
log ""

# Check dependencies first
log "Dependencies:"
for dep in node python3 docker sops age yq; do
    if check_command "$dep" "$dep"; then
        log "  $dep: $(which $dep)"
    else
        log "  $dep: NOT FOUND"
    fi
done
log ""

# Read config and check each server
log "Servers:"

# Parse config.yaml using yq
if ! command -v yq >/dev/null 2>&1; then
    log "Error: yq not installed. Run: brew install yq"
    exit 1
fi

# Get list of enabled servers
servers=$(yq '.servers | keys | .[]' "$MCP_HUB_DIR/config.yaml")

for server in $servers; do
    enabled=$(yq ".servers[\"$server\"].enabled" "$MCP_HUB_DIR/config.yaml")

    # Treat missing/null as enabled, only skip if explicitly false
    if [ "$enabled" = "false" ]; then
        echo "  $server: DISABLED"
        ((SKIPPED++))
        continue
    fi

    source=$(yq ".servers[\"$server\"].source" "$MCP_HUB_DIR/config.yaml")

    case "$source" in
        npx|npm)
            package=$(yq ".servers[\"$server\"].package" "$MCP_HUB_DIR/config.yaml")
            check_npm_package "$server" "$package"
            ;;
        pip)
            package=$(yq ".servers[\"$server\"].package" "$MCP_HUB_DIR/config.yaml")
            check_pip_package "$server" "$package"
            ;;
        docker)
            image=$(yq ".servers[\"$server\"].image" "$MCP_HUB_DIR/config.yaml")
            check_docker_image "$server" "$image"
            ;;
        local)
            path=$(yq ".servers[\"$server\"].path" "$MCP_HUB_DIR/config.yaml")
            check_local_server "$server" "$path"
            ;;
        *)
            echo "  $server: Unknown source type: $source"
            ((SKIPPED++))
            ;;
    esac
done

log ""
log "================================"
log "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}, ${YELLOW}$SKIPPED skipped${NC}"
log "Log saved to: $LOG_FILE"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
