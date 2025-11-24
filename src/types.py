"""Type definitions for the trading bot."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict

from flask import Response

# Type aliases for route decorators
RouteDecorator = Callable[..., Response]
SocketIODecorator = Callable[..., None]

# Type aliases for bot metrics and status
BotMetrics = dict[str, float | int | str | datetime | None]
BotStatusDict = dict[str, BotMetrics | bool | str | None]

# Type aliases for configuration
ConfigDict = dict[str, Any]

# Type aliases for trading data
PositionDict = dict[str, str | float | int]
OrderDict = dict[str, str | float | int | datetime]
AccountDict = dict[str, str | float | int | bool]

# Type aliases for strategy
StrategyConfig = dict[str, Any]
StrategyState = dict[str, Any]

# Type aliases for backtesting
BacktestResult = dict[str, float | int | str | dict[str, float]]
BacktestMetrics = dict[str, float]


class TradeAccount(TypedDict):
    """Type definition for trading account details."""

    id: str
    account_number: str
    status: str
    currency: str
    buying_power: float
    cash: float
    equity: float
    last_equity: float
    created_at: datetime
    updated_at: datetime


class PortfolioHistory(TypedDict):
    timestamp: list[datetime]
    equity: list[float]
    profit_loss: list[float]
    profit_loss_pct: list[float]
    base_value: float
    timeframe: str


class MarketStatus(TypedDict):
    is_open: bool
    next_open: datetime
    next_close: datetime
    current_time: datetime
    previous_open: datetime
    previous_close: datetime
    extended_hours_open: datetime
    extended_hours_close: datetime
    timezone: str


@dataclass
class PriceBar:
    """Represents a price bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int | None = None
    vwap: float | None = None


@dataclass
class Position:
    """Represents a trading position."""

    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float
    side: str


@dataclass
class Order:
    """Represents a trading order."""

    id: str
    symbol: str
    quantity: float
    side: str
    type: str
    status: str
    created_at: datetime
    filled_at: datetime | None = None
    filled_quantity: float | None = None
    filled_price: float | None = None
    filled_avg_price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    trail_price: float | None = None
    trail_percent: float | None = None
    hwm: float | None = None
