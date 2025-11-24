"""User model for authentication and profile management."""

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, String

from src.infrastructure.base_model import BaseModel


class User(BaseModel):
    """User model for storing user account information."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        """Hash and set the user's password.

        Args:
            password: Plain text password to hash
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")  # type: ignore[assignment]

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode("utf-8")
        hash_bytes = self.password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user object to dictionary.

        Args:
            include_sensitive: Whether to include sensitive fields

        Returns:
            Dictionary representation of user
        """
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar": self.avatar
            or f"https://ui-avatars.com/api/?name={self.name.replace(' ', '+')}&background=667eea&color=fff",
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash

        return data

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
