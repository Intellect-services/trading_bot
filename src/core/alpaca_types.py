"""Type definitions for Alpaca API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


class Position(TypedDict):
    """Position type definition."""

    symbol: str
    qty: float
    side: str
    avg_entry_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    lastday_price: float
    change_today: float


class Order(TypedDict):
    """Order type definition."""

    id: str
    symbol: str
    qty: float
    side: str
    type: str
    time_in_force: str
    status: str
    filled_qty: float
    filled_avg_price: float
    created_at: datetime
    updated_at: datetime


class Asset(TypedDict):
    """Asset type definition."""

    id: str
    symbol: str
    name: str
    status: str
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool


class Bar(TypedDict):
    """Bar type definition."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int
    vwap: float


class Clock(TypedDict):
    """Market clock type definition."""

    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    timestamp: Optional[datetime]


class Account(TypedDict):
    """Account type definition."""

    id: str
    cash: float
    portfolio_value: float
    buying_power: float
    equity: float
    long_market_value: float
    short_market_value: float
    initial_margin: float
    maintenance_margin: float
    last_equity: float
    multiplier: float
    status: str
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: Optional[datetime]
    trade_suspended_by_user: bool
    currency: str
