"""Trading bot module."""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union, TypedDict, cast
import pandas as pd
import logging
from decimal import Decimal

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.logger import setup_logger

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
        config: Config,
        strategy: Strategy,
        risk_manager: RiskManager,
        data_feed: Optional[DataFeed] = None,
        portfolio: Optional[Portfolio] = None,
        initial_capital: Optional[float] = None,
    ):
        """Initialize trading bot.

        Args:
            config: Configuration instance
            strategy: Trading strategy instance
            risk_manager: Risk management instance
            data_feed: Optional data feed instance
            portfolio: Optional portfolio instance
            initial_capital: Optional initial capital amount (overrides config)
        """
        self.config = config
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.data_feed = data_feed or DataFeed(config)
        self.portfolio = portfolio or Portfolio(initial_capital or config.INITIAL_BALANCE)
        self.positions: Dict[str, Position] = {}
        self.symbols: List[str] = []
        self.running: bool = False
        logger.info("Trading bot initialized with capital: %s", self.portfolio.current_balance)

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
            position = cast(Dict[str, Any], self.positions.get(symbol, {}))
            if not self.risk_manager.apply_risk_management(
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

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Generate trading signals from data.

        Args:
            data: Market data DataFrame

        Returns:
            Dictionary of signal types and values
        """
        try:
            signals = self.strategy.generate_signals(data)
            if isinstance(signals, pd.DataFrame):
                return signals.iloc[-1].to_dict()
            return signals
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return {}

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

    def start(self) -> None:
        """Start the trading bot."""
        try:
            self.running = True
            self.data_feed.add_callback(self._on_data_update_wrapper)
            self.data_feed.start()
            logger.info("Trading bot started")
        except Exception as e:
            logger.error(f"Error starting trading bot: {str(e)}")
            self.running = False

    def stop(self) -> None:
        """Stop the trading bot."""
        try:
            self.running = False
            self.data_feed.stop()
            logger.info("Trading bot stopped")
        except Exception as e:
            logger.error(f"Error stopping trading bot: {str(e)}")

    def _on_data_update_wrapper(self, symbol: str, data: pd.DataFrame) -> None:
        """Wrapper for data update callback.

        Args:
            symbol: Trading symbol
            data: Market data DataFrame
        """
        if not self.running:
            return

        try:
            signals = self.generate_signals(data)
            self._on_data_update(symbol, signals)
        except Exception as e:
            logger.error(f"Error in data update wrapper: {str(e)}")

    def _on_data_update(self, symbol: str, signals: Dict[str, str]) -> None:
        """Handle data updates and execute trades.

        Args:
            symbol: Trading symbol
            signals: Dictionary of trading signals
        """
        try:
            if not self.running:
                return

            position = self.get_position(symbol)
            latest_price = self.data_feed.get_latest_price(symbol)

            if not latest_price:
                logger.warning(f"No price data available for {symbol}")
                return

            if signals.get('action') == 'buy' and (not position or position['quantity'] <= 0):
                self.execute_trade(symbol, 1.0, latest_price, 'buy')
            elif signals.get('action') == 'sell' and position and position['quantity'] > 0:
                self.execute_trade(symbol, position['quantity'], latest_price, 'sell')

        except Exception as e:
            logger.error(f"Error handling data update: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.

        Returns:
            Dictionary containing bot status information
        """
        return {
            "running": self.running,
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
