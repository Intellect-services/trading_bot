"""User credentials model for storing encrypted Alpaca API credentials."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.database import db
from src.utils.encryption import decrypt_value, encrypt_value

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model as _ModelBase
else:
    _ModelBase = db.Model


class UserCredentials(_ModelBase):
    """Model for storing encrypted Alpaca API credentials per user."""

    __tablename__ = "user_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    alpaca_api_key_encrypted = db.Column(db.Text, nullable=True)
    alpaca_secret_key_encrypted = db.Column(db.Text, nullable=True)
    trading_mode = db.Column(db.String(20), default="paper", nullable=False)  # 'paper' or 'live'
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    last_verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    user = db.relationship("User", backref="credentials", uselist=False)

    @classmethod
    def get_by_user_id(cls, user_id: int) -> "UserCredentials | None":
        """Retrieve credentials for a given user."""
        result: UserCredentials | None = db.session.query(cls).filter_by(user_id=user_id).first()
        return result

    def set_credentials(self, api_key: str, secret_key: str, trading_mode: str = "paper") -> None:
        """Encrypt and store Alpaca credentials.

        Args:
            api_key: Alpaca API key (plain text).
            secret_key: Alpaca secret key (plain text).
            trading_mode: Trading mode ('paper' or 'live').
        """
        if not api_key or not secret_key:
            raise ValueError("API key and secret key are required")

        self.alpaca_api_key_encrypted = encrypt_value(api_key)
        self.alpaca_secret_key_encrypted = encrypt_value(secret_key)
        self.trading_mode = trading_mode
        self.updated_at = datetime.utcnow()

    def get_api_key(self) -> str:
        """Decrypt and return the Alpaca API key.

        Returns:
            Decrypted API key.

        Raises:
            ValueError: If credentials are not set or decryption fails.
        """
        if not self.alpaca_api_key_encrypted:
            raise ValueError("API key not configured")
        return decrypt_value(self.alpaca_api_key_encrypted)

    def get_secret_key(self) -> str:
        """Decrypt and return the Alpaca secret key.

        Returns:
            Decrypted secret key.

        Raises:
            ValueError: If credentials are not set or decryption fails.
        """
        if not self.alpaca_secret_key_encrypted:
            raise ValueError("Secret key not configured")
        return decrypt_value(self.alpaca_secret_key_encrypted)

    def has_credentials(self) -> bool:
        """Check if user has configured credentials.

        Returns:
            True if both API key and secret key are set.
        """
        return bool(self.alpaca_api_key_encrypted and self.alpaca_secret_key_encrypted)

    def mark_verified(self) -> None:
        """Mark credentials as verified and active."""
        self.is_active = True
        self.last_verified_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert credentials to dictionary.

        Args:
            include_secrets: If True, include decrypted credentials (use with caution).

        Returns:
            Dictionary representation of credentials.
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "trading_mode": self.trading_mode,
            "is_active": self.is_active,
            "has_credentials": self.has_credentials(),
            "last_verified_at": self.last_verified_at.isoformat()
            if self.last_verified_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_secrets and self.has_credentials():
            data["alpaca_api_key"] = self.get_api_key()
            data["alpaca_secret_key"] = self.get_secret_key()

        return data

    def __repr__(self) -> str:
        user_id: int = int(self.user_id)
        mode: str = str(self.trading_mode)
        active: bool = bool(self.is_active)
        return f"<UserCredentials user_id={user_id} mode={mode} active={active}>"
