"""Portfolio snapshot model for tracking portfolio value over time."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class PortfolioSnapshot(BaseModel):
    """Portfolio snapshot model for historical portfolio values."""

    __tablename__ = "portfolio_snapshots"
    __table_args__ = (Index("idx_portfolio_time", "portfolio_id", "snapshot_at"),)

    portfolio_id = Column(
        Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_value = Column(Numeric(15, 2), nullable=False)
    cash_balance = Column(Numeric(15, 2), nullable=False)
    positions_value = Column(Numeric(15, 2), nullable=False)
    total_pl = Column(Numeric(15, 2), nullable=True)
    daily_pl = Column(Numeric(15, 2), nullable=True)
    snapshot_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    portfolio = relationship("Portfolio", back_populates="snapshots")

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary.

        Returns:
            Dictionary representation of snapshot
        """
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "total_value": float(self.total_value) if self.total_value else None,
            "cash_balance": float(self.cash_balance) if self.cash_balance else None,
            "positions_value": float(self.positions_value) if self.positions_value else None,
            "total_pl": float(self.total_pl) if self.total_pl else None,
            "daily_pl": float(self.daily_pl) if self.daily_pl else None,
            "snapshot_at": self.snapshot_at.isoformat() if self.snapshot_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation of snapshot."""
        return f"<PortfolioSnapshot(id={self.id}, portfolio_id={self.portfolio_id}, value={self.total_value})>"
