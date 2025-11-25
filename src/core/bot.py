"""Trading bot module for executing trading strategies."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, TypedDict

import pandas as pd

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import (
    Bar,
    BarSet,
    OrderSide,
    OrderType,
    TimeFrame,
    TimeInForce,
)
from src.core.data_provider import DataProvider
from src.core.market_data_stream import MarketDataStreamer
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.utils.config import Config

logger = logging.getLogger(__name__)


class LocalPosition(TypedDict, total=False):
    """Lightweight representation of a position used internally by the bot."""

    size: float
    avg_price: float
    side: str
    pnl: float
    market_value: float
    symbol: str


class TradingBot:
    """Main trading bot class that manages trading operations."""

    def __init__(
        self,
        config: Config,
        strategy: Strategy,
        alpaca_service: AlpacaService,
        user_id: int = 1,
        flask_app=None,
    ):
        """Initialize the trading bot.

        Args:
            config: Configuration object
            strategy: Trading strategy (fallback, will be replaced by StrategyManager)
            alpaca_service: Alpaca service for API calls
            user_id: User ID for database operations (default: 1)
            flask_app: Flask application instance (required for database operations in background threads)
        """
        self.config = config
        self.strategy = strategy  # Keep as fallback
        self.alpaca_service = alpaca_service
        self.flask_app = flask_app  # Store Flask app for application context
        self.data_provider = DataProvider(alpaca_service=alpaca_service)
        self.market_streamer = MarketDataStreamer(
            alpaca_service=alpaca_service,
            data_provider=self.data_provider,
        )
        self.user_id = user_id
        self.is_running = False
        self.status_messages: list[dict[str, Any]] = []
        self.current_analysis = None
        self.current_signals = None
        self.last_analysis_time = None
        self.last_signal_time = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Add initial status message
        self.add_status_message("Bot initialized", "info")
        self.logger.info("Trading bot initialized")

        # Initialize database persistence
        from src.core.bot_persistence import TradingBotPersistence

        self.persistence = TradingBotPersistence(user_id)
        if not self.persistence.initialize():
            self.logger.error("Failed to initialize database persistence")
            self.add_status_message("Database initialization failed", "error")
        else:
            self.logger.info("Database persistence initialized")
            self.add_status_message("Database connected", "info")

            # Load existing positions from database
            db_positions = self.persistence.get_open_positions()
            self.logger.info(f"Loaded {len(db_positions)} positions from database")
            self.add_status_message(f"Loaded {len(db_positions)} positions from database", "info")

        # Initialize StrategyManager for multi-strategy execution
        from src.core.strategy_manager import StrategyManager

        self.strategy_manager = StrategyManager(self.persistence)
        self.logger.info("StrategyManager initialized")
        self.add_status_message("Strategy manager ready", "info")

        # Initialize OrderManager for automated order tracking
        from src.core.order_manager import OrderManager

        self.order_manager = OrderManager(self, self.persistence, check_interval=5)
        self.logger.info("OrderManager initialized")
        self.add_status_message("Order tracking ready", "info")

        # Enhanced RiskManager - disabled for now, using basic RiskManager
        # from src.core.enhanced_risk_manager import EnhancedRiskManager
        # self.enhanced_risk_manager = EnhancedRiskManager(
        #     portfolio_value=0,  # Will be updated in update_state
        #     persistence=self.persistence
        # )
        # self.logger.info("Enhanced RiskManager initialized")
        # self.add_status_message("Risk management ready", "info")

        # Initialize state
        self.account = self.alpaca_service.get_account()
        self.equity = float(self.account["portfolio_value"])
        self.cash = float(self.account["cash"])
        self.buying_power = float(self.account["buying_power"])

        # Initialize portfolio and risk manager
        self.portfolio = Portfolio(self.equity)
        self.risk_manager = RiskManager(self.equity)

        # Trading state
        self.is_trading = True
        self.positions: dict[str, LocalPosition] = {}
        self.orders: dict[str, dict[str, Any]] = {}
        self.market_clock: dict[str, Any] = self.alpaca_service.get_clock()

        # Performance tracking
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_trades = 0
        self.total_pnl = 0.0

    def add_status_message(self, message: str, level: str = "info") -> None:
        """Add a status message with timestamp."""
        try:
            timestamp = datetime.now()
            self.status_messages.append(
                {"timestamp": timestamp, "level": level, "message": message}
            )
            # Keep only the last 100 messages
            if len(self.status_messages) > 100:
                self.status_messages = self.status_messages[-100:]
            self.logger.info(f"Status message added: [{level.upper()}] {message}")
        except Exception as e:
            self.logger.error(f"Error adding status message: {e}")

    def start(self) -> None:
        """Start the trading bot."""
        if self.is_running:
            self.add_status_message("Bot is already running", "warning")
            return

        self.is_running = True
        self.add_status_message("Starting trading bot...", "info")

        if self.market_streamer and self.config.strategy_symbols:
            try:
                self.market_streamer.start(
                    self.config.strategy_symbols,
                    self.config.strategy_timeframe,
                )
                self.add_status_message("Real-time market data streaming enabled", "info")
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Failed to start market data streamer: %s", exc, exc_info=True)
                self.add_status_message(
                    "Unable to start live market data streaming. Falling back to cached/REST data.",
                    "warning",
                )

        # Start OrderManager monitoring
        if hasattr(self, "order_manager"):
            self.order_manager.start_monitoring()
            self.add_status_message("Order monitoring started", "info")

        # Start the trading loop in a separate thread
        # Note: Using daemon=False would keep threads alive, but Flask shutdown would hang
        # Daemon=True allows Flask to exit cleanly, but threads die on process exit
        # For persistence, we rely on auto-restart mechanism
        self.trading_thread = threading.Thread(
            target=self._trading_loop, daemon=True, name=f"TradingBot-{self.user_id}"
        )
        self.trading_thread.start()
        self.add_status_message("Trading bot started successfully", "info")
        self.logger.info(
            f"Trading bot started for user {self.user_id} (thread: {self.trading_thread.name})"
        )

    def _convert_position(self, position_data: dict[str, Any]) -> LocalPosition:
        """Convert Alpaca position payload into the simplified structure used internally."""
        qty_value = position_data.get("qty", 0) or 0
        avg_price_value = position_data.get("avg_entry_price", 0) or 0
        pnl_value = position_data.get("unrealized_pl", 0) or 0
        market_value = position_data.get("market_value", 0) or 0

        return LocalPosition(
            size=float(qty_value),
            avg_price=float(avg_price_value),
            side=str(position_data.get("side", "long")),
            pnl=float(pnl_value),
            market_value=float(market_value),
            symbol=str(position_data.get("symbol", "")),
        )

    def _convert_bars_to_dataframe(
        self, symbol: str, bars: dict[str, list[dict[str, float | str]]] | None
    ) -> pd.DataFrame | None:
        """Convert raw bar data into a pandas DataFrame."""
        if not bars:
            return None
        symbol_bars = bars.get(symbol)
        if not symbol_bars:
            return None

        df = pd.DataFrame(symbol_bars)
        if df.empty:
            return None

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df.dropna(subset=["timestamp"], inplace=True)
            df.set_index("timestamp", inplace=True)

        numeric_cols = {"open", "high", "low", "close", "volume"}
        for col in numeric_cols.intersection(df.columns):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["close"], inplace=True)
        return df if not df.empty else None

    def _collect_market_data(self) -> dict[str, pd.DataFrame]:
        """Fetch market data for all strategy symbols."""
        market_data: dict[str, pd.DataFrame] = {}
        now = datetime.now()
        start = now - timedelta(days=self.config.lookback_days)

        if not self.config.strategy_symbols:
            self.logger.warning("No strategy symbols configured")
            self.add_status_message(
                "No trading symbols configured. Please set strategy symbols in settings.", "warning"
            )
            return market_data

        for symbol in self.config.strategy_symbols:
            try:
                # Try with full date range first
                bars = self.data_provider.get_historical_bars(
                    symbol=symbol,
                    timeframe=self.config.strategy_timeframe,
                    start=start,
                    end=now,
                )

                # If no data, try with a shorter range (last 30 days) as fallback
                if not bars:
                    self.logger.debug(
                        f"No data with full range for {symbol}, trying shorter range (30 days)"
                    )
                    shorter_start = now - timedelta(days=30)
                    bars = self.data_provider.get_historical_bars(
                        symbol=symbol,
                        timeframe=self.config.strategy_timeframe,
                        start=shorter_start,
                        end=now,
                        limit=100,  # Limit to 100 bars
                    )

                df = self._convert_bars_to_dataframe(symbol, {symbol: bars})
                if df is not None and not df.empty:
                    market_data[symbol] = df
                    self.logger.debug(f"Collected {len(df)} data points for {symbol}")
                else:
                    self.logger.warning(f"No data returned for {symbol} even with fallback")
                    self.add_status_message(
                        f"No data available for {symbol}. "
                        "Possible causes: 1) Data API subscription required (check Alpaca account), "
                        "2) Market closed, 3) Invalid symbol, 4) API authentication issue. "
                        "Check backend logs for detailed error messages.",
                        "warning",
                    )
            except Exception as exc:
                self.logger.error(
                    f"Failed to collect market data for {symbol}: {exc}", exc_info=True
                )
                self.add_status_message(
                    f"Error fetching data for {symbol}: {str(exc)[:100]}", "error"
                )

        return market_data

    def stop(self) -> None:
        """Stop the trading bot."""
        if self.is_running:
            self.is_running = False
            self.logger.info("Trading bot stopped")

        if hasattr(self, "market_streamer") and self.market_streamer:
            try:
                self.market_streamer.stop()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Error stopping market data streamer: %s", exc)

        # Stop OrderManager monitoring
        if hasattr(self, "order_manager"):
            try:
                self.order_manager.stop_monitoring()
                self.logger.info("Order monitoring stopped")
            except Exception as e:
                self.logger.error(f"Error stopping order manager: {e}")

        # Cleanup database session
        if hasattr(self, "persistence"):
            try:
                self.persistence.cleanup()
                self.logger.info("Database session cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up database: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the bot."""
        try:
            datetime.now()
            return {
                "is_running": self.is_running,
                "last_analysis_time": self.last_analysis_time.strftime("%Y-%m-%dT%H:%M:%S")
                if self.last_analysis_time
                else None,
                "last_signal_time": self.last_signal_time.strftime("%Y-%m-%dT%H:%M:%S")
                if self.last_signal_time
                else None,
                "current_analysis": {
                    "symbol": self.current_analysis.get("symbol"),
                    "timestamp": self.current_analysis.get("timestamp").strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                    if self.current_analysis.get("timestamp")
                    else None,
                    "data_points": self.current_analysis.get("data_points", 0),
                }
                if self.current_analysis
                else None,
                "current_signals": self.current_signals,
                "status_messages": [
                    {
                        "timestamp": msg["timestamp"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "level": msg["level"],
                        "message": msg["message"],
                    }
                    for msg in self.status_messages[-50:]  # Last 50 messages for better visibility
                ],
            }
        except Exception as e:
            self.logger.error(f"Error getting bot status: {e}")
            return {"is_running": False, "error": str(e)}

    def _trading_loop(self) -> None:
        """Main trading loop."""
        # Push Flask application context for database operations
        # This is required because DataCache uses Flask-SQLAlchemy which needs app context
        ctx = None
        if self.flask_app:
            ctx = self.flask_app.app_context()
            ctx.push()

        try:
            while self.is_running:
                try:
                    # Check if market is open
                    self.market_clock = self.alpaca_service.get_clock()
                    if not self.market_clock.get("is_open", False):
                        self.add_status_message("Market is closed", "info")
                        time.sleep(60)  # Check every minute
                        continue

                    # Update account information
                    account = self.alpaca_service.get_account()
                    if not account:
                        self.add_status_message("Failed to get account information", "error")
                        time.sleep(60)
                        continue

                    # Update enhanced risk manager with current portfolio value
                    if hasattr(self, "enhanced_risk_manager"):
                        self.enhanced_risk_manager.portfolio_value = float(
                            account["portfolio_value"]
                        )

                    # Get current positions
                    positions = self.alpaca_service.get_positions()
                    self.add_status_message(f"Current positions: {len(positions)}", "info")

                    # Check market status first
                    market_clock = self.alpaca_service.get_clock()
                    is_market_open = market_clock.get("is_open", False)

                    if not is_market_open:
                        next_open = market_clock.get("next_open", "unknown")
                        self.add_status_message(f"Market is closed. Next open: {next_open}", "info")

                    market_data = self._collect_market_data()
                    if not market_data:
                        # Provide more specific error message
                        error_msg = f"No market data available for symbols: {', '.join(self.config.strategy_symbols)}. "
                        if not is_market_open:
                            error_msg += "Market is currently closed. Historical data should still be available."
                        else:
                            error_msg += "This may be due to API issues, invalid symbols, or data API access problems."
                        self.add_status_message(error_msg, "warning")
                        time.sleep(30)
                        continue

                    # Log successful data collection
                    symbols_with_data = list(market_data.keys())
                    if symbols_with_data:
                        total_points = sum(len(df) for df in market_data.values())
                        self.add_status_message(
                            f"Collected {total_points} data points for {len(symbols_with_data)} symbol(s): {', '.join(symbols_with_data)}",
                            "info",
                        )

                    aggregated_signals: dict[str, dict[str, Any]] = {}

                    if hasattr(self, "strategy_manager"):
                        try:
                            self.add_status_message("Executing active strategies...", "info")
                            aggregated_signals = self.strategy_manager.execute_all_strategies(
                                market_data
                            )
                            if aggregated_signals:
                                signal_details = ", ".join(
                                    [
                                        f"{sym}: {sig.get('action', 'hold').upper()}"
                                        for sym, sig in list(aggregated_signals.items())[:5]
                                    ]
                                )
                                self.add_status_message(
                                    f"⚡ SIGNAL GENERATED: {len(aggregated_signals)} signal(s) - {signal_details}",
                                    "signal",
                                )
                            else:
                                self.add_status_message("No aggregated signals generated", "info")
                        except Exception as e:
                            self.add_status_message(f"Error executing strategies: {e!s}", "error")
                            self.logger.error(f"Error executing strategies: {e}")

                    if aggregated_signals:
                        for symbol, signal in aggregated_signals.items():
                            signal_type = signal.get("action") or signal.get("type", "hold")
                            strength = float(signal.get("strength", 0))
                            self.add_status_message(
                                f"📊 SIGNAL: {symbol} → {signal_type.upper()} (strength: {strength:.2f})",
                                "signal",
                            )

                            if hasattr(self, "enhanced_risk_manager"):
                                position_size = self.enhanced_risk_manager.calculate_position_size(
                                    symbol=symbol,
                                    signal_strength=strength,
                                    current_price=self.alpaca_service.get_latest_price(symbol),
                                )
                                if not self.enhanced_risk_manager.check_position_risk(
                                    symbol, position_size
                                ):
                                    self.add_status_message(
                                        f"Position risk check failed for {symbol}", "warning"
                                    )
                                    continue

                            if signal_type == "buy":
                                self._execute_buy(symbol)
                            elif signal_type == "sell":
                                self._execute_sell(symbol)
                    else:
                        self.add_status_message("Using fallback strategy", "warning")
                        if not self.strategy:
                            self.add_status_message("No fallback strategy configured", "error")
                        else:
                            for symbol, data in market_data.items():
                                try:
                                    signals = self.strategy.generate_signals(data)
                                    if not signals:
                                        continue
                                    last_price = float(data["close"].iloc[-1])
                                    for signal in signals:
                                        signal["symbol"] = symbol
                                        signal.setdefault("price", last_price)
                                        self.execute_trade(symbol, signal)
                                except Exception as e:
                                    self.logger.error(f"Error processing {symbol}: {e}")

                    # Sleep before next iteration
                    time.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    self.add_status_message(f"Error in trading loop: {e!s}", "error")
                    self.logger.error(f"Error in trading loop: {e}", exc_info=True)
                    time.sleep(30)  # Wait before retrying
        finally:
            # Pop Flask application context when loop exits
            if ctx:
                ctx.pop()

    def _execute_buy(self, symbol: str) -> None:
        """Execute a buy order."""
        try:
            # Calculate position size (e.g., 10% of available cash)
            account = self.alpaca_service.get_account()
            cash = float(account["cash"])
            position_size = cash * 0.1

            # Get current price
            current_price = self.alpaca_service.get_latest_price(symbol)

            # Calculate quantity
            quantity = int(position_size / current_price)

            if quantity > 0:
                self.add_status_message(
                    f"🚀 EXECUTING BUY ORDER: {quantity} shares of {symbol} at ${current_price:.2f}",
                    "trade",
                )
                order_response = self.alpaca_service.submit_order(
                    symbol=symbol, qty=quantity, side="buy", type="market"
                )
                self.logger.info(f"Executed BUY order for {quantity} shares of {symbol}")

                # Persist order to database
                if order_response and hasattr(self, "persistence"):
                    db_order = self.persistence.persist_order(order_response)
                    if db_order:
                        self.logger.info(f"Order persisted to database: {db_order.id}")
                        self.add_status_message("Order saved to database", "info")
            else:
                self.add_status_message(f"Insufficient funds to buy {symbol}", "warning")
        except Exception as e:
            self.logger.error(f"Error executing buy order for {symbol}: {e}")
            self.add_status_message(f"Error executing buy order for {symbol}: {e!s}", "error")

    def _execute_sell(self, symbol: str) -> None:
        """Execute a sell order."""
        try:
            # Get current position
            positions = self.alpaca_service.get_positions()
            position = next((p for p in positions if p["symbol"] == symbol), None)

            if position:
                quantity = int(position.get("size", 0))
                current_price = self.alpaca_service.get_latest_price(symbol)
                self.add_status_message(
                    f"💰 EXECUTING SELL ORDER: {quantity} shares of {symbol} at ${current_price:.2f}",
                    "trade",
                )
                order_response = self.alpaca_service.submit_order(
                    symbol=symbol, qty=quantity, side="sell", type="market"
                )
                self.logger.info(f"Executed SELL order for {quantity} shares of {symbol}")

                # Persist order to database
                if order_response and hasattr(self, "persistence"):
                    db_order = self.persistence.persist_order(order_response)
                    if db_order:
                        self.logger.info(f"Order persisted to database: {db_order.id}")
                        self.add_status_message("Order saved to database", "info")
            else:
                self.add_status_message(f"No position found for {symbol}", "warning")
        except Exception as e:
            self.logger.error(f"Error executing sell order for {symbol}: {e}")
            self.add_status_message(f"Error executing sell order for {symbol}: {e!s}", "error")

    def update_state(self) -> None:
        """Update the bot's state with latest market data."""
        try:
            # Update account information
            self.account = self.alpaca_service.get_account()
            self.equity = float(self.account["portfolio_value"])
            self.cash = float(self.account["cash"])
            self.buying_power = float(self.account["buying_power"])

            # Update positions
            positions = self.alpaca_service.get_positions()
            self.positions = {
                pos["symbol"]: self._convert_position(pos) for pos in positions if pos.get("symbol")
            }

            # Sync positions with database
            if hasattr(self, "persistence"):
                for pos in positions:
                    try:
                        self.persistence.update_position(
                            symbol=pos["symbol"],
                            quantity=float(pos["qty"]),
                            avg_price=float(pos["avg_entry_price"]),
                            current_price=float(pos["current_price"]),
                            side=pos.get("side", "long"),
                        )
                    except Exception as e:
                        logger.error(f"Error syncing position {pos['symbol']}: {e}")

                # Update portfolio values in database
                try:
                    self.persistence.update_portfolio_values(
                        self.equity, self.cash, self.buying_power
                    )
                except Exception as e:
                    logger.error(f"Error updating portfolio values: {e}")

            # Update orders
            orders = self.alpaca_service.get_orders()
            self.orders = {order["id"]: order for order in orders}

            # Update market clock
            self.market_clock = self.alpaca_service.get_clock()

            logger.debug("Bot state updated successfully")
        except Exception as e:
            logger.error(f"Error updating bot state: {e}")
            raise

    def _check_risk_limits(self) -> bool:
        """Check if any risk limits are breached."""
        try:
            # Check maximum drawdown
            peak_equity = getattr(self.portfolio, "peak_value", self.equity)
            if peak_equity <= 0:
                peak_equity = self.equity or 1.0
            current_drawdown = (peak_equity - self.equity) / peak_equity
            if current_drawdown > self.config.risk_max_drawdown:
                logger.warning(f"Maximum drawdown limit breached: {current_drawdown:.2%}")
                return True

            # Check leverage
            total_position_value = sum(
                float(pos["market_value"]) for pos in self.positions.values()
            )
            current_leverage = total_position_value / self.equity
            if current_leverage > self.config.risk_max_leverage:
                logger.warning(f"Maximum leverage limit breached: {current_leverage:.2f}")
                return True

            # Check position sizes
            for symbol, pos in self.positions.items():
                position_size = float(pos["market_value"]) / self.equity
                if position_size > self.config.risk_max_position_size:
                    msg = f"Maximum position size limit breached for {symbol}"
                    msg += f": {position_size:.2%}"
                    logger.warning(msg)
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return True

    def _stop_trading(self) -> None:
        """Stop trading and close all positions."""
        logger.warning("Stopping trading due to risk limits breach")
        self.is_trading = False
        self._close_all_positions()

    def _reduce_position(self, symbol: str, target_size: float) -> None:
        """Reduce position size to target size."""
        try:
            position = self.positions.get(symbol)
            if position:
                current_size = float(position.get("size", 0))
                reduce_size = current_size - target_size
                if reduce_size > 0:
                    qty_to_sell = max(1, int(reduce_size))
                    self.submit_order(
                        symbol=symbol,
                        qty=qty_to_sell,
                        side=OrderSide.SELL if position["side"] == "long" else OrderSide.BUY,
                        type=OrderType.MARKET,
                        time_in_force=TimeInForce.DAY,
                    )
        except Exception as e:
            logger.error(f"Error reducing position for {symbol}: {e}")

    def _close_position(self, symbol: str) -> None:
        """Close a specific position."""
        try:
            position = self.positions.get(symbol)
            if position:
                shares = max(1, int(position.get("size", 0)))
                if shares <= 0:
                    return
                self.submit_order(
                    symbol=symbol,
                    qty=shares,
                    side=OrderSide.SELL if position["side"] == "long" else OrderSide.BUY,
                    type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY,
                )
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")

    def _close_all_positions(self) -> None:
        """Close all open positions."""
        for symbol in list(self.positions.keys()):
            self._close_position(symbol)

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        type: OrderType,
        time_in_force: TimeInForce,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> None:
        """Submit a new order."""
        try:
            order = self.alpaca_service.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
            self.orders[order["id"]] = order
            logger.info(f"Order submitted: {order}")
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            raise

    def submit_bracket_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        take_profit_price: float,
        stop_loss_price: float,
        time_in_force: TimeInForce = TimeInForce.GTC,
        order_type: OrderType = OrderType.MARKET,
        entry_limit_price: float | None = None,
    ) -> None:
        """Submit a bracket order with take-profit and stop-loss legs."""

        try:
            order = self.alpaca_service.submit_bracket_order(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                limit_price=entry_limit_price,
                take_profit_limit_price=take_profit_price,
                stop_loss_stop_price=stop_loss_price,
            )
            self.orders[order["id"]] = order
            logger.info("Bracket order submitted: %s", order["id"])
        except Exception as exc:
            logger.error(f"Error submitting bracket order: {exc}")
            raise

    def execute_trade(self, symbol: str, signal: dict[str, Any]) -> None:
        """Execute a trade based on the signal."""
        try:
            # Get current position
            position = self.positions.get(symbol)

            # Calculate position size
            risk_fraction = getattr(self.config, "risk_per_trade", 0.01)
            account = self.alpaca_service.get_account()
            portfolio_value = float(account.get("portfolio_value", self.equity))
            if not self.risk_manager.check_drawdown_limit(portfolio_value):
                self.add_status_message("Max drawdown exceeded. No new trades.", "warning")
                return
            if not self.risk_manager.check_daily_loss_limit(portfolio_value):
                self.add_status_message("Daily loss limit reached. Halting trades.", "warning")
                return

            position_size = self.strategy.calculate_position_size(
                price=float(signal["price"]),
                risk_amount=self.equity * risk_fraction,
            )
            risk_amount = self.risk_manager.risk_per_trade * portfolio_value
            risk_limited = self.risk_manager.calculate_position_size(
                price=float(signal["price"]),
                risk_amount=risk_amount,
                portfolio_value=portfolio_value,
            )
            win_rate = self.get_win_rate() or 0.5
            reward_risk = 2.0
            kelly_size = self.risk_manager.position_size_kelly(
                price=float(signal["price"]),
                portfolio_value=portfolio_value,
                win_rate=max(min(win_rate, 0.99), 0.01),
                reward_risk=reward_risk,
            )

            if position:
                # Check if we should close the position
                if self.strategy.should_close_position(price=float(signal["price"])):
                    self._close_position(symbol)
                    logger.info(f"Closed position for {symbol}")
            else:
                # Check if we should open a new position
                if self.strategy.should_open_position(price=float(signal["price"])):
                    # Get stop loss and take profit levels
                    stop_loss = self.strategy.get_stop_loss(price=float(signal["price"]))
                    take_profit = self.strategy.get_take_profit(price=float(signal["price"]))

                    # Submit the order
                    quantity = max(1, int(min(position_size, risk_limited, kelly_size)))
                    side = OrderSide.BUY if signal.get("side", "long") == "long" else OrderSide.SELL
                    if stop_loss and take_profit:
                        self.submit_bracket_order(
                            symbol=symbol,
                            qty=quantity,
                            side=side,
                            take_profit_price=float(take_profit),
                            stop_loss_price=float(stop_loss),
                            time_in_force=TimeInForce.GTC,
                        )
                    else:
                        self.submit_order(
                            symbol=symbol,
                            qty=quantity,
                            side=side,
                            type=OrderType.MARKET,
                            time_in_force=TimeInForce.DAY,
                            stop_price=stop_loss if stop_loss else None,
                            limit_price=take_profit if take_profit else None,
                        )
                    logger.info(f"Opened new position for {symbol}")
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")

    def run(self) -> None:
        """Run the trading bot."""
        try:
            while self.is_trading:
                # Update bot state
                self.update_state()

                # Check if market is open
                if not self.market_clock["is_open"]:
                    logger.info("Market is closed")
                    continue

                # Check risk limits
                if self._check_risk_limits():
                    self._stop_trading()
                    continue

                # Get latest market data and generate signals
                for symbol in self.config.strategy_symbols:
                    bars = self.alpaca_service.get_bars(
                        symbol=symbol,
                        timeframe=self.config.strategy_timeframe,
                        start=datetime.now() - timedelta(days=self.config.lookback_days),
                        end=datetime.now(),
                    )

                    data_frame = self._convert_bars_to_dataframe(symbol, bars)
                    if data_frame is None:
                        continue

                    signals = self.strategy.generate_signals(data_frame)

                    for signal in signals:
                        signal.setdefault("price", float(data_frame["close"].iloc[-1]))
                        self.execute_trade(symbol, signal)

                logger.info("Trading iteration completed")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            self._stop_trading()
            raise

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> BarSet | None:
        """Get historical bars for a symbol."""
        try:
            bars_dict = self.alpaca_service.get_bars(
                symbol=symbol,
                timeframe=TimeFrame(timeframe),
                start=start,
                end=end,
                limit=limit,
            )
            if not bars_dict:
                return None
            symbol_bars = bars_dict.get(symbol)
            if not symbol_bars:
                return None
            bar_objects = [
                Bar(
                    timestamp=datetime.fromisoformat(str(bar["timestamp"])),
                    open=float(bar["open"]),
                    high=float(bar["high"]),
                    low=float(bar["low"]),
                    close=float(bar["close"]),
                    volume=int(float(bar["volume"])),
                )
                for bar in symbol_bars
            ]
            return BarSet(bars=bar_objects)
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return None

    def process_trade(self, trade: dict[str, Any]) -> None:
        """Process a new trade."""
        try:
            # Extract trade information
            symbol = trade.get("symbol")
            price = float(trade.get("price", 0))
            size = float(trade.get("size", 0))
            side = trade.get("side", "").lower()

            # Update position and calculate P&L
            if symbol in self.positions:
                position = self.positions[symbol]
                if side == "buy":
                    position["size"] += size
                    position["avg_price"] = (
                        position["avg_price"] * (position["size"] - size) + price * size
                    ) / position["size"]
                else:
                    position["size"] -= size
                    if position["size"] <= 0:
                        del self.positions[symbol]

                # Calculate P&L
                if position["size"] > 0:
                    pnl = (price - position["avg_price"]) * position["size"]
                    position["pnl"] = pnl
                    self.total_pnl += pnl
        except Exception as e:
            logger.error(f"Error processing trade: {e}")

    def get_win_rate(self) -> float:
        """Get the win rate as a percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
