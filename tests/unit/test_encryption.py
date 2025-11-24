"""Unit tests for encryption utilities."""

import warnings

import pytest

from src.utils.encryption import (
    decrypt_value,
    encrypt_value,
    generate_encryption_key,
    get_encryption_key,
)


class TestEncryption:
    """Test encryption utilities."""

    def test_generate_key(self) -> None:
        """Test key generation."""
        key = generate_encryption_key()
        assert key is not None
        assert len(key) == 44  # Base64 encoded 32-byte key

    def test_encrypt_decrypt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test encryption and decryption."""
        key = generate_encryption_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key)
        original_value = "sensitive_data_123"

        encrypted = encrypt_value(original_value)
        assert encrypted != original_value
        assert encrypted is not None

        decrypted = decrypt_value(encrypted)
        assert decrypted == original_value

    def test_different_keys_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that decryption with wrong key fails."""
        key1 = generate_encryption_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key1)
        original_value = "sensitive_data"
        encrypted = encrypt_value(original_value)

        key2 = generate_encryption_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key2)
        with pytest.raises(ValueError):
            decrypt_value(encrypted)

    def test_get_encryption_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting encryption key from environment."""
        test_key = generate_encryption_key()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)

        key = get_encryption_key()
        assert key == test_key.encode("utf-8")

    def test_missing_key_warns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure missing key path emits warning and returns generated value."""
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            key_bytes = get_encryption_key()

        assert key_bytes
        assert caught
        assert "ENCRYPTION_KEY not set" in str(caught[-1].message)
