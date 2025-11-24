"""Bot service for managing trading operations."""

from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, TypedDict, cast

import pandas as pd
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Asset, Clock, Order, TradeAccount
from src.strategies.moving_average import MovingAverageCrossover

from ..utils.logger import setup_logger
from .config import Config
from .risk_manager import RiskManager

logger = setup_logger(__name__)


class BotStatus(Enum):
    """Bot status enumeration."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


class Position(TypedDict):
    """Position type definition."""

    symbol: str
    size: float
    avg_price: float
    current_price: float
    side: str
    stop_loss: float | None
    take_profit: float | None


class BotService:
    """Service for managing trading operations."""

    def __init__(self, config: Config) -> None:
        """Initialize the bot service with configuration."""
        try:
            self.config = config
            self.alpaca_service = AlpacaService(config)
            self.risk_manager = RiskManager(config.risk_factor, config.max_position_size)
            self.strategy = MovingAverageCrossover(
                short_window=config.short_window, long_window=config.long_window
            )
            self.positions: dict[str, Position] = {}
            self.status = BotStatus.STOPPED
            self.update_positions()
        except Exception as e:
            logger.error(f"Failed to initialize bot service: {e}")
            raise

    def start(self) -> None:
        """Start the trading bot.

        Raises:
            Exception: If bot fails to start
        """
        try:
            self.status = BotStatus.RUNNING
            logger.info("Trading bot started")
        except Exception as e:
            logger.error("Error starting trading bot: %s", str(e))
            raise

    def stop(self) -> None:
        """Stop the trading bot.

        Raises:
            Exception: If bot fails to stop
        """
        try:
            self.status = BotStatus.STOPPED
            logger.info("Trading bot stopped")
        except Exception as e:
            logger.error("Error stopping trading bot: %s", str(e))
            raise

    def get_status(self) -> dict[str, str | float | int | bool]:
        """Get the current status of the trading bot.

        Returns:
            Dict[str, Union[str, float, int, bool]]: Bot status information

        Raises:
            Exception: If status retrieval fails
        """
        try:
            account = self.alpaca_service.get_account()
            positions = self.alpaca_service.get_positions()

            return {
                "status": self.status.name.lower(),
                "initial_capital": float(self.config.INITIAL_CAPITAL),
                "current_capital": float(account.get("equity", 0.0)),
                "active_positions": len(positions),
                "total_trades": len(self.positions),
            }
        except Exception as e:
            logger.error("Error getting bot status: %s", str(e))
            raise

    def get_positions(self) -> list[Position]:
        """Get all positions."""
        try:
            positions = self.alpaca_service.get_positions()
            return [
                Position(
                    symbol=pos["symbol"],
                    size=float(pos["qty"]),
                    avg_price=float(pos["avg_entry_price"]),
                    current_price=float(pos["current_price"]),
                    side=pos["side"],
                    stop_loss=None,
                    take_profit=None,
                )
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_trades(self) -> list[dict[str, str | float | datetime]]:
        """Get trade history.

        Returns:
            List[Dict[str, Union[str, float, datetime]]]: List of trades

        Raises:
            Exception: If trade history retrieval fails
        """
        try:
            trades: list[dict[str, str | float | datetime]] = []
            for position in self.positions.values():
                trades.append(
                    {
                        "symbol": str(position["symbol"]),
                        "qty": float(position["size"]),
                        "side": str(position["side"]),
                        "price": float(position["avg_price"]),
                        "timestamp": datetime.now(),
                    }
                )
            return trades
        except Exception as e:
            logger.error("Error getting trades: %s", str(e))
            raise

    def get_portfolio_history(
        self, timeframe: str = "1D"
    ) -> dict[str, list[datetime] | list[float] | str]:
        """Get portfolio history.

        Args:
            timeframe: Timeframe for history (default: "1D")

        Returns:
            Dict[str, Union[List[datetime], List[float], str]]: Portfolio history

        Raises:
            Exception: If portfolio history retrieval fails
        """
        try:
            end = datetime.now()
            end - timedelta(days=30)  # Default to 30 days

            if timeframe == "1D":
                end - timedelta(days=30)
            elif timeframe == "1W":
                end - timedelta(weeks=12)
            elif timeframe == "1M":
                end - timedelta(days=365)

            account = self.alpaca_service.get_account()
            equity = float(account.get("equity", 0.0))
            float(self.config.INITIAL_CAPITAL)

            return {
                "timestamp": [end],
                "equity": [equity],
                "timeframe": timeframe,
            }
        except Exception as e:
            logger.error("Error getting portfolio history: %s", str(e))
            raise

    def get_account(self) -> TradeAccount:
        """Get account information."""
        try:
            account = self.alpaca_service.get_account()
            return TradeAccount(
                account_number=str(account.get("account_number", "")),
                status=str(account.get("status", "")),
                currency=str(account.get("currency", "USD")),
                cash=float(account.get("cash", 0.0)),
                portfolio_value=float(account.get("portfolio_value", 0.0)),
                pattern_day_trader=bool(account.get("pattern_day_trader", False)),
                trading_blocked=bool(account.get("trading_blocked", False)),
                transfers_blocked=bool(account.get("transfers_blocked", False)),
                account_blocked=bool(account.get("account_blocked", False)),
                created_at=account.get("created_at", datetime.utcnow()),
                trade_suspended_by_user=bool(account.get("trade_suspended_by_user", False)),
                shorting_enabled=bool(account.get("shorting_enabled", False)),
                long_market_value=float(account.get("long_market_value", 0.0)),
                short_market_value=float(account.get("short_market_value", 0.0)),
                equity=float(account.get("equity", 0.0)),
                last_equity=float(account.get("last_equity", 0.0)),
                initial_margin=float(account.get("initial_margin", 0.0)),
                maintenance_margin=float(account.get("maintenance_margin", 0.0)),
                last_maintenance_margin=float(account.get("last_maintenance_margin", 0.0)),
                daytrading_buying_power=float(account.get("daytrading_buying_power", 0.0)),
                regt_buying_power=float(account.get("regt_buying_power", 0.0)),
                buying_power=float(account.get("buying_power", 0.0)),
                effective_buying_power=float(account.get("effective_buying_power", 0.0)),
                is_portfolio_margin=bool(account.get("is_portfolio_margin", False)),
                multiplier=float(account.get("multiplier", 1.0)),
                accrued_fees=float(account.get("accrued_fees", 0.0)),
                pending_transfer_in=float(account.get("pending_transfer_in", 0.0)),
                pending_transfer_out=float(account.get("pending_transfer_out", 0.0)),
                max_withdrawal_amount=float(account.get("max_withdrawal_amount", 0.0)),
            )
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_open_position(self, symbol: str) -> Position | None:  # noqa: ARG002
        """Get open position for a symbol."""
        try:
            position = self.alpaca_service.get_positions()
            if not position:
                return None
            pos = position[0]
            return Position(
                symbol=pos["symbol"],
                size=float(pos["qty"]),
                avg_price=float(pos["avg_entry_price"]),
                current_price=float(pos["current_price"]),
                side=pos["side"],
                stop_loss=None,
                take_profit=None,
            )
        except Exception as e:
            logger.error(f"Failed to get open position: {e}")
            raise

    def get_asset(self, symbol: str) -> Asset:
        """Get asset information.

        Args:
            symbol: Symbol to get asset for

        Returns:
            Asset: Asset information
        """
        asset = self.alpaca_service.get_asset(symbol)
        return Asset(
            class_=asset.get("class_", asset.get("class", "")),
            exchange=asset.get("exchange", ""),
            symbol=asset.get("symbol", symbol),
            name=asset.get("name", ""),
            status=asset.get("status", "active"),
            tradable=bool(asset.get("tradable", True)),
            marginable=bool(asset.get("marginable", False)),
            shortable=bool(asset.get("shortable", False)),
            easy_to_borrow=bool(asset.get("easy_to_borrow", False)),
            fractionable=bool(asset.get("fractionable", False)),
        )

    def get_clock(self) -> Clock:
        """Get market clock."""
        try:
            clock = self.alpaca_service.get_clock()
            return Clock(
                timestamp=clock.get("timestamp", datetime.now()),
                is_open=bool(clock.get("is_open", False)),
                next_open=clock.get("next_open", datetime.now()),
                next_close=clock.get("next_close", datetime.now()),
            )
        except Exception as e:
            logger.error(f"Failed to get clock: {e}")
            raise

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> Order:
        """Submit an order."""
        try:
            order = self.alpaca_service.submit_order(
                symbol=symbol,
                qty=int(qty),  # Convert to int as required by Alpaca
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
            # Construct Order TypedDict field by field
            return Order(
                id=order.get("id", ""),
                client_order_id=order.get("client_order_id", ""),
                created_at=order.get("created_at", datetime.now()),
                updated_at=order.get("updated_at", datetime.now()),
                submitted_at=order.get("submitted_at", datetime.now()),
                filled_at=order.get("filled_at", None),
                expired_at=order.get("expired_at", None),
                canceled_at=order.get("canceled_at", None),
                failed_at=order.get("failed_at", None),
                replaced_at=order.get("replaced_at", None),
                replaced_by=order.get("replaced_by", None),
                replaces=order.get("replaces", None),
                asset_id=order.get("asset_id", ""),
                symbol=order.get("symbol", symbol),
                asset_class=order.get("asset_class", ""),
                qty=float(order.get("qty", qty)),
                filled_qty=float(order.get("filled_qty", 0.0)),
                type=order.get("type", str(type)),
                side=order.get("side", str(side)),
                time_in_force=order.get("time_in_force", str(time_in_force)),
                limit_price=float(order.get("limit_price", 0.0)),
                stop_price=float(order.get("stop_price", 0.0)),
                filled_avg_price=float(order.get("filled_avg_price", 0.0)),
                status=order.get("status", ""),
                extended_hours=bool(order.get("extended_hours", False)),
                legs=order.get("legs", []),
            )
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise

    def get_orders(self, status: str | None = None) -> list[Order]:
        """Get orders.

        Args:
            status: Order status to filter by

        Returns:
            List[Order]: List of orders
        """
        orders = self.alpaca_service.get_orders(status=status)
        return [
            Order(
                id=order.get("id", ""),
                client_order_id=order.get("client_order_id", ""),
                created_at=order.get("created_at", datetime.now()),
                updated_at=order.get("updated_at", datetime.now()),
                submitted_at=order.get("submitted_at", datetime.now()),
                filled_at=order.get("filled_at", None),
                expired_at=order.get("expired_at", None),
                canceled_at=order.get("canceled_at", None),
                failed_at=order.get("failed_at", None),
                replaced_at=order.get("replaced_at", None),
                replaced_by=order.get("replaced_by", None),
                replaces=order.get("replaces", None),
                asset_id=order.get("asset_id", ""),
                symbol=order.get("symbol", ""),
                asset_class=order.get("asset_class", ""),
                qty=float(order.get("qty", 0.0)),
                filled_qty=float(order.get("filled_qty", 0.0)),
                type=order.get("type", ""),
                side=order.get("side", ""),
                time_in_force=order.get("time_in_force", ""),
                limit_price=float(order.get("limit_price", 0.0)),
                stop_price=float(order.get("stop_price", 0.0)),
                filled_avg_price=float(order.get("filled_avg_price", 0.0)),
                status=order.get("status", ""),
                extended_hours=bool(order.get("extended_hours", False)),
                legs=order.get("legs", []),
            )
            for order in orders
        ]

    def get_order_by_id(self, order_id: str) -> Order:
        """Get order by ID.

        Args:
            order_id: ID of order to get

        Returns:
            Order: Order information
        """
        order = self.alpaca_service.get_order_by_id(order_id)
        return Order(
            id=order.get("id", ""),
            client_order_id=order.get("client_order_id", ""),
            created_at=order.get("created_at", datetime.now()),
            updated_at=order.get("updated_at", datetime.now()),
            submitted_at=order.get("submitted_at", datetime.now()),
            filled_at=order.get("filled_at", None),
            expired_at=order.get("expired_at", None),
            canceled_at=order.get("canceled_at", None),
            failed_at=order.get("failed_at", None),
            replaced_at=order.get("replaced_at", None),
            replaced_by=order.get("replaced_by", None),
            replaces=order.get("replaces", None),
            asset_id=order.get("asset_id", ""),
            symbol=order.get("symbol", ""),
            asset_class=order.get("asset_class", ""),
            qty=float(order.get("qty", 0.0)),
            filled_qty=float(order.get("filled_qty", 0.0)),
            type=order.get("type", ""),
            side=order.get("side", ""),
            time_in_force=order.get("time_in_force", ""),
            limit_price=float(order.get("limit_price", 0.0)),
            stop_price=float(order.get("stop_price", 0.0)),
            filled_avg_price=float(order.get("filled_avg_price", 0.0)),
            status=order.get("status", ""),
            extended_hours=bool(order.get("extended_hours", False)),
            legs=order.get("legs", []),
        )

    def cancel_order_by_id(self, order_id: str) -> None:
        """Cancel order by ID.

        Args:
            order_id: ID of order to cancel
        """
        self.alpaca_service.cancel_order_by_id(order_id)

    def update_positions(self) -> None:
        """Update positions from Alpaca."""
        try:
            positions = self.alpaca_service.get_positions()
            self.positions = {
                pos["symbol"]: Position(
                    symbol=pos["symbol"],
                    size=float(pos["qty"]),
                    avg_price=float(pos["avg_entry_price"]),
                    current_price=float(pos["current_price"]),
                    side=pos["side"],
                    stop_loss=None,
                    take_profit=None,
                )
                for pos in positions
            }
        except Exception as e:
            logger.error(f"Failed to update positions: {e}")
            raise

    def check_market_status(self) -> bool:
        """Check if market is open.

        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            clock = self.alpaca_service.get_clock()
            return bool(clock.get("is_open", False))
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            raise

    def run_strategy(self, symbol: str) -> None:
        """Run trading strategy for a symbol.

        Args:
            symbol: Symbol to run strategy for
        """
        try:
            if not self.check_market_status():
                logger.info("Market is closed")
                return

            # Get historical data for the symbol
            end = datetime.now()
            start = end - timedelta(days=self.config.lookback_days or 100)
            bars_df = self.alpaca_service.get_historical_bars(
                symbol=symbol,
                timeframe=self.config.strategy_timeframe,
                start=start,
                end=end,
                limit=self.config.lookback_days,
            )

            if bars_df is None or bars_df.empty:
                logger.warning(f"No data available for {symbol}")
                return

            raw_output: Any = self.strategy.generate_signals(bars_df)
            signal_records: list[dict[str, Any]]
            if isinstance(raw_output, pd.DataFrame):
                signal_records = cast("list[dict[str, Any]]", raw_output.to_dict("records"))
            else:
                signal_records = []
                if raw_output:
                    for sig in raw_output:
                        record: dict[str, Any] = {
                            str(key): value for key, value in dict(sig).items()
                        }
                        signal_records.append(record)

            for signal in signal_records:
                action = str(signal.get("action") or signal.get("side") or "").lower()
                size = float(signal.get("size", signal.get("strength", 0.1)))
                if action == "buy":
                    self.submit_order(symbol=symbol, qty=size, side=OrderSide.BUY)
                elif action == "sell":
                    self.submit_order(symbol=symbol, qty=size, side=OrderSide.SELL)
        except Exception as e:
            logger.error(f"Failed to run strategy: {e}")
            raise
