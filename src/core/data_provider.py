"""Unified data provider with caching and fallbacks."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.core.alpaca_service import AlpacaService
from src.core.data_cache import DataCache
from src.core.data_providers import AlphaVantageProvider, YahooFinanceProvider


class DataProvider:
    """Combines Alpaca, cache, and free providers to supply market data."""

    def __init__(
        self,
        *,
        alpaca_service: AlpacaService | None,
        cache: DataCache | None = None,
        yahoo_provider: YahooFinanceProvider | None = None,
        alpha_provider: AlphaVantageProvider | None = None,
    ) -> None:
        self.alpaca_service = alpaca_service
        self.cache = cache or DataCache()
        self.yahoo_provider = yahoo_provider or YahooFinanceProvider()
        self.alpha_provider = alpha_provider or AlphaVantageProvider()

    def get_historical_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch bars using cache → Alpaca → Yahoo → Alpha Vantage fallback."""

        end = end or datetime.utcnow()

        cached = self.cache.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
        )
        if cached:
            return [bar.to_dict() for bar in cached]

        if self.alpaca_service:
            alpaca_bars = self.alpaca_service.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
            )
            symbol_bars = alpaca_bars.get(symbol, []) if alpaca_bars else []
            if symbol_bars:
                self.cache.store_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    bars=symbol_bars,
                    source="alpaca",
                )
                return symbol_bars

        yahoo_bars = self.yahoo_provider.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
        )
        if yahoo_bars:
            self.cache.store_bars(
                symbol=symbol,
                timeframe=timeframe,
                bars=yahoo_bars,
                source="yahoo",
            )
            return yahoo_bars

        if self.alpha_provider.is_configured():
            alpha_bars = self.alpha_provider.get_intraday_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
            if alpha_bars:
                self.cache.store_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    bars=alpha_bars,
                    source="alpha_vantage",
                )
                return alpha_bars

        return []

    def get_latest_price(self, symbol: str) -> float | None:
        """Fetch the latest price using Alpaca first, then cache, then Yahoo."""

        if self.alpaca_service:
            try:
                return self.alpaca_service.get_latest_price(symbol)
            except Exception:
                pass

        cached = self.cache.get_bars(
            symbol=symbol,
            timeframe="1Day",
            start=datetime.utcnow() - timedelta(days=5),
            end=datetime.utcnow(),
            limit=1,
            ascending=False,
        )
        if cached:
            return cached[0].close

        yahoo_bars = self.yahoo_provider.get_historical_data(
            symbol=symbol,
            timeframe="1Day",
            start=datetime.utcnow() - timedelta(days=5),
            end=datetime.utcnow(),
            limit=1,
        )
        if yahoo_bars:
            return float(yahoo_bars[-1]["close"])
        return None
