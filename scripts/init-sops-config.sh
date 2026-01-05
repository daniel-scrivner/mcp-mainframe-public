#!/bin/bash
# Initialize SOPS configuration for secret management

set -e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the public key from the age key file
if [ ! -f "$AGE_KEY_FILE" ]; then
    echo "Error: Age key not found at $AGE_KEY_FILE"
    echo "Run: make secrets-init"
    exit 1
fi

PUBLIC_KEY=$(grep "public key:" "$AGE_KEY_FILE" | cut -d: -f2 | tr -d ' ')

if [ -z "$PUBLIC_KEY" ]; then
    echo "Error: Could not extract public key from $AGE_KEY_FILE"
    exit 1
fi

echo "Using age public key: $PUBLIC_KEY"

# Create .sops.yaml
cat > "$MCP_HUB_DIR/secrets/.sops.yaml" << EOF
# SOPS configuration for MCP Mainframe secrets
# Encryption uses age (https://github.com/FiloSottile/age)

creation_rules:
  - path_regex: .*\.enc\.yaml$
    age: $PUBLIC_KEY
EOF

echo -e "${GREEN}✓${NC} Created $MCP_HUB_DIR/secrets/.sops.yaml"

# Create template secret files if they don't exist
create_template() {
    local service=$1
    local template=$2
    local file="$MCP_HUB_DIR/secrets/$service.enc.yaml"

    if [ -f "$file" ]; then
        echo "  $service.enc.yaml already exists"
        return
    fi

    # Create unencrypted template with .enc.yaml extension (required by SOPS regex)
    echo "$template" > "$file"

    # Encrypt it in place using explicit config
    cd "$MCP_HUB_DIR/secrets"
    sops --config "$MCP_HUB_DIR/secrets/.sops.yaml" -e -i "$file"

    echo -e "  ${GREEN}✓${NC} Created $service.enc.yaml (edit with: make secrets-edit SERVICE=$service)"
}

echo ""
echo "Creating secret templates..."

create_template "github" "# GitHub secrets
GITHUB_TOKEN: ghp_your_personal_access_token_here"

create_template "slack" "# Slack secrets (browser session tokens - stealth mode)
# Get these from browser DevTools while logged into app.slack.com
# See: https://github.com/korotovsky/slack-mcp-server/blob/master/docs/01-authentication-setup.md
SLACK_XOXC_TOKEN: xoxc-your-token-here
SLACK_XOXD_TOKEN: xoxd-your-token-here"

create_template "stripe" "# Stripe secrets
STRIPE_API_KEY: sk_test_your_api_key_here"

create_template "aws" "# AWS secrets
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: your_secret_key_here
AWS_REGION: us-west-2"

create_template "vercel" "# Vercel secrets
VERCEL_API_TOKEN: your_vercel_token_here"

create_template "namecheap" "# Namecheap secrets
NAMECHEAP_API_USERNAME: your_username
NAMECHEAP_API_KEY: your_api_key
NAMECHEAP_ACCOUNT_USERNAME: your_account_username
NAMECHEAP_IP_ADDRESS: your_whitelisted_ip"

create_template "front" "# Front secrets
FRONT_API_TOKEN: your_front_api_token_here"

echo ""
echo -e "${GREEN}✓${NC} Secret templates created"
echo ""
echo "Next steps:"
echo "  1. Edit each secret file: make secrets-edit SERVICE=<name>"
echo "  2. Regenerate config: make generate"
