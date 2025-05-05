"""Trading bot module for executing trading strategies."""

import logging
import secrets  # For secure random number generation
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import alpaca_trade_api as tradeapi
import pandas as pd
from alpaca_trade_api.entity import Bar
from alpaca_trade_api.rest import REST

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Asset
from src.core.alpaca_types import Bar as AlpacaBar
from src.core.alpaca_types import BarSet, Clock, Order, OrderSide, OrderType
from src.core.alpaca_types import Position as AlpacaPosition
from src.core.alpaca_types import TimeInForce, TradeAccount
from src.core.portfolio import Portfolio
from src.core.position import Position
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.strategies.base import BaseStrategy
from src.utils.config import Config
from src.utils.helpers import calculate_position_size
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class that manages trading operations."""

    def __init__(self, config: Config, strategy: Strategy, alpaca_service: AlpacaService):
        """Initialize the trading bot."""
        self.config = config
        self.strategy = strategy
        self.alpaca_service = alpaca_service

        # Initialize state
        self.account: Dict[str, Any] = self.alpaca_service.get_account()
        self.equity = float(self.account["equity"])
        self.cash = float(self.account["cash"])
        self.buying_power = float(self.account["buying_power"])

        # Initialize portfolio and risk manager
        self.portfolio = Portfolio(self.equity)
        self.risk_manager = RiskManager(self.equity)

        # Trading state
        self.is_trading = True
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.market_clock: Dict[str, Any] = {}

        # Performance tracking
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_trades = 0
        self.total_pnl = 0.0

        logger.info("Trading bot initialized")

    def update_state(self) -> None:
        """Update the bot's state with latest market data."""
        try:
            # Update account information
            self.account = self.alpaca_service.get_account()
            self.equity = float(self.account["equity"])
            self.cash = float(self.account["cash"])
            self.buying_power = float(self.account["buying_power"])

            # Update positions
            positions = self.alpaca_service.get_positions()
            self.positions = {pos["symbol"]: pos for pos in positions}

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
            current_drawdown = (
                self.portfolio.peak_equity - self.equity
            ) / self.portfolio.peak_equity
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
            for pos in self.positions.values():
                position_size = float(pos["market_value"]) / self.equity
                if position_size > self.config.risk_max_position_size:
                    logger.warning(
                        f"Maximum position size limit breached for {pos['symbol']}: {position_size:.2%}"
                    )
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
                current_size = float(position["qty"])
                reduce_size = current_size - target_size
                if reduce_size > 0:
                    self.submit_order(
                        symbol=symbol,
                        qty=str(reduce_size),
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
                self.submit_order(
                    symbol=symbol,
                    qty=position["qty"],
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
        qty: str,
        side: OrderSide,
        type: OrderType,
        time_in_force: TimeInForce,
        limit_price: Optional[str] = None,
        stop_price: Optional[str] = None,
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

    def execute_trade(self, symbol: str, signal: Dict[str, Any]) -> None:
        """Execute a trade based on the signal."""
        try:
            # Get current position
            position = self.positions.get(symbol)

            # Calculate position size
            position_size = self.strategy.calculate_position_size(
                price=float(signal["price"]), risk_amount=self.equity * self.config.risk_per_trade
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
                    self.submit_order(
                        symbol=symbol,
                        qty=str(position_size),
                        side=OrderSide.BUY if signal["side"] == "long" else OrderSide.SELL,
                        type=OrderType.MARKET,
                        time_in_force=TimeInForce.DAY,
                        stop_price=str(stop_loss) if stop_loss else None,
                        limit_price=str(take_profit) if take_profit else None,
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
                    # Get historical data
                    bars = self.alpaca_service.get_bars(
                        symbol=symbol,
                        timeframe=self.config.strategy_timeframe,
                        start=datetime.now() - timedelta(days=self.config.lookback_days),
                        end=datetime.now(),
                    )

                    # Generate trading signals
                    signals = self.strategy.generate_signals(bars)

                    # Execute trades based on signals
                    for signal in signals:
                        self.execute_trade(symbol, signal)

                logger.info("Trading iteration completed")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            self._stop_trading()
            raise
