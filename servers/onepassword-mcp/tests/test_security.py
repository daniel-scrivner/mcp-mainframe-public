"""Tests for security utilities."""

import asyncio
import time
import pytest

from onepassword_mcp.security import (
    FieldRedactor,
    RateLimiter,
    VaultFilter,
)


class TestVaultFilter:
    """Tests for VaultFilter."""

    def test_default_allows_ai_vault(self):
        """Default filter allows 'AI' vault."""
        filter = VaultFilter()
        assert filter.is_allowed("AI")
        assert filter.is_allowed("ai")
        assert filter.is_allowed("Ai")

    def test_default_blocks_other_vaults(self):
        """Default filter blocks other vaults."""
        filter = VaultFilter()
        assert not filter.is_allowed("Personal")
        assert not filter.is_allowed("Work")

    def test_custom_allowlist(self):
        """Custom allowlist works correctly."""
        filter = VaultFilter("Dev,Staging,Production")
        assert filter.is_allowed("Dev")
        assert filter.is_allowed("staging")
        assert filter.is_allowed("PRODUCTION")
        assert not filter.is_allowed("AI")

    def test_filter_vaults(self):
        """filter_vaults only returns allowed vaults."""
        filter = VaultFilter("AI,Dev")
        vaults = [
            {"id": "1", "name": "AI"},
            {"id": "2", "name": "Personal"},
            {"id": "3", "name": "Dev"},
        ]
        filtered = filter.filter_vaults(vaults)
        assert len(filtered) == 2
        assert filtered[0]["name"] == "AI"
        assert filtered[1]["name"] == "Dev"


class TestFieldRedactor:
    """Tests for FieldRedactor."""

    def test_redacts_concealed_fields(self):
        """Concealed fields are redacted."""
        redactor = FieldRedactor()
        field = {
            "id": "password",
            "field_type": "CONCEALED",
            "value": "secret123",
        }
        result = redactor.redact_field(field)
        assert result["value"] == "[REDACTED]"

    def test_preserves_normal_fields(self):
        """Normal fields are not redacted."""
        redactor = FieldRedactor()
        field = {
            "id": "username",
            "field_type": "TEXT",
            "value": "john@example.com",
        }
        result = redactor.redact_field(field)
        assert result["value"] == "john@example.com"

    def test_redacts_by_field_id(self):
        """Fields with sensitive IDs are redacted."""
        redactor = FieldRedactor()
        field = {
            "id": "api_secret_key",
            "field_type": "TEXT",
            "value": "sk-123456",
        }
        result = redactor.redact_field(field)
        assert result["value"] == "[REDACTED]"

    def test_redact_item(self):
        """redact_item processes all fields."""
        redactor = FieldRedactor()
        item = {
            "id": "item1",
            "title": "Test",
            "fields": [
                {"id": "username", "field_type": "TEXT", "value": "user"},
                {"id": "password", "field_type": "CONCEALED", "value": "pass"},
            ],
        }
        result = redactor.redact_item(item)
        assert result["fields"][0]["value"] == "user"
        assert result["fields"][1]["value"] == "[REDACTED]"


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_first_call_no_delay(self):
        """First call should not be delayed."""
        limiter = RateLimiter(min_delay_seconds=1.0)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_second_call_delayed(self):
        """Second call should be delayed."""
        limiter = RateLimiter(min_delay_seconds=0.5)
        await limiter.acquire()
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.4  # Should wait ~0.5 seconds

    @pytest.mark.asyncio
    async def test_no_delay_after_waiting(self):
        """No delay if enough time has passed."""
        limiter = RateLimiter(min_delay_seconds=0.1)
        await limiter.acquire()
        await asyncio.sleep(0.15)  # Wait longer than min_delay
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05  # Should be nearly instant
