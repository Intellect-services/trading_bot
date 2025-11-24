"""Strategy model for trading strategy configurations."""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class Strategy(BaseModel):
    """Strategy model for storing trading strategy configurations."""

    __tablename__ = "strategies"
    __table_args__ = (Index("idx_user_type", "user_id", "type"),)

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(
        String(50), nullable=False
    )  # 'moving_average', 'mean_reversion', 'momentum', etc.
    parameters = Column(JSON, nullable=False)  # Strategy-specific parameters
    risk_parameters = Column(JSON, nullable=True)  # Stop loss, position sizing, max drawdown, etc.
    is_active = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", backref="strategies")
    signals = relationship("Signal", back_populates="strategy", cascade="all, delete-orphan")
    backtest_results = relationship(
        "BacktestResult", back_populates="strategy", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Convert strategy to dictionary.

        Returns:
            Dictionary representation of strategy
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "parameters": self.parameters,
            "risk_parameters": self.risk_parameters,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of strategy."""
        return f"<Strategy(id={self.id}, name={self.name}, type={self.type})>"
