"""Encryption utility for securing sensitive data like API credentials."""

import os
from typing import Any, cast

from cryptography.fernet import Fernet


def generate_encryption_key() -> str:
    """Generate a new encryption key.

    Returns:
        Base64-encoded encryption key suitable for Fernet.
    """
    generated: Any = Fernet.generate_key()
    return cast("bytes", generated).decode("utf-8")


def get_encryption_key() -> bytes:
    """Get or generate the encryption key from environment variable.

    Returns:
        Encryption key as bytes.

    Raises:
        ValueError: If ENCRYPTION_KEY is not set and cannot be generated.
    """
    key_str: str | None = os.getenv("ENCRYPTION_KEY")

    if not key_str:
        # Try to generate and warn (in production, this should be set)
        import warnings

        warnings.warn(
            "ENCRYPTION_KEY not set. Generating a new key. "
            "This key will be lost on restart. Set ENCRYPTION_KEY in environment.",
            UserWarning,
            stacklevel=2,
        )
        key_str = generate_encryption_key()

    if key_str is None:
        raise ValueError("ENCRYPTION_KEY should be configured before encrypting data.")
    return key_str.encode("utf-8")


def get_cipher() -> Fernet:
    """Get Fernet cipher instance for encryption/decryption.

    Returns:
        Fernet cipher instance.
    """
    key = get_encryption_key()
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a string value.

    Args:
        value: Plain text string to encrypt.

    Returns:
        Encrypted string (base64-encoded).

    Raises:
        ValueError: If value is None or empty.
    """
    if not value:
        raise ValueError("Cannot encrypt empty value")

    cipher = get_cipher()
    encrypted_any: Any = cipher.encrypt(value.encode("utf-8"))
    encrypted_bytes = cast("bytes", encrypted_any)
    return encrypted_bytes.decode("utf-8")


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string value.

    Args:
        encrypted_value: Encrypted string (base64-encoded).

    Returns:
        Decrypted plain text string.

    Raises:
        ValueError: If decryption fails (invalid key or corrupted data).
    """
    if not encrypted_value:
        raise ValueError("Cannot decrypt empty value")

    try:
        cipher = get_cipher()
        decrypted_any: Any = cipher.decrypt(encrypted_value.encode("utf-8"))
        decrypted_bytes = cast("bytes", decrypted_any)
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e!s}")
