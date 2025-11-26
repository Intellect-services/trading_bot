"""Market data caching utilities built on SQLAlchemy."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import asc, desc, select

from src.database import db
from src.models.market_data_bar import MarketDataBar

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class DataCache:
    """Persist and retrieve market data bars from the local database."""

    def store_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        bars: Iterable[dict[str, float | str]],
        source: str = "alpaca",
    ) -> None:
        """Persist a batch of bars, ignoring duplicates."""

        objects: list[MarketDataBar] = []
        for bar in bars:
            timestamp_raw = bar.get("timestamp")
            if timestamp_raw is None:
                continue
            timestamp = (
                timestamp_raw
                if isinstance(timestamp_raw, datetime)
                else datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            )
            objects.append(
                MarketDataBar(
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=float(bar.get("open", bar.get("o", 0.0))),
                    high=float(bar.get("high", bar.get("h", 0.0))),
                    low=float(bar.get("low", bar.get("l", 0.0))),
                    close=float(bar.get("close", bar.get("c", 0.0))),
                    volume=float(bar.get("volume", bar.get("v", 0.0))),
                    source=source,
                )
            )

        if not objects:
            return

        with db.session.no_autoflush:
            for bar in objects:
                existing = MarketDataBar.query.filter_by(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                ).first()
                if existing:
                    continue
                db.session.add(bar)
        db.session.commit()

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
        ascending: bool = True,
    ) -> list[MarketDataBar]:
        """Retrieve cached bars for a symbol/timeframe."""

        stmt = select(MarketDataBar).where(
            MarketDataBar.symbol == symbol.upper(),
            MarketDataBar.timeframe == timeframe,
        )
        if start:
            stmt = stmt.where(MarketDataBar.timestamp >= start)
        if end:
            stmt = stmt.where(MarketDataBar.timestamp <= end)

        stmt = stmt.order_by(
            asc(MarketDataBar.timestamp) if ascending else desc(MarketDataBar.timestamp)
        )
        if limit:
            stmt = stmt.limit(limit)

        result: Sequence[MarketDataBar] = db.session.execute(stmt).scalars().all()
        return list(result)
