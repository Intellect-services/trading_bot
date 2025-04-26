"""Trading bot module."""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
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
        self.positions: Dict[str, Dict[str, Union[float, datetime]]] = {}
        self.symbols: List[str] = []
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
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            logger.error("Invalid quantity: %s", quantity)
            return False
            
        if not isinstance(price, (int, float)) or price <= 0:
            logger.error("Invalid price: %s", price)
            return False
            
        if action not in ["buy", "sell"]:
            logger.error("Invalid action: %s", action)
            return False

        try:
            # Check risk management
            position = self.positions.get(symbol, {})
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
            if symbol in self.positions:
                current_position = self.positions[symbol]
                quantity_value = current_position.get("quantity")
                if not isinstance(quantity_value, (int, float)):
                    logger.error("Invalid position quantity type")
                    return False
                current_quantity = float(quantity_value)
                new_quantity = current_quantity + (quantity if action == "buy" else -quantity)
                
                if abs(new_quantity) < 1e-8:  # Close to zero
                    del self.positions[symbol]
                else:
                    self.positions[symbol] = {
                        "quantity": new_quantity,
                        "entry_price": price,
                        "timestamp": datetime.now(),
                    }
            else:
                if action == "buy":
                    self.positions[symbol] = {
                        "quantity": quantity,
                        "entry_price": price,
                        "timestamp": datetime.now(),
                    }

            logger.info(
                "Executed %s trade: %s %s @ %s",
                action, quantity, symbol, price
            )
            return True

        except Exception as e:
            logger.error("Error executing trade: %s", e)
            return False

    def get_position(self, symbol: str) -> Optional[Dict[str, Union[float, datetime]]]:
        """Get current position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position dictionary if exists, None otherwise
        """
        return self.positions.get(symbol)

    def generate_signals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals from market data.
        
        Args:
            data: Market data dictionary
            
        Returns:
            Dictionary containing trading signals
        """
        try:
            if not data:
                logger.warning("Empty data received for signal generation")
                return {}
                
            # Convert data to DataFrame
            df = pd.DataFrame([data])
            
            # Generate signals using strategy
            signals = self.strategy.generate_signals(df)
            
            if signals.empty:
                logger.warning("No signals generated")
                return {}
                
            # Return the latest signal
            return signals.iloc[-1].to_dict()
            
        except Exception as e:
            logger.error("Error generating signals: %s", e)
            return {}

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to trade.
        
        Args:
            symbol: Stock symbol to trade
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.data_feed.add_symbol(symbol)
            logger.info(f"Added symbol: {symbol}")

    def start(self) -> None:
        """Start the trading bot."""
        try:
            logger.info("Starting trading bot")
            
            # Initialize data for each symbol
            for symbol in self.symbols:
                self._initialize_symbol(symbol)
            
            # Start data feed
            self.data_feed.add_callback(self._on_data_update_wrapper)
            logger.info("Trading bot started")
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")

    def stop(self) -> None:
        """Stop the trading bot."""
        try:
            logger.info("Stopping trading bot")
            # Cleanup code here
            logger.info("Trading bot stopped")
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")

    def _initialize_symbol(self, symbol: str) -> None:
        """Initialize data for a symbol.
        
        Args:
            symbol: Stock symbol to initialize
        """
        try:
            # Get historical data
            data = self.data_feed.get_historical_data(symbol)
            if data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return
            
            # Initialize strategy
            self.strategy.initialize_symbol(symbol, data)
            logger.info(f"Initialized {symbol}")
        except Exception as e:
            logger.error(f"Error initializing {symbol}: {e}")

    def _on_data_update_wrapper(self, symbol: str, data: pd.DataFrame) -> None:
        """Wrapper for data update callback to convert DataFrame to dict.
        
        Args:
            symbol: Updated symbol
            data: New market data
        """
        try:
            if data.empty:
                return
            latest_data = data.iloc[-1].to_dict()
            latest_data["timestamp"] = data.index[-1]
            self._on_data_update(symbol, latest_data)
        except Exception as e:
            logger.error(f"Error in data update wrapper: {e}")

    def _on_data_update(self, symbol: str, data: Dict[str, Any]) -> None:
        """Handle data updates.
        
        Args:
            symbol: Updated symbol
            data: New market data
        """
        try:
            # Get trading signal
            signal = self.strategy.generate_signals(pd.DataFrame([data])).iloc[-1]["signal"]
            if signal is None:
                return
            
            # Check risk management
            position = self.portfolio.get_position(symbol) or {}
            if not self.risk_manager.apply_risk_management(
                price=float(data["close"]),
                position=position,
                account_value=self.portfolio.get_value()
            ):
                logger.warning("Risk check failed for %s", symbol)
                return
            
            # Execute trade
            self._execute_trade(symbol, signal, data)
        except Exception as e:
            logger.error("Error handling data update: %s", e)

    def _execute_trade(self, symbol: str, signal: int, data: Dict[str, Any]) -> None:
        """Execute a trade based on signal.
        
        Args:
            symbol: Symbol to trade
            signal: Trading signal (1: buy, -1: sell, 0: hold)
            data: Current market data
        """
        try:
            if signal == 0:
                return
            
            # Get current position
            position = self.portfolio.get_position(symbol)
            
            # Calculate position size
            size = self.portfolio.calculate_position_size(float(data["close"]))
            if size == 0:
                logger.warning(f"Position size is 0 for {symbol}")
                return
            
            # Execute order
            if signal > 0 and (position is None or position["size"] < size):
                # Buy or increase position
                order = self.portfolio.execute_order(
                    symbol=symbol,
                    qty=size - (position["size"] if position else 0),
                    side="buy",
                    price=float(data["close"])
                )
                logger.info(f"Buy order submitted for {symbol}: {order}")
            elif signal < 0 and position is not None and position["size"] > 0:
                # Sell or decrease position
                order = self.portfolio.execute_order(
                    symbol=symbol,
                    qty=position["size"],
                    side="sell",
                    price=float(data["close"])
                )
                logger.info(f"Sell order submitted for {symbol}: {order}")
        except Exception as e:
            logger.error(f"Error executing trade: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.
        
        Returns:
            Dictionary containing bot status
        """
        try:
            return {
                "symbols": self.symbols,
                "portfolio": self.portfolio.get_summary(),
                "risk_metrics": {
                    "max_position_size": self.config.RISK_MAX_POSITION_SIZE,
                    "stop_loss_pct": self.config.RISK_STOP_LOSS_PCT,
                    "max_drawdown": self.config.RISK_MAX_DRAWDOWN,
                    "risk_per_trade": self.config.RISK_PER_TRADE
                }
            }
        except Exception as e:
            logger.error("Error getting bot status: %s", e)
            return {}

    def run(self) -> None:
        """Run the trading bot."""
        try:
            logger.info("Running trading bot")
            
            # Get latest data for each symbol
            for symbol in self.symbols:
                data = self.data_feed.get_latest_data(symbol)
                if data is not None:
                    self._on_data_update(symbol, data)
            
            logger.info("Trading bot run completed")
        except Exception as e:
            logger.error(f"Error running trading bot: {e}")

    def get_portfolio_value(self) -> float:
        """Get current portfolio value.
        
        Returns:
            Current portfolio value
        """
        try:
            return self.portfolio.get_value()
        except Exception as e:
            logger.error(f"Error getting portfolio value: {e}")
            return 0.0
