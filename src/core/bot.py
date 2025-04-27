"""Trading bot module."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import logging
from decimal import Decimal
import pytz
import threading
import time

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.logger import setup_logger
from src.core.alpaca_client import AlpacaClient

logger = setup_logger(__name__)


class Position(TypedDict):
    """Type definition for position data."""
    quantity: float
    entry_price: float
    timestamp: datetime


class TradingBot:
    """Trading bot for executing trading strategies."""

    def __init__(self, config: Config) -> None:
        """Initialize trading bot."""
        self.config = config
        self.client = AlpacaClient(config)
        self.data_feed = DataFeed(self.client)
        self.portfolio = Portfolio(config.INITIAL_BALANCE)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logger
        self.positions: Dict[str, Position] = {}
        self.symbols: List[str] = []
        logger.info("Trading bot initialized with capital: %s", self.portfolio.current_balance)

    def start(self) -> None:
        """Start the trading bot."""
        if not self._running:
            self._running = True
            self.data_feed.start()
            self._thread = threading.Thread(target=self._run)
            self._thread.daemon = True
            self._thread.start()
            self.logger.info("Started trading bot")

    def stop(self) -> None:
        """Stop the trading bot."""
        if self._running:
            self._running = False
            self.data_feed.stop()
            if self._thread:
                self._thread.join()
            self.logger.info("Stopped trading bot")

    def _run(self) -> None:
        """Run the trading bot loop."""
        while self._running:
            try:
                # Update portfolio
                self._update_portfolio()
                
                # Generate signals
                signals = self.generate_signals()
                
                # Execute trades based on signals
                for symbol, action in signals.items():
                    if action == 'buy':
                        self._execute_buy(symbol)
                    elif action == 'sell':
                        self._execute_sell(symbol)
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in trading bot loop: {e}")
                time.sleep(60)  # Wait before retrying

    def _update_portfolio(self) -> None:
        """Update portfolio with latest prices."""
        try:
            positions = self.client.get_positions()
            for position in positions:
                symbol = position['symbol']
                price = self.data_feed.get_latest_price(symbol)
                if price is not None:
                    self.portfolio.update_position(symbol, position['qty'], price)
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")

    def _execute_buy(self, symbol: str) -> None:
        """Execute a buy order."""
        try:
            price = self.data_feed.get_latest_price(symbol)
            if price is None:
                return
            
            # Calculate position size
            position_size = self.portfolio.calculate_position_size(symbol, price)
            if position_size <= 0:
                return
            
            # Submit order
            order = self.client.submit_order(
                symbol=symbol,
                qty=position_size,
                side='buy',
                type='market'
            )
            
            if order:
                self.logger.info(f"Executed buy order for {symbol}: {order}")
        except Exception as e:
            self.logger.error(f"Error executing buy order for {symbol}: {e}")

    def _execute_sell(self, symbol: str) -> None:
        """Execute a sell order."""
        try:
            position = self.portfolio.get_position(symbol)
            if not position or position['quantity'] <= 0:
                return
            
            # Submit order
            order = self.client.submit_order(
                symbol=symbol,
                qty=position['quantity'],
                side='sell',
                type='market'
            )
            
            if order:
                self.logger.info(f"Executed sell order for {symbol}: {order}")
        except Exception as e:
            self.logger.error(f"Error executing sell order for {symbol}: {e}")

    def generate_signals(self) -> Dict[str, str]:
        """Generate trading signals."""
        signals: Dict[str, str] = {}
        try:
            for symbol in self.data_feed.symbols:
                df = self.data_feed.get_latest_data(symbol)
                if df.empty:
                    continue
                
                # Simple moving average crossover strategy
                if df['sma_20'].iloc[-1] > df['sma_50'].iloc[-1] and df['sma_20'].iloc[-2] <= df['sma_50'].iloc[-2]:
                    signals[symbol] = 'buy'
                elif df['sma_20'].iloc[-1] < df['sma_50'].iloc[-1] and df['sma_20'].iloc[-2] >= df['sma_50'].iloc[-2]:
                    signals[symbol] = 'sell'
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
        return signals

    def get_account_info(self) -> Dict[str, float]:
        """Get current account information.

        Returns:
            Dictionary with account info
        """
        try:
            return {
                "equity": self.portfolio.current_balance,
                "cash": self.portfolio.current_balance,
                "buying_power": self.portfolio.current_balance * 2,  # Assuming 2x leverage
            }
        except Exception as e:
            logger.error("Error getting account info: %s", e)
            return {"equity": 0.0, "cash": 0.0, "buying_power": 0.0}

    def _validate_trade_params(
        self,
        quantity: float,
        price: float,
        action: str,
    ) -> bool:
        """Validate trade parameters.

        Args:
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)

        Returns:
            True if parameters are valid, False otherwise
        """
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            logger.error("Invalid quantity: %s", quantity)
            return False
            
        if not isinstance(price, (int, float)) or price <= 0:
            logger.error("Invalid price: %s", price)
            return False
            
        if action not in ["buy", "sell"]:
            logger.error("Invalid action: %s", action)
            return False
            
        return True

    def _update_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        action: str,
    ) -> None:
        """Update position for a symbol.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)
        """
        if symbol in self.positions:
            current_position = self.positions[symbol]
            current_quantity = current_position["quantity"]
            new_quantity = current_quantity + (quantity if action == "buy" else -quantity)
            
            if abs(new_quantity) < 1e-8:  # Close to zero
                del self.positions[symbol]
            else:
                self.positions[symbol] = {
                    "quantity": new_quantity,
                    "entry_price": price,
                    "timestamp": datetime.now()
                }
        else:
            if action == "buy":
                self.positions[symbol] = {
                    "quantity": quantity,
                    "entry_price": price,
                    "timestamp": datetime.now()
                }

    def execute_trade(
        self,
        symbol: str,
        quantity: float,
        price: float,
        action: str,
    ) -> bool:
        """Execute a trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)

        Returns:
            True if trade executed successfully, False otherwise
        """
        if not self._validate_trade_params(quantity, price, action):
            return False

        try:
            # Check risk management
            position = self.positions.get(symbol)
            if position and not self.risk_manager.apply_risk_management(
                price=price,
                position=position,
                account_value=self.portfolio.current_balance,
            ):
                logger.warning("Trade rejected by risk management")
                return False

            # Update portfolio
            if not self.portfolio.execute_order(
                symbol=symbol,
                qty=quantity,
                side=action,
                price=price
            ):
                logger.error("Failed to update portfolio")
                return False

            # Update positions
            self._update_position(symbol, quantity, price, action)

            logger.info(
                "Executed %s trade: %s %s @ %s",
                action, quantity, symbol, price
            )
            return True

        except Exception as e:
            logger.error("Error executing trade: %s", e)
            return False

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position dictionary if exists, None otherwise
        """
        return self.positions.get(symbol)

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track.

        Args:
            symbol: Trading symbol
        """
        try:
            if symbol not in self.symbols:
                self.symbols.append(symbol)
                self.data_feed.add_symbol(symbol)
                logger.info(f"Added symbol: {symbol}")
        except Exception as e:
            logger.error(f"Error adding symbol {symbol}: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.

        Returns:
            Dictionary containing bot status information
        """
        return {
            "running": self._running,
            "symbols": self.symbols,
            "positions": self.positions,
            "portfolio_value": self.portfolio.current_balance,
            "num_trades": len(self.portfolio.trades)
        }

    def get_portfolio_value(self) -> float:
        """Get current portfolio value.

        Returns:
            Current portfolio value
        """
        return self.portfolio.current_balance
