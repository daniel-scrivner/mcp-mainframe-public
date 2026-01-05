"""
IBKR MCP Server - Interactive Brokers access via SQS.

This MCP server provides Claude Code with access to Interactive Brokers
through an EC2/TWS infrastructure. It communicates via SQS queues with
a TWS service running on EC2.

Usage:
    # Run as standalone server
    python -m ibkr_mcp.server

    # Or via the installed script
    ibkr-mcp

Environment Variables:
    IBKR_REQUEST_QUEUE_URL: SQS queue URL for sending requests
    IBKR_RESPONSE_QUEUE_URL: SQS queue URL for receiving responses
    AWS_REGION: AWS region (default: us-west-2)
    AWS_ACCESS_KEY_ID: AWS access key
    AWS_SECRET_ACCESS_KEY: AWS secret key
"""

import json
import logging
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from .sqs_client import SQSClient, SQSClientError, SQSTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("ibkr-mcp")

# Lazy-initialized SQS client
_sqs_client: SQSClient | None = None


def get_sqs_client() -> SQSClient:
    """Get or create the SQS client."""
    global _sqs_client
    if _sqs_client is None:
        request_queue = os.environ.get("IBKR_REQUEST_QUEUE_URL")
        response_queue = os.environ.get("IBKR_RESPONSE_QUEUE_URL")

        if not request_queue or not response_queue:
            raise ValueError(
                "IBKR_REQUEST_QUEUE_URL and IBKR_RESPONSE_QUEUE_URL environment "
                "variables must be set. See README for configuration details."
            )

        _sqs_client = SQSClient(
            request_queue_url=request_queue,
            response_queue_url=response_queue,
            region=os.environ.get("AWS_REGION", "us-west-2"),
        )
    return _sqs_client


def format_response(data: dict) -> str:
    """Format response data as readable JSON."""
    return json.dumps(data, indent=2, default=str)


def handle_error(error: Exception) -> list[TextContent]:
    """Handle errors and return appropriate MCP response."""
    if isinstance(error, SQSTimeoutError):
        return [TextContent(
            type="text",
            text=f"Request timed out. The TWS service may be unavailable or processing a long operation.\n\nError: {error}"
        )]
    elif isinstance(error, SQSClientError):
        return [TextContent(
            type="text",
            text=f"SQS communication error. Check AWS credentials and queue access.\n\nError: {error}"
        )]
    else:
        return [TextContent(
            type="text",
            text=f"Unexpected error: {error}"
        )]


# =============================================================================
# Tool Definitions
# =============================================================================

TOOLS = [
    Tool(
        name="ibkr_health",
        description="Check the health of the TWS connection. Returns connection status, server time, and ping duration.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_account_summary",
        description="Get account values including balances, buying power, and P&L. Data is uploaded to S3 and the S3 URI is returned.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_positions",
        description="Get current portfolio positions with quantities, average costs, and exchange rates. Returns S3 URI where positions are stored as Parquet.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_daily_ohlcv",
        description="Get daily OHLCV (Open, High, Low, Close, Volume) data for all tracked symbols. Processes 7 days of daily bars and stores in S3.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_hourly_ohlcv",
        description="Get hourly OHLCV data for all tracked symbols. Processes 7 days of hourly bars and stores in S3.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_contract_details",
        description="Get detailed contract information for all tracked symbols including trading hours, ISIN, and exchange details. Stored in S3.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="ibkr_search_symbols",
        description="Search for contracts matching a query string. Useful for finding symbols, contract IDs, and available exchanges.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'AAPL', 'Apple', 'TSLA')",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="ibkr_contract_by_id",
        description="Get detailed information for a specific contract by its IBKR contract ID (conId).",
        inputSchema={
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "integer",
                    "description": "IBKR contract ID (conId)",
                },
                "check_ohlcv": {
                    "type": "boolean",
                    "description": "If true, also verify OHLCV data availability",
                    "default": False,
                },
            },
            "required": ["contract_id"],
        },
    ),
    Tool(
        name="ibkr_custom_ohlcv",
        description="Get OHLCV data for specific symbols (not just tracked ones). Specify symbols with their properties.",
        inputSchema={
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "description": "List of symbol specifications",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Ticker symbol"},
                            "currency": {"type": "string", "description": "Currency (e.g., USD, EUR)"},
                            "secType": {"type": "string", "description": "Security type (STK, IND, CMDTY)", "default": "STK"},
                            "exchange": {"type": "string", "description": "Exchange (optional)"},
                            "conId": {"type": "integer", "description": "Contract ID if known (optional)"},
                        },
                        "required": ["symbol", "currency"],
                    },
                },
                "duration": {
                    "type": "string",
                    "description": "Duration string (e.g., '7 D', '1 M', '1 Y')",
                    "default": "7 D",
                },
                "bar_size": {
                    "type": "string",
                    "description": "Bar size ('1 day', '1 hour', '5 mins')",
                    "default": "1 day",
                },
            },
            "required": ["symbols"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available IBKR tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    client = get_sqs_client()

    try:
        if name == "ibkr_health":
            result = client.health_check()
            return [TextContent(
                type="text",
                text=f"TWS Health Check:\n{format_response(result)}"
            )]

        elif name == "ibkr_account_summary":
            result = client.account_values()
            return [TextContent(
                type="text",
                text=f"Account Summary:\n{format_response(result)}"
            )]

        elif name == "ibkr_positions":
            result = client.positions()
            return [TextContent(
                type="text",
                text=f"Positions:\n{format_response(result)}"
            )]

        elif name == "ibkr_daily_ohlcv":
            result = client.daily_ohlcv()
            return [TextContent(
                type="text",
                text=f"Daily OHLCV Processing Result:\n{format_response(result)}"
            )]

        elif name == "ibkr_hourly_ohlcv":
            result = client.hourly_ohlcv()
            return [TextContent(
                type="text",
                text=f"Hourly OHLCV Processing Result:\n{format_response(result)}"
            )]

        elif name == "ibkr_contract_details":
            result = client.contract_details()
            return [TextContent(
                type="text",
                text=f"Contract Details Processing Result:\n{format_response(result)}"
            )]

        elif name == "ibkr_search_symbols":
            query = arguments.get("query", "")
            if not query:
                return [TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            result = client.find_symbols(query)
            return [TextContent(
                type="text",
                text=f"Symbol Search Results for '{query}':\n{format_response(result)}"
            )]

        elif name == "ibkr_contract_by_id":
            contract_id = arguments.get("contract_id")
            if contract_id is None:
                return [TextContent(
                    type="text",
                    text="Error: 'contract_id' parameter is required"
                )]
            check_ohlcv = arguments.get("check_ohlcv", False)
            result = client.get_contract_by_id(contract_id, check_ohlcv=check_ohlcv)
            return [TextContent(
                type="text",
                text=f"Contract Details for ID {contract_id}:\n{format_response(result)}"
            )]

        elif name == "ibkr_custom_ohlcv":
            symbols = arguments.get("symbols", [])
            if not symbols:
                return [TextContent(
                    type="text",
                    text="Error: 'symbols' parameter is required and must be non-empty"
                )]
            duration = arguments.get("duration", "7 D")
            bar_size = arguments.get("bar_size", "1 day")
            result = client.custom_ohlcv(
                symbols=symbols,
                duration_str=duration,
                bar_size_setting=bar_size,
            )
            return [TextContent(
                type="text",
                text=f"Custom OHLCV Result:\n{format_response(result)}"
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.exception(f"Error calling tool {name}")
        return handle_error(e)


async def run_server():
    """Run the MCP server."""
    logger.info("Starting IBKR MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
