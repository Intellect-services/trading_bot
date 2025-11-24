"""Trade model for tracking executed trades."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class Trade(BaseModel):
    """Trade model for tracking executed trades."""

    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_portfolio_symbol", "portfolio_id", "symbol"),
        Index("idx_executed_at", "executed_at"),
    )

    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    portfolio_id = Column(
        Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    price = Column(Numeric(15, 4), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    commission = Column(Numeric(10, 4), default=0)
    realized_pl = Column(Numeric(15, 2), nullable=True)  # Calculated on close
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="trades")
    portfolio = relationship("Portfolio", back_populates="trades")

    def to_dict(self) -> dict:
        """Convert trade to dictionary.

        Returns:
            Dictionary representation of trade
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "quantity": float(self.quantity) if self.quantity else None,
            "price": float(self.price) if self.price else None,
            "side": self.side,
            "commission": float(self.commission) if self.commission else None,
            "realized_pl": float(self.realized_pl) if self.realized_pl else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation of trade."""
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side})>"
