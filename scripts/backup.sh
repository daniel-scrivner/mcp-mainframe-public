#!/bin/bash
# Backup MCP Mainframe configuration and secrets

set -e

MCP_HUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$HOME/.mcp-mainframe-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mcp-mainframe-backup-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup..."

# Create tarball of important files
tar -czf "$BACKUP_FILE" \
    -C "$MCP_HUB_DIR" \
    config.yaml \
    Makefile \
    secrets/ \
    scripts/ \
    2>/dev/null

echo "✓ Backup created: $BACKUP_FILE"

# Also backup the age key (critical!)
AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"
if [ -f "$AGE_KEY_FILE" ]; then
    cp "$AGE_KEY_FILE" "$BACKUP_DIR/age-keys-$TIMESTAMP.txt"
    chmod 600 "$BACKUP_DIR/age-keys-$TIMESTAMP.txt"
    echo "✓ Age key backed up (KEEP THIS SAFE!)"
fi

# Cleanup old backups (keep last 10)
ls -t "$BACKUP_DIR"/mcp-mainframe-backup-*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To restore:"
echo "  tar -xzf $BACKUP_FILE -C ~/mcp-mainframe"
echo "  cp $BACKUP_DIR/age-keys-$TIMESTAMP.txt ~/.config/sops/age/keys.txt"
