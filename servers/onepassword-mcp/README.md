# 1Password MCP Server

MCP server for 1Password using the **official `onepassword-sdk-python`** package.

## Features

- **Official SDK**: Uses 1Password's maintained Python SDK
- **Vault Allowlist**: Only exposes vaults you explicitly allow
- **Field Redaction**: Sensitive fields hidden unless explicitly requested
- **Rate Limiting**: 1-second delay between secret resolutions
- **Multi-Account**: Supports personal + work accounts via separate server instances

## Installation

```bash
cd servers/onepassword-mcp
pip install -e .
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OP_SERVICE_ACCOUNT_TOKEN` | Yes | - | 1Password service account token |
| `OP_ALLOWED_VAULTS` | No | `AI` | Comma-separated vault allowlist |
| `OP_ENABLE_WRITES` | No | `false` | Enable write operations |
| `OP_LOG_LEVEL` | No | `INFO` | Logging level |

### Setup

1. **Create a Service Account** at my.1password.com → Developer Tools
2. **Grant access** ONLY to vaults you want Claude to access
3. **Create an "AI" vault** for items you want to expose (recommended)
4. **Set the token** in your secrets file

## Available Tools

### Read-Only (Always Available)

| Tool | Description |
|------|-------------|
| `op_list_vaults` | List accessible vaults |
| `op_list_items` | List items in a vault |
| `op_get_item` | Get item metadata (sensitive fields redacted) |
| `op_resolve_secret` | Get a specific field value |
| `op_get_otp` | Get current TOTP code |

### Write (Opt-In via `OP_ENABLE_WRITES=true`)

| Tool | Description |
|------|-------------|
| `op_create_item` | Create a new item |
| `op_archive_item` | Archive an item |
| `op_generate_password` | Generate a secure password |

## Security Model

### Vault Allowlist

Only vaults listed in `OP_ALLOWED_VAULTS` are accessible:

```bash
# Default: only "AI" vault
OP_ALLOWED_VAULTS="AI"

# Multiple vaults
OP_ALLOWED_VAULTS="AI,Development,Staging"
```

### Field Redaction

When listing items with `op_get_item`, sensitive fields are shown as `[REDACTED]`:
- Password fields
- Concealed fields
- Credit card numbers
- CVV/PIN fields

Use `op_resolve_secret` to get actual values when needed.

### Rate Limiting

`op_resolve_secret` enforces a 1-second delay between calls to prevent rapid credential harvesting.

## Usage Examples

### List Available Vaults

```
op_list_vaults
```

### List Items in a Vault

```
op_list_items vault_id="abc123"
op_list_items vault_id="abc123" category="LOGIN"
```

### Get Item Details

```
op_get_item vault_id="abc123" item_id="xyz789"
```

### Resolve a Secret

```
op_resolve_secret secret_reference="op://AI/GitHub/password"
op_resolve_secret secret_reference="op://AI/AWS/access-key-id"
```

### Get TOTP Code

```
op_get_otp vault_id="abc123" item_id="xyz789"
```

## Multi-Account Setup

Like Figma, you can set up multiple 1Password accounts:

```yaml
# config.yaml
1password:
  enabled: true
  env:
    OP_SERVICE_ACCOUNT_TOKEN: "${OP_SERVICE_ACCOUNT_TOKEN}"
    OP_ALLOWED_VAULTS: "AI,Personal"

1password-work:
  enabled: true
  env:
    OP_SERVICE_ACCOUNT_TOKEN: "${OP_SERVICE_ACCOUNT_TOKEN_WORK}"
    OP_ALLOWED_VAULTS: "Engineering,DevOps"
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run the server
python -m onepassword_mcp.server
```
