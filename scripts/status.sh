#!/bin/bash
# Show status of all MCP servers

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "MCP Mainframe Status"
echo "=============="
echo ""

# Check if yq is installed
if ! command -v yq >/dev/null 2>&1; then
    echo "Error: yq not installed. Run: brew install yq"
    exit 1
fi

# Get list of servers grouped by tier
for tier in 1 2 3 4; do
    case $tier in
        1) tier_name="Critical" ;;
        2) tier_name="Important" ;;
        3) tier_name="Useful" ;;
        4) tier_name="Niche" ;;
    esac

    echo -e "${BLUE}Tier $tier: $tier_name${NC}"

    servers=$(yq ".servers | to_entries | .[] | select(.value.tier == $tier) | .key" "$MCP_HUB_DIR/config.yaml")

    if [ -z "$servers" ]; then
        echo "  (none)"
        continue
    fi

    for server in $servers; do
        enabled=$(yq ".servers.$server.enabled // true" "$MCP_HUB_DIR/config.yaml")
        source=$(yq ".servers.$server.source" "$MCP_HUB_DIR/config.yaml")
        description=$(yq ".servers.$server.description // \"\"" "$MCP_HUB_DIR/config.yaml")

        if [ "$enabled" = "true" ]; then
            status="${GREEN}●${NC}"
        else
            status="${YELLOW}○${NC}"
        fi

        printf "  %b %-20s %-10s %s\n" "$status" "$server" "($source)" "$description"
    done
    echo ""
done

# Show secrets status
echo -e "${BLUE}Secrets${NC}"
if [ -d "$MCP_HUB_DIR/secrets" ]; then
    for secret in "$MCP_HUB_DIR/secrets"/*.enc.yaml; do
        if [ -f "$secret" ]; then
            name=$(basename "$secret" .enc.yaml)
            # Check if it's a real encrypted file or template
            if sops -d "$secret" >/dev/null 2>&1; then
                echo -e "  ${GREEN}●${NC} $name"
            else
                echo -e "  ${RED}●${NC} $name (decryption failed)"
            fi
        fi
    done
else
    echo "  No secrets configured"
fi
echo ""

# Show recent health check
echo -e "${BLUE}Last Health Check${NC}"
latest_log=$(ls -t "$MCP_HUB_DIR/logs/health-checks"/*.log 2>/dev/null | head -1)
if [ -n "$latest_log" ]; then
    echo "  $(basename "$latest_log")"
    tail -3 "$latest_log" | sed 's/^/  /'
else
    echo "  No health checks run yet"
fi
