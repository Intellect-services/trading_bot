"""Type definitions for Alpaca API responses."""

from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Literal, NamedTuple, Optional, TypedDict, Union
from uuid import UUID


class TimeFrame(NamedTuple):
    """Time frame for market data."""

    amount: int
    unit: Literal["minute", "hour", "day"]


class OrderSide(str, Enum):
    """Order side enumeration."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    """Time in force enumeration."""

    DAY = "day"
    GTC = "gtc"
    OPG = "opg"
    CLS = "cls"
    IOC = "ioc"
    FOK = "fok"


class Sort(str, Enum):
    """Sort direction enumeration."""

    ASC = "asc"
    DESC = "desc"


class QueryOrderStatus(str, Enum):
    """Order status enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class TradeAccount(TypedDict):
    """Account information from Alpaca API."""

    account_number: str
    buying_power: float
    cash: float
    equity: float
    initial_margin: float
    maintenance_margin: float
    pattern_day_trader: bool
    portfolio_value: float
    status: str
    trade_suspended_by_user: bool
    trading_blocked: bool
    transfers_blocked: bool


class Position(TypedDict):
    """Position information from Alpaca API."""

    asset_id: UUID
    symbol: str
    exchange: str
    asset_class: str
    avg_entry_price: float
    qty: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    lastday_price: float
    change_today: float


class Order(TypedDict):
    """Order information from Alpaca API."""

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
    legs: Optional[List[Dict[str, str]]]


class Asset(TypedDict):
    """Asset information from Alpaca API."""

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
    maintenance_margin_requirement: float
    min_order_size: float
    min_trade_increment: float
    price_increment: float


class Clock(TypedDict):
    """Market clock information from Alpaca API."""

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime


class Bar(TypedDict):
    """Bar data from Alpaca API."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int
    vwap: float


class BarSet(TypedDict):
    """Bar set data from Alpaca API."""

    bars: List[Bar]
    next_page_token: Optional[str]
    symbol: str


class BaseOrderRequest(TypedDict):
    """Base order request parameters."""

    symbol: str
    qty: float
    side: OrderSide
    time_in_force: TimeInForce


class MarketOrderRequest(BaseOrderRequest):
    """Market order request parameters."""

    type: Literal["market"]


class LimitOrderRequest(BaseOrderRequest):
    """Limit order request parameters."""

    type: Literal["limit"]
    limit_price: float


class StopOrderRequest(BaseOrderRequest):
    """Stop order request parameters."""

    type: Literal["stop"]
    stop_price: float


class StopLimitOrderRequest(BaseOrderRequest):
    """Stop limit order request parameters."""

    type: Literal["stop_limit"]
    limit_price: float
    stop_price: float
