"""Portfolio model for managing trading portfolios."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class Portfolio(BaseModel):
    """Portfolio model for managing user trading accounts."""

    __tablename__ = "portfolios"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    initial_capital = Column(Numeric(15, 2), nullable=False)
    current_value = Column(Numeric(15, 2), nullable=True)
    cash_balance = Column(Numeric(15, 2), nullable=True)
    buying_power = Column(Numeric(15, 2), nullable=True)
    is_paper = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", backref="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship(
        "PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Convert portfolio to dictionary.

        Returns:
            Dictionary representation of portfolio
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "initial_capital": float(self.initial_capital) if self.initial_capital else None,
            "current_value": float(self.current_value) if self.current_value else None,
            "cash_balance": float(self.cash_balance) if self.cash_balance else None,
            "buying_power": float(self.buying_power) if self.buying_power else None,
            "is_paper": self.is_paper,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of portfolio."""
        return f"<Portfolio(id={self.id}, name={self.name}, user_id={self.user_id})>"
