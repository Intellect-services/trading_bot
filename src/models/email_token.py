"""Email token model for email verification and password reset."""

import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from src.database import db

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model as _ModelBase
else:
    _ModelBase = db.Model


class TokenType(str, Enum):
    """Allowed token types for email operations."""

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"  # nosec B105


class EmailToken(_ModelBase):
    """Model for storing email verification and password reset tokens."""

    __tablename__ = "email_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(50), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", backref="email_tokens")

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token.

        Returns:
            URL-safe random token string.
        """
        return secrets.token_urlsafe(32)

    @classmethod
    def create_verification_token(cls, user_id: int, expiration_hours: int = 24) -> "EmailToken":
        """Create a new email verification token.

        Args:
            user_id: ID of the user.
            expiration_hours: Hours until token expires (default: 24).

        Returns:
            New EmailToken instance.
        """
        token_data = {
            "user_id": user_id,
            "token": EmailToken.generate_token(),
            "token_type": TokenType.VERIFICATION.value,
            "expires_at": datetime.utcnow() + timedelta(hours=expiration_hours),
        }
        token_obj = cast("Any", cls)(**token_data)
        return cast("EmailToken", token_obj)

    @classmethod
    def create_password_reset_token(cls, user_id: int, expiration_hours: int = 1) -> "EmailToken":
        """Create a new password reset token.

        Args:
            user_id: ID of the user.
            expiration_hours: Hours until token expires (default: 1).

        Returns:
            New EmailToken instance.
        """
        token_data = {
            "user_id": user_id,
            "token": EmailToken.generate_token(),
            "token_type": TokenType.PASSWORD_RESET.value,
            "expires_at": datetime.utcnow() + timedelta(hours=expiration_hours),
        }
        token_obj = cast("Any", cls)(**token_data)
        return cast("EmailToken", token_obj)

    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired).

        Returns:
            True if token is valid, False otherwise.
        """
        if self.used_at is not None:
            return False
        return not datetime.utcnow() > self.expires_at

    def mark_as_used(self) -> None:
        """Mark token as used."""
        self.used_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert token to dictionary.

        Returns:
            Dictionary representation of token (without the actual token value for security).
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<EmailToken user_id={self.user_id} type={self.token_type} valid={self.is_valid()}>"
