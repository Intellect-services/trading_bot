"""Type definitions for the trading bot."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from alpaca.trading.models import Bar
from flask import Response

# Type aliases for route decorators
RouteDecorator = Callable[..., Response]
SocketIODecorator = Callable[..., None]

# Type aliases for bot metrics and status
BotMetrics = Dict[str, Union[float, int, str, datetime, None]]
BotStatusDict = Dict[str, Union[BotMetrics, bool, str, None]]

# Type aliases for configuration
ConfigDict = Dict[str, Any]

# Type aliases for trading data
PositionDict = Dict[str, Union[str, float, int]]
OrderDict = Dict[str, Union[str, float, int, datetime]]
AccountDict = Dict[str, Union[str, float, int, bool]]

# Type aliases for strategy
StrategyConfig = Dict[str, Any]
StrategyState = Dict[str, Any]

# Type aliases for backtesting
BacktestResult = Dict[str, Union[float, int, str, Dict[str, float]]]
BacktestMetrics = Dict[str, float]


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
    timestamp: List[datetime]
    equity: List[float]
    profit_loss: List[float]
    profit_loss_pct: List[float]
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
class Bar:
    """Represents a price bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[int] = None
    vwap: Optional[float] = None


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
    filled_at: Optional[datetime] = None
    filled_quantity: Optional[float] = None
    filled_price: Optional[float] = None
    filled_avg_price: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_price: Optional[float] = None
    trail_percent: Optional[float] = None
    hwm: Optional[float] = None
