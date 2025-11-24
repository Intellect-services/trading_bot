"""Position model for tracking open trading positions."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class Position(BaseModel):
    """Position model for tracking open positions."""

    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_portfolio_symbol", "portfolio_id", "symbol"),
        Index("idx_opened_at", "opened_at"),
    )

    portfolio_id = Column(
        Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    avg_entry_price = Column(Numeric(15, 4), nullable=False)
    current_price = Column(Numeric(15, 4), nullable=True)
    market_value = Column(Numeric(15, 2), nullable=True)
    unrealized_pl = Column(Numeric(15, 2), nullable=True)
    unrealized_pl_percent = Column(Numeric(10, 4), nullable=True)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    portfolio = relationship("Portfolio", back_populates="positions")

    def to_dict(self) -> dict:
        """Convert position to dictionary.

        Returns:
            Dictionary representation of position
        """
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "quantity": float(self.quantity) if self.quantity else None,
            "avg_entry_price": float(self.avg_entry_price) if self.avg_entry_price else None,
            "current_price": float(self.current_price) if self.current_price else None,
            "market_value": float(self.market_value) if self.market_value else None,
            "unrealized_pl": float(self.unrealized_pl) if self.unrealized_pl else None,
            "unrealized_pl_percent": float(self.unrealized_pl_percent)
            if self.unrealized_pl_percent
            else None,
            "side": self.side,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of position."""
        return f"<Position(id={self.id}, symbol={self.symbol}, qty={self.quantity})>"
