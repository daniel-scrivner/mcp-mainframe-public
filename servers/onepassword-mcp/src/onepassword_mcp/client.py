"""1Password SDK client wrapper.

Wraps the official 1Password SDK with vault filtering and error handling.
"""

import logging
import os
from typing import Any

from onepassword import Client

from .security import FieldRedactor, VaultFilter

logger = logging.getLogger(__name__)


class OnePasswordClientError(Exception):
    """Error from 1Password client operations."""

    pass


class OnePasswordClient:
    """Wrapper around 1Password SDK with security filtering."""

    def __init__(
        self,
        service_account_token: str | None = None,
        allowed_vaults: str | None = None,
    ):
        """Initialize the 1Password client.

        Args:
            service_account_token: 1Password service account token.
                                  Falls back to OP_SERVICE_ACCOUNT_TOKEN env var.
            allowed_vaults: Comma-separated vault names to allow access to.
                           Falls back to OP_ALLOWED_VAULTS env var (default: "AI").
        """
        # SECURITY: Token is stored in memory for SDK authentication.
        # The service account token is scoped to specific vaults at creation time
        # in 1Password, and we further restrict access via OP_ALLOWED_VAULTS.
        self._token = service_account_token or os.environ.get("OP_SERVICE_ACCOUNT_TOKEN")
        if not self._token:
            raise OnePasswordClientError(
                "OP_SERVICE_ACCOUNT_TOKEN environment variable is required"
            )

        self._client: Client | None = None
        self._vault_filter = VaultFilter(allowed_vaults)
        self._field_redactor = FieldRedactor()

        # Cache vault ID -> name mapping for allowlist checks
        self._vault_cache: dict[str, str] = {}

    async def _get_client(self) -> Client:
        """Get or create the authenticated 1Password client."""
        if self._client is None:
            try:
                self._client = await Client.authenticate(
                    auth=self._token,
                    integration_name="onepassword-mcp",
                    integration_version="0.1.0",
                )
                logger.info("1Password client authenticated successfully")
            except Exception as e:
                raise OnePasswordClientError(f"Failed to authenticate: {e}") from e
        return self._client

    async def _refresh_vault_cache(self) -> None:
        """Refresh the vault ID -> name cache."""
        client = await self._get_client()
        self._vault_cache = {}
        async for vault in await client.vaults.list_all():
            self._vault_cache[vault.id] = vault.name

    async def _is_vault_allowed(self, vault_id: str) -> bool:
        """Check if a vault ID is in the allowlist."""
        if vault_id not in self._vault_cache:
            await self._refresh_vault_cache()

        vault_name = self._vault_cache.get(vault_id, "")
        return self._vault_filter.is_allowed(vault_name)

    async def list_vaults(self) -> list[dict[str, Any]]:
        """List all accessible vaults (filtered by allowlist).

        Returns:
            List of vault dictionaries with id and name.
        """
        client = await self._get_client()
        vaults = []

        try:
            async for vault in await client.vaults.list_all():
                if self._vault_filter.is_allowed(vault.name):
                    vaults.append({
                        "id": vault.id,
                        "name": vault.name,
                    })
                    # Update cache
                    self._vault_cache[vault.id] = vault.name
        except Exception as e:
            raise OnePasswordClientError(f"Failed to list vaults: {e}") from e

        return vaults

    async def list_items(
        self,
        vault_id: str,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """List items in a vault (filtered by allowlist).

        Args:
            vault_id: The vault ID to list items from.
            category: Optional category filter (e.g., "LOGIN", "PASSWORD").

        Returns:
            List of item dictionaries with id, title, and category.
        """
        if not await self._is_vault_allowed(vault_id):
            vault_name = self._vault_cache.get(vault_id, vault_id)
            raise OnePasswordClientError(
                f"Vault '{vault_name}' (ID: {vault_id}) is not in the allowed vaults list"
            )

        client = await self._get_client()
        items = []

        try:
            async for item in await client.items.list_all(vault_id):
                # Apply category filter if specified
                if category and item.category.name.upper() != category.upper():
                    continue

                items.append({
                    "id": item.id,
                    "title": item.title,
                    "category": item.category.name,
                    "vault_id": vault_id,
                })
        except Exception as e:
            raise OnePasswordClientError(f"Failed to list items: {e}") from e

        return items

    async def get_item(
        self,
        vault_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """Get item details (with sensitive fields redacted).

        Args:
            vault_id: The vault ID containing the item.
            item_id: The item ID to retrieve.

        Returns:
            Item dictionary with redacted sensitive fields.
        """
        if not await self._is_vault_allowed(vault_id):
            vault_name = self._vault_cache.get(vault_id, vault_id)
            raise OnePasswordClientError(
                f"Vault '{vault_name}' (ID: {vault_id}) is not in the allowed vaults list"
            )

        client = await self._get_client()

        try:
            item = await client.items.get(vault_id, item_id)

            # Convert to dict and redact
            item_dict = {
                "id": item.id,
                "title": item.title,
                "category": item.category.name,
                "vault_id": vault_id,
                "fields": [],
                "tags": list(item.tags) if item.tags else [],
                "urls": [],
            }

            # Add fields (redacted)
            if item.fields:
                for field in item.fields:
                    field_dict = {
                        "id": field.id,
                        "title": field.title,
                        "field_type": field.field_type.name if field.field_type else "TEXT",
                        "value": field.value if field.value else "",
                    }
                    item_dict["fields"].append(
                        self._field_redactor.redact_field(field_dict)
                    )

            # Add URLs
            if item.urls:
                for url in item.urls:
                    item_dict["urls"].append({
                        "url": url.href,
                        "primary": url.primary,
                    })

            return item_dict

        except Exception as e:
            raise OnePasswordClientError(f"Failed to get item: {e}") from e

    async def resolve_secret(self, secret_reference: str) -> str:
        """Resolve a secret reference to its value.

        Args:
            secret_reference: Secret reference in format "op://vault/item/field"
                             or "op://vault/item/section/field".

        Returns:
            The secret value.
        """
        # Validate reference format
        if not secret_reference.startswith("op://"):
            raise OnePasswordClientError(
                "Secret reference must start with 'op://'"
            )

        # Extract vault from reference for allowlist check
        parts = secret_reference[5:].split("/")
        if len(parts) < 3:
            raise OnePasswordClientError(
                "Invalid secret reference format. Use: op://vault/item/field"
            )

        vault_name = parts[0]
        if not self._vault_filter.is_allowed(vault_name):
            raise OnePasswordClientError(
                f"Vault '{vault_name}' is not in the allowed vaults list"
            )

        client = await self._get_client()

        try:
            return await client.secrets.resolve(secret_reference)
        except Exception as e:
            raise OnePasswordClientError(f"Failed to resolve secret: {e}") from e

    async def get_otp(
        self,
        vault_id: str,
        item_id: str,
        field_id: str | None = None,
    ) -> str:
        """Get the current OTP code for an item.

        Args:
            vault_id: The vault ID containing the item.
            item_id: The item ID with TOTP field.
            field_id: Optional field ID if item has multiple TOTP fields.

        Returns:
            The current OTP code.
        """
        if not await self._is_vault_allowed(vault_id):
            vault_name = self._vault_cache.get(vault_id, vault_id)
            raise OnePasswordClientError(
                f"Vault '{vault_name}' (ID: {vault_id}) is not in the allowed vaults list"
            )

        # Get vault name for reference - must have valid name, not ID
        if vault_id not in self._vault_cache:
            await self._refresh_vault_cache()

        if vault_id not in self._vault_cache:
            raise OnePasswordClientError(
                f"Unable to determine vault name for ID '{vault_id}' when building OTP reference"
            )

        vault_name = self._vault_cache[vault_id]

        # Build OTP reference
        field = field_id or "one-time password"
        reference = f"op://{vault_name}/{item_id}/{field}?attribute=otp"

        client = await self._get_client()

        try:
            return await client.secrets.resolve(reference)
        except Exception as e:
            raise OnePasswordClientError(f"Failed to get OTP: {e}") from e
