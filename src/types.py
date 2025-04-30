"""Type definitions for the trading bot."""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from flask import Response
from flask_socketio import SocketIO

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
    portfolio_value: float
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: datetime
    trade_suspended_by_user: bool
    multiplier: str
    shorting_enabled: bool
    equity: float
    last_equity: float
    long_market_value: float
    short_market_value: float
    initial_margin: float
    maintenance_margin: float
    last_maintenance_margin: float
    daytrading_buying_power: float
    balance: float
    cleared_balance: float
    pending_transfer_in: float
    pending_transfer_out: float
    sma: float


class Position(TypedDict):
    """Type definition for position details."""

    asset_id: str
    symbol: str
    qty: float
    avg_entry_price: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    lastday_price: float
    change_today: float
    side: str


class Order(TypedDict):
    """Type definition for order details."""

    id: str
    client_order_id: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime
    filled_at: Optional[datetime]
    expired_at: Optional[datetime]
    canceled_at: Optional[datetime]
    failed_at: Optional[datetime]
    asset_id: str
    symbol: str
    asset_class: str
    qty: float
    filled_qty: float
    type: str
    side: str
    time_in_force: str
    limit_price: Optional[float]
    stop_price: Optional[float]
    filled_avg_price: Optional[float]
    status: str
    extended_hours: bool
    legs: Optional[List[Dict[str, Any]]]
