# MCP Mainframe

A centralized management system for [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers used with [Claude Code](https://docs.anthropic.com/en/docs/claude-code). This project provides a unified configuration hub for deploying, managing, and maintaining 20+ MCP server integrations.

## What is This?

If you use Claude Code with multiple MCP servers, you've probably experienced the pain of:

- Managing API keys and tokens across dozens of services
- Keeping `~/.claude.json` in sync across machines
- Debugging why a particular MCP server stopped working
- Remembering which servers need OAuth refresh vs API keys

**MCP Mainframe** solves these problems by providing:

- **Single source of truth**: One `config.yaml` file defines all your MCP servers
- **Encrypted secrets**: SOPS/age encryption keeps credentials safe in version control
- **Auto-generation**: Scripts generate your `~/.claude.json` from config
- **Health checks**: Verify all servers are working with one command
- **Tiered organization**: Servers categorized by importance (Tier 1-4)

## Quick Start

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- Python 3.11+
- [SOPS](https://github.com/getsops/sops) for secret encryption
- [age](https://github.com/FiloSottile/age) for encryption keys

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/mcp-mainframe.git
cd mcp-mainframe

# Install dependencies
brew install sops age  # macOS
# or: apt install sops age  # Ubuntu/Debian

# Initialize encryption (creates age key if needed)
make setup

# Edit config.yaml to enable/configure your servers
# Edit secrets files with your credentials
make secrets-edit SERVICE=github

# Generate Claude config
make generate

# Restart Claude Code to pick up changes
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Mainframe                          │
├─────────────────────────────────────────────────────────────┤
│  config.yaml          │  secrets/*.enc.yaml                 │
│  ─────────────        │  ──────────────────                 │
│  Server definitions   │  Encrypted credentials              │
│  Enable/disable       │  API keys, tokens                   │
│  Version pinning      │  OAuth secrets                      │
└──────────┬────────────┴──────────────┬──────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│              generate-claude-config.py                       │
│  Combines config + decrypted secrets → ~/.claude.json       │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code                              │
│  Loads ~/.claude.json on startup                            │
│  Connects to configured MCP servers                         │
└─────────────────────────────────────────────────────────────┘
```

## Server Categories

Servers are organized into tiers based on usage frequency and criticality:

### Tier 1: Critical (Daily Use)
| Server | Description | Auth Type |
|--------|-------------|-----------|
| GitHub | Repos, issues, PRs, Actions | Personal Access Token |
| Linear | Issue tracking, projects | OAuth (browser) |
| Slack | Messages, channels, search | Session tokens |
| Notion | Pages, databases, blocks | OAuth (browser) |

### Tier 2: Important (Regular Use)
| Server | Description | Auth Type |
|--------|-------------|-----------|
| Figma | Design files, components | Local app / OAuth |
| Framer | Design, components, React export | Plugin MCP URL |
| Stripe | Payments, customers, subscriptions | API key |
| AWS Lambda | Serverless function invocation | Access key/secret |
| Cloudflare | Workers, KV, R2, DNS | OAuth (browser) |

### Tier 3: Specialized
| Server | Description | Auth Type |
|--------|-------------|-----------|
| Craft | Notes, documents, spaces | MCP URL |
| Composer | Trading strategies, backtesting | OAuth |
| Dropbox | Files, folders, sharing | OAuth |
| Vercel | Deployments, projects, domains | API token |
| Readwise | Highlights, books, articles | Access token |
| Ghost | CMS posts, pages, members | Admin API key |
| 1Password | Vault-scoped credential access | Service Account token |
| Asana | Tasks, projects, workspaces | OAuth |

### Tier 4: Niche
| Server | Description | Auth Type |
|--------|-------------|-----------|
| Namecheap | Domains, DNS management | API key + IP whitelist |
| Front | Email, conversations, contacts | JWT token |

## Configuration

### config.yaml Structure

```yaml
servers:
  github:
    tier: 1
    enabled: true
    source: docker
    image: ghcr.io/github/github-mcp-server
    version: latest
    transport: stdio
    secrets_file: secrets/github.enc.yaml
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    description: "GitHub repositories, issues, PRs, and Actions"

  slack:
    tier: 1
    enabled: true
    source: npm
    package: "@anthropic/slack-mcp"
    version: "0.1.0"
    transport: stdio
    secrets_file: secrets/slack.enc.yaml
    env:
      SLACK_XOXC_TOKEN: "${SLACK_XOXC}"
      SLACK_XOXD_TOKEN: "${SLACK_XOXD}"
    description: "Slack messages, channels, and search"
```

### Secrets Management

Secrets are encrypted using SOPS with age encryption:

```bash
# Create a new secret file
make secrets-create SERVICE=myservice

# Edit an existing secret
make secrets-edit SERVICE=github

# View decrypted secrets (careful!)
sops -d secrets/github.enc.yaml
```

Secret file format (`secrets/github.enc.yaml`):

```yaml
# Before encryption
GITHUB_TOKEN: ghp_xxxxxxxxxxxxxxxxxxxx

# After encryption (what's stored in git)
GITHUB_TOKEN: ENC[AES256_GCM,data:...,iv:...,tag:...,type:str]
sops:
    age:
        - recipient: age1...
          enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            ...
```

## Commands

```bash
# Setup & Configuration
make setup              # Initial setup (creates age key, installs deps)
make generate           # Generate ~/.claude.json from config
make validate           # Validate config.yaml syntax

# Server Management
make health             # Run health checks on all enabled servers
make status             # Show server status summary
make update             # Update server versions

# Secrets Management
make secrets-edit SERVICE=<name>   # Edit encrypted secrets
make secrets-create SERVICE=<name> # Create new secret file
make secrets-rotate                # Rotate age encryption key

# Maintenance
make backup             # Backup config + secrets
make clean              # Remove generated files
make logs               # View recent logs
```

## Custom MCP Servers

This project includes two custom MCP server implementations:

### 1Password MCP Server (`servers/onepassword-mcp/`)

A security-focused 1Password integration using the official SDK:

- **Vault allowlisting**: Restrict Claude to specific vaults (default: "AI" vault only)
- **Field redaction**: Sensitive fields hidden unless explicitly requested
- **Rate limiting**: Built-in delays to prevent abuse
- **Multi-account**: Run separate instances for personal/work accounts

```bash
cd servers/onepassword-mcp
uv sync
uv run python -m onepassword_mcp
```

### Interactive Brokers MCP Server (`servers/ibkr-mcp/`)

Trading data access via Interactive Brokers TWS:

- Historical OHLCV data (daily, hourly, custom)
- Account summary and positions
- Symbol search and contract details
- Communicates with TWS via AWS SQS (requires EC2 setup)

```bash
cd servers/ibkr-mcp
uv sync
uv run python -m ibkr_mcp
```

## Security Considerations

### What's Safe to Commit

- ✅ `config.yaml` - Server definitions (no secrets)
- ✅ `secrets/*.enc.yaml` - Encrypted credentials
- ✅ `secrets/.sops.yaml` - SOPS config (public key only)
- ✅ All scripts and documentation

### What's NOT Safe

- ❌ Unencrypted secret files
- ❌ Your age private key (`~/.config/sops/age/keys.txt`)
- ❌ Generated `~/.claude.json` (contains decrypted secrets)
- ❌ Any file with actual API keys/tokens

### Best Practices

1. **Never commit unencrypted secrets** - The `.gitignore` prevents this, but be careful
2. **Backup your age key** - If you lose it, you can't decrypt your secrets
3. **Use service accounts** - Where possible, use scoped tokens (1Password, AWS IAM)
4. **Review before pushing** - Run `git diff --staged` to check for secrets
5. **Rotate regularly** - Use `make secrets-rotate` periodically

## Troubleshooting

### Server not connecting

```bash
# Check if server is enabled
grep -A5 "servername:" config.yaml

# Run health check
make health

# Check Claude logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

### Secrets decryption failing

```bash
# Verify age key exists
cat ~/.config/sops/age/keys.txt

# Test decryption
sops -d secrets/github.enc.yaml

# Re-encrypt if key changed
make secrets-rotate
```

### Config generation errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check for missing secrets
make validate
```

## Adding a New Server

1. **Add server definition to `config.yaml`**:

```yaml
servers:
  newservice:
    tier: 3
    enabled: true
    source: npm  # or: docker, local, remote, pip
    package: "@company/newservice-mcp"
    version: "1.0.0"
    transport: stdio
    secrets_file: secrets/newservice.enc.yaml
    env:
      API_KEY: "${NEWSERVICE_API_KEY}"
    description: "What this server does"
```

2. **Create secrets file**:

```bash
make secrets-create SERVICE=newservice
# Edit the file to add your credentials
```

3. **Regenerate config**:

```bash
make generate
# Restart Claude Code
```

## File Structure

```
mcp-mainframe/
├── README.md                    # This file
├── config.yaml                  # Master server configuration
├── Makefile                     # CLI commands
├── OPERATIONS.md               # Day-to-day operations guide
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── scripts/
│   ├── generate-claude-config.py    # Config generator
│   ├── health-check.sh              # Server health checks
│   ├── status.sh                    # Status summary
│   ├── backup.sh                    # Backup utility
│   ├── install-local-servers.sh     # Local server setup
│   ├── update-servers.sh            # Version updates
│   ├── init-sops-config.sh          # SOPS initialization
│   └── create-secret.sh             # Secret file creation
├── secrets/
│   ├── .sops.yaml              # SOPS encryption config
│   ├── examples/               # Example secret templates
│   │   ├── github.yaml
│   │   ├── slack.yaml
│   │   └── ...
│   └── *.enc.yaml              # Your encrypted secrets (gitignored templates)
└── servers/
    ├── ibkr-mcp/               # Interactive Brokers server
    └── onepassword-mcp/        # 1Password server
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Ideas for contributions:
- New MCP server integrations
- Improved health checks
- Better error messages
- Documentation improvements
- Security enhancements

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Anthropic](https://anthropic.com) for Claude and the MCP protocol
- The MCP server community for the various integrations
- [SOPS](https://github.com/getsops/sops) and [age](https://github.com/FiloSottile/age) for encryption

---

**Note**: This is a personal project shared for educational purposes. Your mileage may vary with different MCP servers and configurations. Always review security implications before connecting AI assistants to sensitive services.
