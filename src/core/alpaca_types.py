"""Type stubs for Alpaca modules."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TypedDict, Union


# Type stubs for alpaca.trading.client
class TradingClient(Protocol):
    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        ...

    def get_account(self) -> Dict[str, Any]:
        ...

    def get_positions(self) -> List[Dict[str, Any]]:
        ...

    def submit_order(
        self, symbol: str, qty: float, side: str, type: str, time_in_force: str
    ) -> Dict[str, Any]:
        ...


# Type stubs for alpaca.data.historical
class HistoricalDataClient(Protocol):
    def __init__(self, api_key: str, secret_key: str) -> None:
        ...

    def get_bars(
        self, symbol: str, timeframe: Any, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        ...


# Type stubs for alpaca.data.requests
class StockBarsRequest(Protocol):
    def __init__(
        self,
        symbol_or_symbols: Union[str, List[str]],
        timeframe: Any,
        start: datetime,
        end: datetime,
    ) -> None:
        ...


# Type stubs for alpaca.data.timeframe
class TimeFrame(Protocol):
    def __init__(self, amount: int, unit: str) -> None:
        ...


# Type stubs for alpaca.trading.requests
class OrderRequest(Protocol):
    def __init__(
        self, symbol: str, qty: float, side: str, type: str, time_in_force: str
    ) -> None:
        ...


# Type stubs for alpaca.trading.enums
class OrderSide:
    BUY: str = "buy"
    SELL: str = "sell"


class OrderType:
    MARKET: str = "market"
    LIMIT: str = "limit"


class TimeInForce:
    DAY: str = "day"
    GTC: str = "gtc"


# Type stubs for alpaca.trading.models
class OrderModel(Protocol):
    id: str
    client_order_id: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime
    filled_at: Optional[datetime]
    expired_at: Optional[datetime]
    canceled_at: Optional[datetime]
    failed_at: Optional[datetime]
    replaced_at: Optional[datetime]
    replaced_by: Optional[str]
    replaces: Optional[str]
    asset_id: str
    symbol: str
    asset_class: str
    qty: float
    filled_qty: float
    filled_avg_price: Optional[float]
    order_class: str
    order_type: str
    type: str
    side: str
    time_in_force: str
    limit_price: Optional[float]
    stop_price: Optional[float]
    status: str
    extended_hours: bool
    legs: List[Dict[str, Any]]
    trail_percent: Optional[float]
    trail_price: Optional[float]
    hwm: Optional[float]


# Type stubs for alpaca.data.models
class BarModel(Protocol):
    t: datetime
    o: float
    h: float
    l: float
    c: float
    v: int


class Position(TypedDict):
    """Position type definition."""

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


class Order(TypedDict):
    """Order type definition."""

    id: str
    client_order_id: str
    created_at: str
    updated_at: str
    submitted_at: str
    filled_at: Optional[str]
    expired_at: Optional[str]
    canceled_at: Optional[str]
    failed_at: Optional[str]
    replaced_at: Optional[str]
    replaced_by: Optional[str]
    replaces: Optional[str]
    asset_id: str
    symbol: str
    asset_class: str
    notional: Optional[str]
    qty: Optional[float]
    filled_qty: float
    filled_avg_price: Optional[float]
    order_class: str
    order_type: str
    type: str
    side: str
    time_in_force: str
    limit_price: Optional[float]
    stop_price: Optional[float]
    status: str
    extended_hours: bool
    legs: Optional[List[Dict[str, Any]]]
    trail_percent: Optional[float]
    trail_price: Optional[float]
    hwm: Optional[float]


class Asset(TypedDict):
    """Asset type definition."""

    id: str
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


class Bar(TypedDict):
    """Bar type definition."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int
    vwap: float
