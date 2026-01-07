```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███╗   ███╗ ██████╗██████╗                                                 ║
║   ████╗ ████║██╔════╝██╔══██╗                                                ║
║   ██╔████╔██║██║     ██████╔╝                                                ║
║   ██║╚██╔╝██║██║     ██╔═══╝                                                 ║
║   ██║ ╚═╝ ██║╚██████╗██║                                                     ║
║   ╚═╝     ╚═╝ ╚═════╝╚═╝                                                     ║
║                                                                              ║
║   ███╗   ███╗ █████╗ ██╗███╗   ██╗███████╗██████╗  █████╗ ███╗   ███╗███████╗║
║   ████╗ ████║██╔══██╗██║████╗  ██║██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝║
║   ██╔████╔██║███████║██║██╔██╗ ██║█████╗  ██████╔╝███████║██╔████╔██║█████╗  ║
║   ██║╚██╔╝██║██╔══██║██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ║
║   ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CENTRALIZED MCP SERVER MANAGEMENT FOR CLAUDE CODE                           ║
║  ─────────────────────────────────────────────────                           ║
║  STATUS: OPERATIONAL │ SERVERS: 20+ │ LICENSE: MIT                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## SYSTEM OVERVIEW

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  A centralized management system for Model Context Protocol (MCP)         │
│  servers used with Claude Code. Unified configuration hub for deploying,  │
│  managing, and maintaining 20+ MCP server integrations.                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## THE PROBLEM

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  If you use Claude Code with multiple MCP servers, you've experienced:    │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │   ✗  Managing API keys and tokens across dozens of services          │  │
│  │   ✗  Keeping ~/.claude.json in sync across machines                  │  │
│  │   ✗  Debugging why a particular MCP server stopped working           │  │
│  │   ✗  Remembering which servers need OAuth refresh vs API keys        │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## THE SOLUTION

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  MCP MAINFRAME provides:                                                  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │   ✓  SINGLE SOURCE OF TRUTH                                          │  │
│  │      One config.yaml defines all your MCP servers                    │  │
│  │                                                                      │  │
│  │   ✓  ENCRYPTED SECRETS                                               │  │
│  │      SOPS/age encryption keeps credentials safe in version control   │  │
│  │                                                                      │  │
│  │   ✓  AUTO-GENERATION                                                 │  │
│  │      Scripts generate your ~/.claude.json from config                │  │
│  │                                                                      │  │
│  │   ✓  HEALTH CHECKS                                                   │  │
│  │      Verify all servers are working with one command                 │  │
│  │                                                                      │  │
│  │   ✓  TIERED ORGANIZATION                                             │  │
│  │      Servers categorized by importance (Tier 1-4)                    │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                         ┌─────────────────────────┐                        │
│                         │     MCP MAINFRAME       │                        │
│                         └───────────┬─────────────┘                        │
│                                     │                                      │
│              ┌──────────────────────┼──────────────────────┐               │
│              │                      │                      │               │
│              ▼                      ▼                      ▼               │
│   ┌─────────────────────┐  ┌────────────────┐  ┌─────────────────────┐     │
│   │    config.yaml      │  │   secrets/     │  │     scripts/        │     │
│   ├─────────────────────┤  │   *.enc.yaml   │  ├─────────────────────┤     │
│   │  Server definitions │  ├────────────────┤  │  generate-config.py │     │
│   │  Enable/disable     │  │  Encrypted     │  │  health-check.sh    │     │
│   │  Version pinning    │  │  credentials   │  │  status.sh          │     │
│   └──────────┬──────────┘  └───────┬────────┘  └──────────┬──────────┘     │
│              │                     │                      │                │
│              └─────────────────────┼──────────────────────┘                │
│                                    │                                       │
│                                    ▼                                       │
│                   ╔════════════════════════════════╗                       │
│                   ║  generate-claude-config.py     ║                       │
│                   ║  ────────────────────────────  ║                       │
│                   ║  config + secrets → .claude    ║                       │
│                   ╚═══════════════╤════════════════╝                       │
│                                   │                                        │
│                                   ▼                                        │
│                   ┌────────────────────────────────┐                       │
│                   │       ~/.claude.json           │                       │
│                   │  (Generated MCP Configuration) │                       │
│                   └────────────────┬───────────────┘                       │
│                                    │                                       │
│                                    ▼                                       │
│                   ┌────────────────────────────────┐                       │
│                   │         CLAUDE CODE            │                       │
│                   │   Connects to MCP servers      │                       │
│                   └────────────────────────────────┘                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## PREREQUISITES

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  REQUIRED                                                                  │
│  ────────                                                                  │
│                                                                            │
│  • Claude Code       docs.anthropic.com/en/docs/claude-code               │
│  • Python 3.11+      python.org                                           │
│  • SOPS              github.com/getsops/sops                              │
│  • age               github.com/FiloSottile/age                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## QUICK START

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

---

## SERVER TIERS

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║  TIER 1: CRITICAL — Daily Use                                      ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                            │
│  SERVER        DESCRIPTION                       AUTH TYPE                 │
│  ───────────────────────────────────────────────────────────────────────   │
│  GitHub        Repos, issues, PRs, Actions       Personal Access Token     │
│  Linear        Issue tracking, projects          OAuth (browser)           │
│  Slack         Messages, channels, search        Session tokens            │
│  Notion        Pages, databases, blocks          OAuth (browser)           │
│                                                                            │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║  TIER 2: IMPORTANT — Regular Use                                   ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                            │
│  SERVER        DESCRIPTION                       AUTH TYPE                 │
│  ───────────────────────────────────────────────────────────────────────   │
│  Figma         Design files, components          Local app / OAuth         │
│  Framer        Design, components, React export  Plugin MCP URL            │
│  Stripe        Payments, customers, subs         API key                   │
│  AWS Lambda    Serverless function invocation    Access key/secret         │
│  Cloudflare    Workers, KV, R2, DNS              OAuth (browser)           │
│                                                                            │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║  TIER 3: SPECIALIZED                                               ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                            │
│  SERVER        DESCRIPTION                       AUTH TYPE                 │
│  ───────────────────────────────────────────────────────────────────────   │
│  Craft         Notes, documents, spaces          MCP URL                   │
│  Composer      Trading strategies, backtesting   OAuth                     │
│  Dropbox       Files, folders, sharing           OAuth                     │
│  Vercel        Deployments, projects, domains    API token                 │
│  Readwise      Highlights, books, articles       Access token              │
│  Ghost         CMS posts, pages, members         Admin API key             │
│  1Password     Vault-scoped credential access    Service Account token     │
│  Asana         Tasks, projects, workspaces       OAuth                     │
│                                                                            │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║  TIER 4: NICHE                                                     ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                            │
│  SERVER        DESCRIPTION                       AUTH TYPE                 │
│  ───────────────────────────────────────────────────────────────────────   │
│  Namecheap     Domains, DNS management           API key + IP whitelist    │
│  Front         Email, conversations, contacts    JWT token                 │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## CONFIGURATION

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

---

### SECRETS MANAGEMENT

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  Secrets are encrypted using SOPS with age encryption:                    │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │   # Create a new secret file                                         │  │
│  │   $ make secrets-create SERVICE=myservice                            │  │
│  │                                                                      │  │
│  │   # Edit an existing secret                                          │  │
│  │   $ make secrets-edit SERVICE=github                                 │  │
│  │                                                                      │  │
│  │   # View decrypted secrets (careful!)                                │  │
│  │   $ sops -d secrets/github.enc.yaml                                  │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  SECRET FILE FORMAT                                                       │
│  ──────────────────                                                       │
│                                                                            │
│  Before encryption:                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GITHUB_TOKEN: ghp_xxxxxxxxxxxxxxxxxxxx                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  After encryption (stored in git):                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GITHUB_TOKEN: ENC[AES256_GCM,data:...,iv:...,tag:...,type:str]      │  │
│  │  sops:                                                               │  │
│  │      age:                                                            │  │
│  │          - recipient: age1...                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## COMMANDS

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  SETUP & CONFIGURATION                                                    │
│  ─────────────────────                                                    │
│  make setup              Initial setup (creates age key, installs deps)   │
│  make generate           Generate ~/.claude.json from config              │
│  make validate           Validate config.yaml syntax                      │
│                                                                            │
│  SERVER MANAGEMENT                                                        │
│  ─────────────────                                                        │
│  make health             Run health checks on all enabled servers         │
│  make status             Show server status summary                       │
│  make update             Update server versions                           │
│                                                                            │
│  SECRETS MANAGEMENT                                                       │
│  ──────────────────                                                       │
│  make secrets-edit SERVICE=<name>    Edit encrypted secrets               │
│  make secrets-create SERVICE=<name>  Create new secret file               │
│  make secrets-rotate                 Rotate age encryption key            │
│                                                                            │
│  MAINTENANCE                                                              │
│  ───────────                                                              │
│  make backup             Backup config + secrets                          │
│  make clean              Remove generated files                           │
│  make logs               View recent logs                                 │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## CUSTOM MCP SERVERS

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  This project includes two custom MCP server implementations:             │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  1PASSWORD MCP SERVER                                                │  │
│  │  ════════════════════                                                │  │
│  │  servers/onepassword-mcp/                                            │  │
│  │                                                                      │  │
│  │  Security-focused 1Password integration using the official SDK:     │  │
│  │                                                                      │  │
│  │  • Vault allowlisting — Restrict Claude to specific vaults           │  │
│  │  • Field redaction — Sensitive fields hidden unless requested        │  │
│  │  • Rate limiting — Built-in delays to prevent abuse                  │  │
│  │  • Multi-account — Separate instances for personal/work              │  │
│  │                                                                      │  │
│  │  $ cd servers/onepassword-mcp                                        │  │
│  │  $ uv sync && uv run python -m onepassword_mcp                       │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  INTERACTIVE BROKERS MCP SERVER                                      │  │
│  │  ══════════════════════════════                                      │  │
│  │  servers/ibkr-mcp/                                                   │  │
│  │                                                                      │  │
│  │  Trading data access via Interactive Brokers TWS:                   │  │
│  │                                                                      │  │
│  │  • Historical OHLCV data (daily, hourly, custom)                     │  │
│  │  • Account summary and positions                                     │  │
│  │  • Symbol search and contract details                                │  │
│  │  • Communicates with TWS via AWS SQS (requires EC2)                  │  │
│  │                                                                      │  │
│  │  $ cd servers/ibkr-mcp                                               │  │
│  │  $ uv sync && uv run python -m ibkr_mcp                              │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## SECURITY

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ✓  SAFE TO COMMIT                                                   │  │
│  │  ══════════════════                                                  │  │
│  │                                                                      │  │
│  │  config.yaml              Server definitions (no secrets)            │  │
│  │  secrets/*.enc.yaml       Encrypted credentials                      │  │
│  │  secrets/.sops.yaml       SOPS config (public key only)              │  │
│  │  All scripts/docs         No sensitive data                          │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ✗  NEVER COMMIT                                                     │  │
│  │  ═══════════════                                                     │  │
│  │                                                                      │  │
│  │  Unencrypted secrets      Raw API keys and tokens                    │  │
│  │  ~/.config/sops/age/      Your private encryption key                │  │
│  │  ~/.claude.json           Contains decrypted secrets                 │  │
│  │  Any plaintext creds      Check before every push                    │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  BEST PRACTICES                                                           │
│  ──────────────                                                           │
│                                                                            │
│  [1]  Never commit unencrypted secrets (.gitignore helps)                 │
│  [2]  Backup your age key — loss means no decryption                      │
│  [3]  Use service accounts — scoped tokens where possible                 │
│  [4]  Review before pushing — git diff --staged                           │
│  [5]  Rotate regularly — make secrets-rotate                              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## TROUBLESHOOTING

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  SERVER NOT CONNECTING                                                    │
│  ─────────────────────                                                    │
│                                                                            │
│  $ grep -A5 "servername:" config.yaml  # Check if enabled                 │
│  $ make health                          # Run health check                │
│  $ tail -f ~/Library/Logs/Claude/mcp*.log  # Check logs                   │
│                                                                            │
│  SECRETS DECRYPTION FAILING                                               │
│  ──────────────────────────                                               │
│                                                                            │
│  $ cat ~/.config/sops/age/keys.txt     # Verify age key exists            │
│  $ sops -d secrets/github.enc.yaml     # Test decryption                  │
│  $ make secrets-rotate                  # Re-encrypt if key changed       │
│                                                                            │
│  CONFIG GENERATION ERRORS                                                 │
│  ────────────────────────                                                 │
│                                                                            │
│  $ python -c "import yaml; yaml.safe_load(open('config.yaml'))"           │
│  $ make validate                        # Check for missing secrets       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ADDING A NEW SERVER

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  [1]  ADD SERVER DEFINITION TO config.yaml                                │
│                                                                            │
│       servers:                                                            │
│         newservice:                                                       │
│           tier: 3                                                         │
│           enabled: true                                                   │
│           source: npm  # or: docker, local, remote, pip                   │
│           package: "@company/newservice-mcp"                              │
│           version: "1.0.0"                                                │
│           transport: stdio                                                │
│           secrets_file: secrets/newservice.enc.yaml                       │
│           env:                                                            │
│             API_KEY: "${NEWSERVICE_API_KEY}"                              │
│           description: "What this server does"                            │
│                                                                            │
│  [2]  CREATE SECRETS FILE                                                 │
│                                                                            │
│       $ make secrets-create SERVICE=newservice                            │
│       # Edit the file to add your credentials                             │
│                                                                            │
│  [3]  REGENERATE CONFIG                                                   │
│                                                                            │
│       $ make generate                                                     │
│       # Restart Claude Code                                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## FILE STRUCTURE

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  mcp-mainframe/                                                           │
│  │                                                                        │
│  ├── README.md                     This file                              │
│  ├── config.yaml                   Master server configuration            │
│  ├── Makefile                      CLI commands                           │
│  ├── OPERATIONS.md                 Day-to-day operations guide            │
│  ├── CONTRIBUTING.md               Contribution guidelines                │
│  ├── LICENSE                       MIT License                            │
│  │                                                                        │
│  ├── scripts/                                                             │
│  │   ├── generate-claude-config.py Config generator                       │
│  │   ├── health-check.sh           Server health checks                   │
│  │   ├── status.sh                 Status summary                         │
│  │   ├── backup.sh                 Backup utility                         │
│  │   ├── install-local-servers.sh  Local server setup                     │
│  │   ├── update-servers.sh         Version updates                        │
│  │   ├── init-sops-config.sh       SOPS initialization                    │
│  │   └── create-secret.sh          Secret file creation                   │
│  │                                                                        │
│  ├── secrets/                                                             │
│  │   ├── .sops.yaml                SOPS encryption config                 │
│  │   ├── examples/                 Example secret templates               │
│  │   └── *.enc.yaml                Encrypted secrets                      │
│  │                                                                        │
│  └── servers/                                                             │
│      ├── ibkr-mcp/                 Interactive Brokers server             │
│      └── onepassword-mcp/          1Password server                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## CONTRIBUTING

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  See CONTRIBUTING.md for guidelines. Ideas welcome:                       │
│                                                                            │
│  • New MCP server integrations                                            │
│  • Improved health checks                                                 │
│  • Better error messages                                                  │
│  • Documentation improvements                                             │
│  • Security enhancements                                                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ACKNOWLEDGMENTS

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  • Anthropic         Claude and the MCP protocol                          │
│  • MCP Community     Various server integrations                          │
│  • SOPS + age        Encryption tooling                                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  NOTE: Personal project shared for educational purposes. Your mileage     │
│  may vary. Always review security implications before connecting AI       │
│  assistants to sensitive services.                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```
