"""Type definitions for Alpaca API interactions."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, TypedDict, Union
from uuid import UUID


class TimeFrame(TypedDict):
    """Timeframe for historical data."""

    amount: int
    unit: str


class OrderSide(str, Enum):
    """Order side enum."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enum."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    """Time in force enum."""

    DAY = "day"
    GTC = "gtc"
    OPG = "opg"
    CLS = "cls"
    IOC = "ioc"
    FOK = "fok"


class Sort(str, Enum):
    """Sort order enum."""

    ASC = "asc"
    DESC = "desc"


class QueryOrderStatus(str, Enum):
    """Order status enum."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class TradeAccount(TypedDict):
    """Trading account data."""

    account_number: str
    cash: str
    portfolio_value: str
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: datetime
    trade_suspended_by_user: bool
    multiplier: str
    shorting_enabled: bool
    equity: str
    last_equity: str
    initial_margin: str
    maintenance_margin: str
    last_maintenance_margin: str
    long_market_value: str
    short_market_value: str
    buying_power: str
    regt_buying_power: str
    daytrading_buying_power: str
    effective_buying_power: str
    crypto_status: str
    currency: str
    accrued_fees: str
    max_withdrawal_amount: str


class Position(TypedDict):
    """Position data."""

    asset_id: UUID
    symbol: str
    exchange: str
    asset_class: str
    asset_marginable: bool
    qty: str
    avg_entry_price: str
    side: str
    market_value: str
    cost_basis: str
    unrealized_pl: str
    unrealized_plpc: str
    unrealized_intraday_pl: str
    unrealized_intraday_plpc: str
    current_price: str
    lastday_price: str
    change_today: str


class Order(TypedDict):
    """Order data."""

    id: UUID
    client_order_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    filled_at: Optional[datetime]
    expired_at: Optional[datetime]
    canceled_at: Optional[datetime]
    failed_at: Optional[datetime]
    replaced_at: Optional[datetime]
    replaced_by: Optional[UUID]
    replaces: Optional[UUID]
    asset_id: Optional[UUID]
    symbol: str
    asset_class: str
    qty: float
    filled_qty: float
    type: OrderType
    side: OrderSide
    time_in_force: TimeInForce
    limit_price: Optional[float]
    stop_price: Optional[float]
    filled_avg_price: Optional[float]
    status: str
    extended_hours: bool
    legs: Optional[List["Order"]]


class Asset(TypedDict):
    """Asset data."""

    id: UUID
    class_: str
    exchange: str
    symbol: str
    name: str
    status: str
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool


class Clock(TypedDict):
    """Market clock data."""

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime


class Bar(TypedDict):
    """Bar data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class BarSet(TypedDict):
    """Set of bars."""

    bars: List[Bar]


class MarketOrderRequest(TypedDict):
    """Market order request."""

    symbol: str
    qty: float
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce


class LimitOrderRequest(TypedDict):
    """Limit order request."""

    symbol: str
    qty: float
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce
    limit_price: float


class StopOrderRequest(TypedDict):
    """Stop order request."""

    symbol: str
    qty: float
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce
    stop_price: float


class StopLimitOrderRequest(TypedDict):
    """Stop limit order request."""

    symbol: str
    qty: float
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce
    limit_price: float
    stop_price: float
