"""Audit log model for tracking all system changes."""

from sqlalchemy import JSON, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class AuditLog(BaseModel):
    """Audit log model for tracking all changes in the system."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_user_entity", "user_id", "entity_type"),
        Index("idx_audit_created_at", "created_at"),
    )

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    entity_type = Column(String(50), nullable=False)  # 'order', 'trade', 'position', 'user', etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # 'create', 'update', 'delete'
    changes = Column(JSON, nullable=True)  # Before/after values
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6

    # Relationship
    user = relationship("User", backref="audit_logs")

    def to_dict(self) -> dict:
        """Convert audit log object to dictionary.

        Returns:
            Dictionary representation of audit log
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation of the audit log."""
        return f"<AuditLog(id={self.id}, entity_type={self.entity_type}, action={self.action})>"
