"""Security utilities for 1Password MCP server.

Handles vault allowlisting, field redaction, and rate limiting.
"""

import asyncio
import copy
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Sensitive field types that should be redacted in item listings
SENSITIVE_FIELD_TYPES = {
    "CONCEALED",
    "PASSWORD",
    "CREDIT_CARD_NUMBER",
    "CREDIT_CARD_VERIFICATION_NUMBER",
}

# Fields to always redact by ID pattern
SENSITIVE_FIELD_IDS = {
    "password",
    "credential",
    "secret",
    "cvv",
    "pin",
}


class VaultFilter:
    """Filters vault access based on allowlist."""

    def __init__(self, allowed_vaults: str | None = None):
        """Initialize with comma-separated vault names.

        Args:
            allowed_vaults: Comma-separated vault names (e.g., "AI,Development").
                           Defaults to "AI" if not specified.
        """
        raw = allowed_vaults or os.environ.get("OP_ALLOWED_VAULTS", "AI")
        self.allowed_vaults = {v.strip().lower() for v in raw.split(",") if v.strip()}
        logger.info(f"Vault allowlist: {self.allowed_vaults}")

    def is_allowed(self, vault_name: str) -> bool:
        """Check if a vault is in the allowlist."""
        return vault_name.lower() in self.allowed_vaults

    def filter_vaults(self, vaults: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter a list of vaults to only those allowed."""
        return [v for v in vaults if self.is_allowed(v.get("name", ""))]


class FieldRedactor:
    """Redacts sensitive fields in item data."""

    REDACTED = "[REDACTED]"

    def redact_field(self, field: dict[str, Any]) -> dict[str, Any]:
        """Redact a single field if it contains sensitive data."""
        field_type = field.get("field_type", "").upper()
        field_id = field.get("id", "").lower()

        # Check if this field type or ID should be redacted
        should_redact = (
            field_type in SENSITIVE_FIELD_TYPES or
            any(s in field_id for s in SENSITIVE_FIELD_IDS)
        )

        if should_redact and "value" in field:
            redacted = field.copy()
            redacted["value"] = self.REDACTED
            return redacted

        return field

    def redact_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Redact all sensitive fields in an item."""
        redacted = copy.deepcopy(item)

        if "fields" in redacted:
            redacted["fields"] = [
                self.redact_field(f) for f in redacted["fields"]
            ]

        return redacted


class RateLimiter:
    """Simple rate limiter for secret resolution.

    Enforces a minimum delay between op_resolve_secret calls to prevent
    rapid-fire credential harvesting while keeping UX smooth.
    """

    def __init__(self, min_delay_seconds: float = 1.0):
        """Initialize rate limiter.

        Args:
            min_delay_seconds: Minimum seconds between resolve calls.
        """
        self.min_delay = min_delay_seconds
        self._last_resolve_time: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if needed to respect rate limit."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_resolve_time

            if elapsed < self.min_delay and self._last_resolve_time > 0:
                wait_time = self.min_delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            self._last_resolve_time = time.monotonic()


def is_writes_enabled() -> bool:
    """Check if write operations are enabled."""
    return os.environ.get("OP_ENABLE_WRITES", "false").lower() in ("true", "1", "yes")
