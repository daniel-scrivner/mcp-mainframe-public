"""Tests for 1Password client wrapper."""

import pytest
from unittest.mock import AsyncMock, patch

from onepassword_mcp.client import OnePasswordClient, OnePasswordClientError


class TestOnePasswordClientInit:
    """Tests for OnePasswordClient initialization."""

    def test_requires_token(self):
        """Client requires service account token."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(OnePasswordClientError) as exc_info:
                OnePasswordClient()
            assert "OP_SERVICE_ACCOUNT_TOKEN" in str(exc_info.value)

    def test_accepts_token_from_env(self):
        """Client accepts token from environment variable."""
        with patch.dict("os.environ", {"OP_SERVICE_ACCOUNT_TOKEN": "test_token"}):
            client = OnePasswordClient()
            assert client._token == "test_token"

    def test_accepts_token_as_argument(self):
        """Client accepts token as constructor argument."""
        client = OnePasswordClient(service_account_token="direct_token")
        assert client._token == "direct_token"


class TestVaultFiltering:
    """Tests for vault allowlist enforcement in client."""

    @pytest.fixture
    def client(self):
        """Create client with test token."""
        return OnePasswordClient(
            service_account_token="test_token",
            allowed_vaults="AI,Development",
        )

    @pytest.mark.asyncio
    async def test_list_vaults_filters_by_allowlist(self, client):
        """list_vaults only returns allowed vaults."""
        # The vault filter is already tested in test_security.py.
        # Here we verify the client's filter is configured correctly.
        assert client._vault_filter.is_allowed("AI")
        assert client._vault_filter.is_allowed("Development")
        assert not client._vault_filter.is_allowed("Personal")
        assert not client._vault_filter.is_allowed("Work")

    @pytest.mark.asyncio
    async def test_list_items_blocks_disallowed_vault(self, client):
        """list_items raises error for non-allowed vault."""
        # Set up cache with known vault
        client._vault_cache = {"vault_123": "Personal"}

        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.list_items("vault_123")

        assert "not in the allowed vaults list" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_item_blocks_disallowed_vault(self, client):
        """get_item raises error for non-allowed vault."""
        client._vault_cache = {"vault_456": "Work"}

        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.get_item("vault_456", "item_123")

        assert "not in the allowed vaults list" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resolve_secret_blocks_disallowed_vault(self, client):
        """resolve_secret raises error for non-allowed vault."""
        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.resolve_secret("op://Personal/item/password")

        assert "not in the allowed vaults list" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resolve_secret_allows_permitted_vault(self, client):
        """resolve_secret works for allowed vault."""
        mock_sdk = AsyncMock()
        mock_sdk.secrets.resolve = AsyncMock(return_value="secret_value")
        client._client = mock_sdk

        result = await client.resolve_secret("op://AI/item/password")
        assert result == "secret_value"

    @pytest.mark.asyncio
    async def test_get_otp_blocks_disallowed_vault(self, client):
        """get_otp raises error for non-allowed vault."""
        client._vault_cache = {"vault_789": "Personal"}

        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.get_otp("vault_789", "item_123")

        assert "not in the allowed vaults list" in str(exc_info.value)


class TestSecretReferenceValidation:
    """Tests for secret reference format validation."""

    @pytest.fixture
    def client(self):
        """Create client with test token."""
        return OnePasswordClient(
            service_account_token="test_token",
            allowed_vaults="AI",
        )

    @pytest.mark.asyncio
    async def test_rejects_invalid_prefix(self, client):
        """Secret reference must start with op://."""
        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.resolve_secret("vault/item/field")

        assert "must start with 'op://'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rejects_too_few_parts(self, client):
        """Secret reference must have vault/item/field format."""
        with pytest.raises(OnePasswordClientError) as exc_info:
            await client.resolve_secret("op://vault/item")

        assert "Invalid secret reference format" in str(exc_info.value)
