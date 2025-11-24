"""Type definitions for Alpaca API interactions."""

from datetime import datetime
from enum import Enum
from typing import TypedDict
from uuid import UUID


class TimeFrame(str, Enum):
    """Timeframe for historical data."""

    MINUTE = "1Min"
    FIVE_MINUTE = "5Min"
    FIFTEEN_MINUTE = "15Min"
    THIRTY_MINUTE = "30Min"
    HOUR = "1H"
    DAY = "1D"
    WEEK = "1W"
    MONTH = "1M"


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


class TradeAccount(TypedDict, total=False):
    """Trading account data."""

    account_number: str
    status: str
    cash: float
    portfolio_value: float
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: datetime
    trade_suspended_by_user: bool
    multiplier: float
    shorting_enabled: bool
    equity: float
    last_equity: float
    initial_margin: float
    maintenance_margin: float
    last_maintenance_margin: float
    long_market_value: float
    short_market_value: float
    buying_power: float
    regt_buying_power: float
    daytrading_buying_power: float
    effective_buying_power: float
    crypto_status: str
    currency: str
    accrued_fees: float
    max_withdrawal_amount: float
    is_portfolio_margin: bool
    pending_transfer_in: float
    pending_transfer_out: float


class Position(TypedDict, total=False):
    """Position data used internally by the bot."""

    symbol: str
    qty: float
    avg_entry_price: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    unrealized_intraday_pl: float
    unrealized_intraday_plpc: float
    current_price: float
    lastday_price: float
    change_today: float
    size: float
    avg_price: float
    pnl: float
    stop_loss: float
    take_profit: float


class Order(TypedDict):
    """Order data."""

    id: UUID
    client_order_id: str
    created_at: datetime
    updated_at: datetime | None
    submitted_at: datetime | None
    filled_at: datetime | None
    expired_at: datetime | None
    canceled_at: datetime | None
    failed_at: datetime | None
    replaced_at: datetime | None
    replaced_by: UUID | None
    replaces: UUID | None
    asset_id: UUID | None
    symbol: str
    asset_class: str
    qty: float
    filled_qty: float
    type: OrderType
    side: OrderSide
    time_in_force: TimeInForce
    limit_price: float | None
    stop_price: float | None
    filled_avg_price: float | None
    status: str
    extended_hours: bool
    legs: list["Order"] | None


class Asset(TypedDict, total=False):
    """Asset data."""

    symbol: str
    name: str
    exchange: str
    class_: str
    status: str
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool


class Clock(TypedDict, total=False):
    """Market clock data."""

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime


class Bar:
    """Bar data."""

    def __init__(
        self,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: int,
    ) -> None:
        """Initialize bar data.

        Args:
            timestamp: Bar timestamp
            open: Opening price
            high: Highest price
            low: Lowest price
            close: Closing price
            volume: Trading volume
        """
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


class BarSet:
    """Set of bars."""

    def __init__(self, bars: list[Bar]) -> None:
        """Initialize bar set.

        Args:
            bars: List of bars
        """
        self.bars = bars


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
