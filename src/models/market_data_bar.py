"""SQLAlchemy model for cached market data bars."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import SQLAlchemyModel


class MarketDataBar(SQLAlchemyModel):
    """Persisted market data bar for building historical datasets."""

    __tablename__ = "market_data_bars"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timeframe",
            "timestamp",
            name="uq_market_data_bar_symbol_timeframe_timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(index=True, nullable=False)
    open: Mapped[float] = mapped_column(nullable=False)
    high: Mapped[float] = mapped_column(nullable=False)
    low: Mapped[float] = mapped_column(nullable=False)
    close: Mapped[float] = mapped_column(nullable=False)
    volume: Mapped[float] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(default="alpaca", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict[str, float | str]:
        """Serialize the bar to a plain dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source,
        }
