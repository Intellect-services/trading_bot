"""Trading bot module."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, TypedDict, cast
import pandas as pd
import logging
from decimal import Decimal
import pytz
import threading
import time
import numpy as np

from src.utils.config import Config
from src.core.strategy import Strategy  # noqa: F401
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.logger import setup_logger
from src.core.alpaca_client import AlpacaClient
from alpaca.trading.enums import OrderSide

logger = setup_logger(__name__)


class Position(TypedDict):
    """Type definition for position data."""
    quantity: float
    entry_price: float
    timestamp: datetime


class TradingBot:
    """Trading bot for executing trading strategies."""

    def __init__(
        self,
        strategy: Strategy,
        symbols: List[str],
        initial_capital: float = 100000.0
    ) -> None:
        """Initialize trading bot.

        Args:
            strategy: Trading strategy
            symbols: List of symbols to trade
            initial_capital: Initial capital
        """
        self.strategy = strategy
        self.symbols = symbols
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager()
        self.client = AlpacaClient()
        self.data_feed = DataFeed(self.client)
        self.logger = logger
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self.positions: Dict[str, Position] = {}
        
        # Initialize data storage
        self.data: Dict[str, pd.DataFrame] = {}
        self._initialize_data()

    def _initialize_data(self) -> None:
        """Initialize historical data."""
        for symbol in self.symbols:
            data = self.data_feed.get_historical_data(
                symbol,
                start=datetime.now() - pd.Timedelta(days=100),
                end=datetime.now()
            )
            if data.empty:
                self.logger.warning("No data found for %s", symbol)
                continue
            self.data[symbol] = data

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
                self.logger.error("Error in trading bot loop: %s", e)
                time.sleep(60)  # Wait before retrying

    def _update_portfolio(self) -> None:
        """Update portfolio with latest prices."""
        try:
            positions = self.client.get_all_positions()
            for symbol, position in positions.items():
                price = self.data_feed.get_latest_price(symbol)
                if price is not None:
                    self.portfolio.update_position(symbol, position['qty'], price, 'update')
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")

    def _execute_buy(self, symbol: str) -> None:
        """Execute a buy order."""
        try:
            price = self.data_feed.get_latest_price(symbol)
            if price is None:
                return
            
            # Calculate position size
            position_size = self.portfolio.calculate_position_size(price)
            if position_size <= 0:
                return
            
            # Submit order
            order = self.client.submit_order(
                symbol=symbol,
                qty=position_size,
                side=OrderSide.BUY,
                order_type="market"
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
                side=OrderSide.SELL,
                order_type="market"
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
                sma_20 = df['sma_20'].iloc[-1]
                sma_50 = df['sma_50'].iloc[-1]
                sma_20_prev = df['sma_20'].iloc[-2]
                sma_50_prev = df['sma_50'].iloc[-2]
                
                if sma_20 > sma_50 and sma_20_prev <= sma_50_prev:
                    signals[symbol] = 'buy'
                elif sma_20 < sma_50 and sma_20_prev >= sma_50_prev:
                    signals[symbol] = 'sell'
        except Exception as e:
            self.logger.error("Error generating signals: %s", e)
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

    def _validate_trade_params(self, quantity: float, price: float, action: str) -> bool:
        """Validate trade parameters.

        Args:
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)

        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            # Check if quantity is positive
            if quantity <= 0:
                self.logger.warning("Invalid quantity: %s", quantity)
                return False

            # Check if price is positive
            if price <= 0:
                self.logger.warning("Invalid price: %s", price)
                return False

            # Check if action is valid
            if action not in ['buy', 'sell']:
                self.logger.warning("Invalid action: %s", action)
                return False

            # Use risk_manager's validate_trade method
            current_prices = {symbol: self.data_feed.get_latest_price(symbol) or 0.0 for symbol in self.positions}
            portfolio_value = self.portfolio.calculate_portfolio_value(current_prices)
            return self.risk_manager.validate_trade(
                symbol="",  # Symbol not needed for basic validation
                quantity=quantity,
                price=price,
                portfolio_value=portfolio_value
            )

        except Exception as e:
            self.logger.error("Error validating trade parameters: %s", e)
            return False

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
            if position:
                position_dict = {
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price']
                }
            else:
                position_dict = None

            current_prices = {symbol: self.data_feed.get_latest_price(symbol) or 0.0 for symbol in self.positions}
            portfolio_value = self.portfolio.calculate_portfolio_value(current_prices)
            
            risk_check = self.risk_manager.apply_risk_management(
                price=price,
                position=position_dict,
                account_value=portfolio_value
            )
            
            if position and not risk_check:
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

            logger.info("Executed %s trade: %s %s @ %s", action, quantity, symbol, price)
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

    def _check_risk_management(self, symbol: str, price: float) -> bool:
        """Check if trade meets risk management criteria.

        Args:
            symbol: Trading symbol
            price: Current price

        Returns:
            True if trade meets risk criteria, False otherwise
        """
        try:
            # Get current position
            position = self.portfolio.get_position(symbol)
            
            # Get current portfolio value
            current_prices = {
                sym: float(self.data[sym].iloc[-1]['close'])
                for sym in self.symbols
                if not self.data[sym].empty
            }
            portfolio_value = self.portfolio.calculate_portfolio_value(current_prices)
            
            # Check risk management
            position_dict = None if position is None else {
                'size': float(position['quantity']),
                'avg_price': float(position['entry_price'])
            }
            
            return self.risk_manager.apply_risk_management(
                price=price,
                position=position_dict,
                account_value=portfolio_value
            )
            
        except Exception as e:
            self.logger.error("Error checking risk management: %s", e)
            return False
