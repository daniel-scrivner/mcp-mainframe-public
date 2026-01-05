"""
1Password MCP Server - Access credentials using official SDK.

This MCP server provides Claude Code with secure access to 1Password
credentials via the official onepassword-sdk-python package.

Usage:
    # Run as standalone server
    python -m onepassword_mcp.server

    # Or via the installed script
    onepassword-mcp
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import OnePasswordClient, OnePasswordClientError
from .security import RateLimiter

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("OP_LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("onepassword-mcp")

# Lazy-initialized client and rate limiter
_op_client: OnePasswordClient | None = None
_rate_limiter: RateLimiter | None = None


def get_client() -> OnePasswordClient:
    """Get or create the 1Password client."""
    global _op_client
    if _op_client is None:
        _op_client = OnePasswordClient()
    return _op_client


def get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter for secret resolution."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(min_delay_seconds=1.0)
    return _rate_limiter


def format_response(data: Any) -> str:
    """Format response data as readable JSON."""
    return json.dumps(data, indent=2, default=str)


def handle_error(error: Exception) -> list[TextContent]:
    """Handle errors and return appropriate MCP response."""
    if isinstance(error, OnePasswordClientError):
        return [
            TextContent(
                type="text",
                text=f"1Password error: {error}",
            )
        ]
    else:
        logger.error("Unexpected error: %s", error, exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Unexpected error: {error}",
            )
        ]


# =============================================================================
# Tool Definitions
# =============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available 1Password tools."""
    tools = [
        Tool(
            name="op_list_vaults",
            description="List all accessible 1Password vaults (filtered by allowlist)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="op_list_items",
            description="List items in a 1Password vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_id": {
                        "type": "string",
                        "description": "The vault ID to list items from",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g., LOGIN, PASSWORD, API_CREDENTIAL)",
                    },
                },
                "required": ["vault_id"],
            },
        ),
        Tool(
            name="op_get_item",
            description="Get item details from 1Password (sensitive fields redacted)",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_id": {
                        "type": "string",
                        "description": "The vault ID containing the item",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "The item ID to retrieve",
                    },
                },
                "required": ["vault_id", "item_id"],
            },
        ),
        Tool(
            name="op_resolve_secret",
            description="Resolve a secret reference to get its value. Use format: op://vault/item/field",
            inputSchema={
                "type": "object",
                "properties": {
                    "secret_reference": {
                        "type": "string",
                        "description": "Secret reference (e.g., op://AI/GitHub/password)",
                    },
                },
                "required": ["secret_reference"],
            },
        ),
        Tool(
            name="op_get_otp",
            description="Get the current TOTP code for an item",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_id": {
                        "type": "string",
                        "description": "The vault ID containing the item",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "The item ID with TOTP field",
                    },
                    "field_id": {
                        "type": "string",
                        "description": "Optional field ID if item has multiple TOTP fields",
                    },
                },
                "required": ["vault_id", "item_id"],
            },
        ),
    ]

    # Note: Write tools (op_create_item, op_archive_item, op_generate_password)
    # are not exposed until fully implemented. The handlers exist as stubs
    # but are not advertised in the tool list. When implementing, add them
    # here conditionally on is_writes_enabled().

    return tools


# =============================================================================
# Tool Handlers
# =============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool call: {name}")

    try:
        if name == "op_list_vaults":
            return await handle_list_vaults()
        elif name == "op_list_items":
            return await handle_list_items(arguments)
        elif name == "op_get_item":
            return await handle_get_item(arguments)
        elif name == "op_resolve_secret":
            return await handle_resolve_secret(arguments)
        elif name == "op_get_otp":
            return await handle_get_otp(arguments)
        # Write tools are not exposed in list_tools() until implemented.
        # When implementing, uncomment these handlers:
        # elif name == "op_create_item" and is_writes_enabled():
        #     return await handle_create_item(arguments)
        # elif name == "op_archive_item" and is_writes_enabled():
        #     return await handle_archive_item(arguments)
        # elif name == "op_generate_password" and is_writes_enabled():
        #     return await handle_generate_password(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]
    except Exception as e:
        return handle_error(e)


async def handle_list_vaults() -> list[TextContent]:
    """Handle op_list_vaults tool."""
    client = get_client()
    vaults = await client.list_vaults()

    return [
        TextContent(
            type="text",
            text=format_response({
                "vaults": vaults,
                "count": len(vaults),
            }),
        )
    ]


async def handle_list_items(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_list_items tool."""
    vault_id = arguments.get("vault_id")
    category = arguments.get("category")

    if not vault_id:
        return [TextContent(type="text", text="Error: vault_id is required")]

    client = get_client()
    items = await client.list_items(vault_id, category)

    return [
        TextContent(
            type="text",
            text=format_response({
                "items": items,
                "count": len(items),
                "vault_id": vault_id,
            }),
        )
    ]


async def handle_get_item(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_get_item tool."""
    vault_id = arguments.get("vault_id")
    item_id = arguments.get("item_id")

    if not vault_id or not item_id:
        return [TextContent(type="text", text="Error: vault_id and item_id are required")]

    client = get_client()
    item = await client.get_item(vault_id, item_id)

    return [
        TextContent(
            type="text",
            text=format_response(item),
        )
    ]


async def handle_resolve_secret(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_resolve_secret tool."""
    secret_reference = arguments.get("secret_reference")

    if not secret_reference:
        return [TextContent(type="text", text="Error: secret_reference is required")]

    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    await rate_limiter.acquire()

    client = get_client()
    secret = await client.resolve_secret(secret_reference)

    return [
        TextContent(
            type="text",
            text=secret,
        )
    ]


async def handle_get_otp(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_get_otp tool."""
    vault_id = arguments.get("vault_id")
    item_id = arguments.get("item_id")
    field_id = arguments.get("field_id")

    if not vault_id or not item_id:
        return [TextContent(type="text", text="Error: vault_id and item_id are required")]

    client = get_client()
    otp = await client.get_otp(vault_id, item_id, field_id)

    return [
        TextContent(
            type="text",
            text=otp,
        )
    ]


async def handle_create_item(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_create_item tool."""
    # TODO: Implement create_item when write support is needed
    return [
        TextContent(
            type="text",
            text="Error: op_create_item is not yet implemented",
        )
    ]


async def handle_archive_item(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_archive_item tool."""
    # TODO: Implement archive_item when write support is needed
    return [
        TextContent(
            type="text",
            text="Error: op_archive_item is not yet implemented",
        )
    ]


async def handle_generate_password(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle op_generate_password tool."""
    # TODO: Implement generate_password when write support is needed
    return [
        TextContent(
            type="text",
            text="Error: op_generate_password is not yet implemented",
        )
    ]


# =============================================================================
# Main Entry Point
# =============================================================================


async def run_server() -> None:
    """Run the MCP server."""
    logger.info("Starting 1Password MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
