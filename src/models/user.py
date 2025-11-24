"""User model for authentication."""

from datetime import datetime
from typing import Any

import bcrypt

from src.database import db


class User(db.Model):  # type: ignore[name-defined]
    """User model for storing user account information."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True, index=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default="trader", nullable=False)  # 'trader', 'admin', 'owner'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        password_bytes = password.encode("utf-8")
        hash_bytes = self.password_hash.encode("utf-8")
        return bool(bcrypt.checkpw(password_bytes, hash_bytes))

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        role: str = str(self.role)
        return role in ("admin", "owner")

    def is_trader(self) -> bool:
        """Check if user has trader role."""
        role: str = str(self.role)
        return role == "trader"

    def is_owner(self) -> bool:
        """Check if user has owner role."""
        role: str = str(self.role)
        return role == "owner"

    def can_trade(self) -> bool:
        """Check if user can trade (email verified and has credentials configured)."""
        if not bool(self.email_verified):
            return False
        # Check if user has credentials configured
        # Handle both single object and list (in case of relationship issues)
        from src.models.user_credentials import UserCredentials

        credentials = UserCredentials.get_by_user_id(self.id)
        if credentials:
            return bool(credentials.has_credentials() and credentials.is_active)
        return False

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:  # noqa: ARG002
        """Convert user object to dictionary.

        Args:
            include_sensitive: If True, include sensitive information like role.
        """
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar": self.avatar
            or f"https://ui-avatars.com/api/?name={self.name.replace(' ', '+')}&background=667eea&color=fff",
            "email_verified": self.email_verified,
            "role": self.role,
            "can_trade": self.can_trade(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        email: str = str(self.email)
        role: str = str(self.role)
        verified: bool = bool(self.email_verified)
        return f"<User {email} role={role} verified={verified}>"
