"""Order model for tracking trading orders."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class Order(BaseModel):
    """Order model for tracking trading orders."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_portfolio_symbol", "portfolio_id", "symbol"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
    )

    portfolio_id = Column(
        Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alpaca_order_id = Column(String(100), unique=True, nullable=True)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    filled_quantity = Column(Numeric(15, 4), default=0)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    type = Column(String(20), nullable=False)  # 'market', 'limit', 'stop', 'stop_limit'
    time_in_force = Column(String(10), nullable=True)  # 'day', 'gtc', 'ioc', 'fok'
    status = Column(
        String(20), nullable=False
    )  # 'pending', 'filled', 'partial', 'cancelled', 'rejected'
    limit_price = Column(Numeric(15, 4), nullable=True)
    stop_price = Column(Numeric(15, 4), nullable=True)
    filled_avg_price = Column(Numeric(15, 4), nullable=True)
    commission = Column(Numeric(10, 4), default=0)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="orders")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert order to dictionary.

        Returns:
            Dictionary representation of order
        """
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "alpaca_order_id": self.alpaca_order_id,
            "symbol": self.symbol,
            "quantity": float(self.quantity) if self.quantity else None,
            "filled_quantity": float(self.filled_quantity) if self.filled_quantity else None,
            "side": self.side,
            "type": self.type,
            "time_in_force": self.time_in_force,
            "status": self.status,
            "limit_price": float(self.limit_price) if self.limit_price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "filled_avg_price": float(self.filled_avg_price) if self.filled_avg_price else None,
            "commission": float(self.commission) if self.commission else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of order."""
        return f"<Order(id={self.id}, symbol={self.symbol}, status={self.status})>"
