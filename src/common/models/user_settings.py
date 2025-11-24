"""User settings model for storing user preferences and configuration."""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class UserSettings(BaseModel):
    """User settings model for storing user-specific configuration."""

    __tablename__ = "user_settings"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_settings_user_key"),)

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=True)

    # Relationship
    user = relationship("User", backref="settings")

    def to_dict(self) -> dict:
        """Convert settings object to dictionary.

        Returns:
            Dictionary representation of settings
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of the settings."""
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, key={self.key})>"
