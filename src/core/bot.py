"""Trading bot module for executing trading strategies."""

from typing import List, Dict, Optional, Any
from datetime import datetime
import time
import secrets  # For secure random number generation

from src.core.strategy import Strategy
from src.core.portfolio import Portfolio
from src.core.position import Position
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TradingBot:
    """Trading bot class for executing trading strategies."""
    
    def __init__(
        self,
        strategy: Strategy,
        symbols: List[str],
        initial_capital: float = 100000.0
    ) -> None:
        """Initialize trading bot.
        
        Args:
            strategy: Trading strategy to use
            symbols: List of trading symbols
            initial_capital: Initial capital for trading
        """
        self.strategy = strategy
        self.symbols = symbols
        self.portfolio = Portfolio(initial_capital)
        self.positions: Dict[str, Position] = {}
        self._last_trade_time: datetime = datetime.now()
        self._is_running: bool = False
        
    def start(self) -> None:
        """Start the trading bot."""
        logger.info("Starting trading bot...")
        self._is_running = True
        
    def stop(self) -> None:
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self._is_running = False
        
    def _run(self) -> None:
        """Run one iteration of the trading bot."""
        if not self._is_running:
            return
            
        try:
            # Check for new trading signals
            for symbol in self.symbols:
                if symbol in self.positions:
                    # Check if position should be closed
                    if self._should_close_position(symbol):
                        self._close_position(symbol)
                else:
                    # Check if new position should be opened
                    if self._should_open_position(symbol):
                        self._open_position(symbol)
                        
            # Update portfolio value
            self.portfolio.update_value(self.positions)
            
        except Exception as e:
            logger.error(f"Error in bot iteration: {e}")
            
    def _should_open_position(self, symbol: str) -> bool:
        """Check if a new position should be opened.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position should be opened, False otherwise
        """
        # Generate a secure random number between 0 and 1
        random_value = secrets.randbelow(100) / 100.0
        return random_value < 0.1 and len(self.positions) < 5
        
    def _should_close_position(self, symbol: str) -> bool:
        """Check if a position should be closed.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position should be closed, False otherwise
        """
        # Generate a secure random number between 0 and 1
        random_value = secrets.randbelow(100) / 100.0
        return random_value < 0.1
        
    def _open_position(self, symbol: str) -> None:
        """Open a new position.
        
        Args:
            symbol: Trading symbol
        """
        try:
            # Calculate position size (10% of portfolio)
            position_size = self.portfolio.current_balance * 0.1
            
            # Create new position
            position = Position(
                symbol=symbol,
                size=position_size,
                entry_price=100.0,  # Mock price
                entry_time=datetime.now()
            )
            
            # Add to positions
            self.positions[symbol] = position
            self._last_trade_time = datetime.now()
            
            logger.info(f"Opened position: {position}")
            
        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {e}")
            
    def _close_position(self, symbol: str) -> None:
        """Close an existing position.
        
        Args:
            symbol: Trading symbol
        """
        try:
            if symbol in self.positions:
                position = self.positions.pop(symbol)
                # Update portfolio with position P&L
                self.portfolio.update_with_trade(position)
                self._last_trade_time = datetime.now()
                
                logger.info(f"Closed position: {position}")
                
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.
        
        Returns:
            Dictionary with bot status information
        """
        return {
            "is_running": self._is_running,
            "portfolio_value": self.portfolio.current_balance,
            "active_positions": len(self.positions),
            "last_trade_time": self._last_trade_time.isoformat(),
            "positions": [pos.to_dict() for pos in self.positions.values()]
        }
