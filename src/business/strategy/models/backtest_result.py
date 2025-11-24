"""Backtest result model for strategy performance tracking."""

from sqlalchemy import JSON, Column, Date, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import relationship

from src.infrastructure.base_model import BaseModel


class BacktestResult(BaseModel):
    """Backtest result model for tracking strategy performance."""

    __tablename__ = "backtest_results"
    __table_args__ = (Index("idx_strategy_date", "strategy_id", "end_date"),)

    strategy_id = Column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(15, 2), nullable=False)
    final_value = Column(Numeric(15, 2), nullable=False)
    total_return = Column(Numeric(10, 4), nullable=True)  # Percentage
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)  # Percentage
    win_rate = Column(Numeric(10, 4), nullable=True)  # Percentage
    total_trades = Column(Integer, nullable=True)
    metrics = Column(JSON, nullable=True)  # Additional performance metrics

    # Relationship
    strategy = relationship("Strategy", back_populates="backtest_results")

    def to_dict(self) -> dict:
        """Convert backtest result to dictionary.

        Returns:
            Dictionary representation of backtest result
        """
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_capital": float(self.initial_capital) if self.initial_capital else None,
            "final_value": float(self.final_value) if self.final_value else None,
            "total_return": float(self.total_return) if self.total_return else None,
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else None,
            "win_rate": float(self.win_rate) if self.win_rate else None,
            "total_trades": self.total_trades,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation of backtest result."""
        return f"<BacktestResult(id={self.id}, strategy_id={self.strategy_id}, return={self.total_return})>"
