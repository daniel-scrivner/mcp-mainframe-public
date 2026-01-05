# MCP Mainframe Makefile
# Run `make help` to see available commands

.PHONY: help setup install generate health update secrets-init secrets-edit clean

# Default target
help:
	@echo "MCP Mainframe - Centralized MCP Server Management"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Initial setup (install deps, init secrets)"
	@echo "  make install        - Install/update all server dependencies"
	@echo ""
	@echo "Daily Commands:"
	@echo "  make generate       - Generate Claude config from config.yaml"
	@echo "  make health         - Run health checks on all servers"
	@echo "  make status         - Show server status summary"
	@echo ""
	@echo "Secret Management:"
	@echo "  make secrets-init   - Initialize age key and SOPS config"
	@echo "  make secrets-edit   - Edit secrets (decrypts, opens editor, re-encrypts)"
	@echo "  make secrets-rotate - Rotate encryption key"
	@echo ""
	@echo "Maintenance:"
	@echo "  make update         - Update servers to latest pinned versions"
	@echo "  make clean          - Remove generated files and logs"
	@echo "  make backup         - Backup secrets and config"

# ============================================================================
# Setup
# ============================================================================

setup: check-deps secrets-init install generate
	@echo "✓ MCP Mainframe setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit secrets: make secrets-edit SERVICE=github"
	@echo "  2. Regenerate config: make generate"
	@echo "  3. Run health checks: make health"

check-deps:
	@echo "Checking dependencies..."
	@command -v node >/dev/null 2>&1 || { echo "✗ Node.js not found. Install: brew install node"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "✗ Python 3 not found"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "✗ Docker not found. Install: brew install --cask docker"; exit 1; }
	@command -v sops >/dev/null 2>&1 || { echo "✗ SOPS not found. Install: brew install sops"; exit 1; }
	@command -v age >/dev/null 2>&1 || { echo "✗ age not found. Install: brew install age"; exit 1; }
	@command -v yq >/dev/null 2>&1 || { echo "✗ yq not found. Install: brew install yq"; exit 1; }
	@echo "✓ All dependencies found"

install: install-npm install-pip install-local
	@echo "✓ All servers installed"

install-npm:
	@echo "Installing npm-based servers..."
	@npm install -g slack-mcp-server mcp-remote 2>/dev/null || true

install-pip:
	@echo "Installing pip-based servers..."
	@pip install mcp-server-dagster 2>/dev/null || true

install-local:
	@echo "Setting up local servers..."
	@./scripts/install-local-servers.sh

# ============================================================================
# Generation
# ============================================================================

generate:
	@echo "Generating Claude config..."
	@python3 scripts/generate-claude-config.py
	@echo "✓ Claude config updated"

# ============================================================================
# Health Checks
# ============================================================================

health:
	@echo "Running health checks..."
	@./scripts/health-check.sh

status:
	@echo "Server Status:"
	@./scripts/status.sh

# ============================================================================
# Secret Management
# ============================================================================

AGE_KEY_FILE := ~/.config/sops/age/keys.txt

secrets-init:
	@echo "Initializing secrets..."
	@mkdir -p ~/.config/sops/age
	@if [ ! -f $(AGE_KEY_FILE) ]; then \
		age-keygen -o $(AGE_KEY_FILE) 2>/dev/null; \
		chmod 600 $(AGE_KEY_FILE); \
		echo "✓ Age key generated at $(AGE_KEY_FILE)"; \
	else \
		echo "✓ Age key already exists"; \
	fi
	@./scripts/init-sops-config.sh

secrets-edit:
ifndef SERVICE
	@echo "Usage: make secrets-edit SERVICE=<service-name>"
	@echo "Available services:"
	@ls -1 secrets/*.enc.yaml 2>/dev/null | xargs -I {} basename {} .enc.yaml | sed 's/^/  /' || echo "  (none)"
else
	@SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops --config secrets/.sops.yaml secrets/$(SERVICE).enc.yaml
endif

secrets-create:
ifndef SERVICE
	@echo "Usage: make secrets-create SERVICE=<service-name>"
else
	@./scripts/create-secret.sh $(SERVICE)
endif

secrets-rotate:
	@echo "Rotating encryption keys..."
	@./scripts/rotate-secrets.sh

# ============================================================================
# Maintenance
# ============================================================================

update:
	@echo "Updating servers..."
	@./scripts/update-servers.sh
	@make generate

clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/*
	@find logs -type f -mtime +30 -delete 2>/dev/null || true
	@echo "✓ Cleaned"

backup:
	@echo "Creating backup..."
	@./scripts/backup.sh

# ============================================================================
# Development
# ============================================================================

test:
	@echo "Running tests..."
	@./scripts/test.sh

lint:
	@yamllint config.yaml
	@python3 -m py_compile scripts/generate-claude-config.py
