# IBKR MCP Server

MCP server for Interactive Brokers access via SQS-based communication with a TWS service running on EC2.

## Overview

This server provides Claude Code with access to Interactive Brokers through SQS-based communication with a TWSService running on EC2. It does **not** connect directly to TWS - instead, it requires a separate TWS service that handles:

- Headless TWS with automated MFA
- Connection management and health checks
- Circuit breakers and retry logic
- S3 storage for market data

## Architecture

```
Claude Code → IBKR MCP Server (local) → SQS → EC2/TWS → SQS → MCP Server
```

## Prerequisites

1. **AWS Credentials**: The server needs AWS credentials with access to:
   - SQS queues for requests and responses
   - Region: Your AWS region (default: `us-west-2`)

2. **EC2/TWS Service**: A TWSService must be running on EC2 and listening to the SQS queues.

3. **SQS Queues**: You must create request and response queues in your AWS account.

## Installation

```bash
# Install in development mode
cd servers/ibkr-mcp
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Configuration

The server **requires** these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `IBKR_REQUEST_QUEUE_URL` | Yes | Full SQS URL for request queue |
| `IBKR_RESPONSE_QUEUE_URL` | Yes | Full SQS URL for response queue |
| `AWS_REGION` | No | AWS region (default: `us-west-2`) |
| `AWS_ACCESS_KEY_ID` | No | AWS access key (can use AWS config) |
| `AWS_SECRET_ACCESS_KEY` | No | AWS secret key (can use AWS config) |

Example queue URLs:
```
https://sqs.us-west-2.amazonaws.com/123456789012/ibkr-requests
https://sqs.us-west-2.amazonaws.com/123456789012/ibkr-responses
```

## Available Tools

### `ibkr_health`
Check TWS connection status. Returns connection state, server time, and ping duration.

### `ibkr_account_summary`
Get account values including balances, buying power, and P&L. Data is stored in S3.

### `ibkr_positions`
Get current portfolio positions with quantities, average costs, and exchange rates.

### `ibkr_daily_ohlcv`
Get daily OHLCV data for all tracked symbols (7 days of daily bars).

### `ibkr_hourly_ohlcv`
Get hourly OHLCV data for all tracked symbols (7 days of hourly bars).

### `ibkr_contract_details`
Get detailed contract information for all tracked symbols.

### `ibkr_search_symbols`
Search for contracts by query string.

**Parameters:**
- `query` (required): Search string (e.g., "AAPL", "Apple")

### `ibkr_contract_by_id`
Get details for a specific contract by ID.

**Parameters:**
- `contract_id` (required): IBKR contract ID (conId)
- `check_ohlcv` (optional): If true, verify OHLCV data availability

### `ibkr_custom_ohlcv`
Get OHLCV data for specific symbols (not just tracked ones).

**Parameters:**
- `symbols` (required): Array of symbol specifications
  - `symbol`: Ticker symbol
  - `currency`: Currency (USD, EUR, etc.)
  - `secType`: Security type (STK, IND, CMDTY)
  - `exchange`: Exchange (optional)
  - `conId`: Contract ID if known (optional)
- `duration` (optional): Duration string (default: "7 D")
- `bar_size` (optional): Bar size (default: "1 day")

## Usage with Claude Code

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "python",
      "args": ["-m", "ibkr_mcp.server"],
      "env": {
        "IBKR_REQUEST_QUEUE_URL": "https://sqs.us-west-2.amazonaws.com/YOUR_ACCOUNT/ibkr-requests",
        "IBKR_RESPONSE_QUEUE_URL": "https://sqs.us-west-2.amazonaws.com/YOUR_ACCOUNT/ibkr-responses",
        "AWS_REGION": "us-west-2"
      }
    }
  }
}
```

Or if installed globally:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "ibkr-mcp",
      "env": {
        "IBKR_REQUEST_QUEUE_URL": "https://sqs.us-west-2.amazonaws.com/YOUR_ACCOUNT/ibkr-requests",
        "IBKR_RESPONSE_QUEUE_URL": "https://sqs.us-west-2.amazonaws.com/YOUR_ACCOUNT/ibkr-responses"
      }
    }
  }
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=ibkr_mcp
```

## Troubleshooting

### Missing queue URL errors
The server requires both `IBKR_REQUEST_QUEUE_URL` and `IBKR_RESPONSE_QUEUE_URL` environment variables.

### Timeout errors
The TWS service on EC2 may be unavailable or processing a long operation. Check:
1. EC2 instance is running
2. TWS is connected (run MFA script if needed)
3. SQS queues are accessible

### AWS credential errors
Ensure your AWS credentials are configured:
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### No response from TWS
The TWSService polls SQS for messages. If it's not running:
1. SSH to EC2
2. Check tmux sessions: `tmux ls`
3. Start the service: `tmux new -s tws` then run the service
