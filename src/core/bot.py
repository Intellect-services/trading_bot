"""Trading bot module for executing trading strategies."""

import logging
import secrets  # For secure random number generation
import time
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Union, cast

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import Bar
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.models import TradeAccount
from alpaca.trading.requests import MarketOrderRequest

from src.core.portfolio import Portfolio
from src.core.position import Position
from src.core.strategy import Strategy
from src.strategies.base import BaseStrategy
from src.utils.config import Config
from src.utils.helpers import calculate_position_size
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class that manages trading operations."""

    def __init__(
        self,
        config: Config,
        strategy: BaseStrategy,
        portfolio: Optional[Portfolio] = None,
        data_feed: Optional[Any] = None,
        risk_manager: Optional[Any] = None,
    ) -> None:
        """Initialize the trading bot.

        Args:
            config: Configuration object
            strategy: Trading strategy to use
            portfolio: Portfolio manager (optional)
            data_feed: Data feed provider (optional)
            risk_manager: Risk management system (optional)
        """
        self.config = config
        self.strategy = strategy
        self.portfolio = portfolio
        self.data_feed = data_feed
        self.risk_manager = risk_manager
        self.trading_client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=config.ALPACA_PAPER,
        )
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY, secret_key=config.ALPACA_SECRET_KEY
        )
        self.positions: Dict[str, AlpacaPosition] = {}
        self.is_running: bool = False
        self.symbols: List[str] = []
        self.initial_capital: float = 0.0
        logger.info("Trading bot initialized")

    def start(self) -> None:
        """Start the trading bot."""
        if not self.config.is_valid:
            raise ValueError("Invalid configuration")

        self.is_running = True
        logger.info("Trading bot started")

        # Initialize positions
        self._update_positions()

    def stop(self) -> None:
        """Stop the trading bot."""
        self.is_running = False
        logger.info("Trading bot stopped")

    def _update_positions(self) -> None:
        """Update current positions from Alpaca."""
        try:
            positions = self.trading_client.get_all_positions()
            self.positions = {
                position.symbol: position
                for position in positions
                if isinstance(position, AlpacaPosition)
            }
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            self.positions = {}

    def get_position(self, symbol: str) -> Optional[AlpacaPosition]:
        """Get position for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position object if exists, None otherwise
        """
        return self.positions.get(symbol)

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the trading bot.

        Returns:
            Dictionary containing bot status information
        """
        return {
            "running": self.is_running,
            "positions": len(self.positions),
            "strategy": self.strategy.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get trading metrics.

        Returns:
            Dictionary containing trading metrics
        """
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self._get_current_capital(),
            "total_trades": self._get_total_trades(),
            "win_rate": self._get_win_rate(),
            "profit_factor": self._get_profit_factor(),
            "sharpe_ratio": self._get_sharpe_ratio(),
            "active_positions": len(self.positions),
        }

    def _get_current_capital(self) -> float:
        """Get current capital from Alpaca account."""
        try:
            account = self.trading_client.get_account()
            if isinstance(account, TradeAccount) and account.cash is not None:
                return float(account.cash)
            return 0.0
        except Exception as e:
            logger.error(f"Error getting current capital: {e}")
            return 0.0

    def _get_total_trades(self) -> int:
        """Get total number of trades."""
        # TODO: Implement proper trade counting
        return 0

    def _get_win_rate(self) -> float:
        """Get win rate as a percentage."""
        # TODO: Implement proper win rate calculation
        return 0.0

    def _get_profit_factor(self) -> float:
        """Get profit factor."""
        # TODO: Implement proper profit factor calculation
        return 0.0

    def _get_sharpe_ratio(self) -> float:
        """Get Sharpe ratio."""
        # TODO: Implement proper Sharpe ratio calculation
        return 0.0

    def execute_trade(self, symbol: str, side: OrderSide, quantity: float) -> Optional[Order]:
        """Execute a trade.

        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Number of shares

        Returns:
            Order object if successful, None otherwise
        """
        try:
            order_data = MarketOrderRequest(
                symbol=symbol, qty=quantity, side=side, time_in_force=TimeInForce.DAY
            )
            order = cast(Order, self.trading_client.submit_order(order_data))
            logger.info(f"Order submitted: {order}")
            return order
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def get_historical_data(
        self, symbol: str, timeframe: TimeFrame, limit: int = 100
    ) -> Optional[List[Bar]]:
        """Get historical price data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe for the data
            limit: Number of bars to retrieve

        Returns:
            List of historical bars if successful, None otherwise
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol, timeframe=timeframe, limit=limit
            )
            bars = self.data_client.get_stock_bars(request_params)
            return list(bars[symbol]) if bars else None
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track.

        Args:
            symbol: Trading symbol to add
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"Added symbol: {symbol}")

    def _run(self) -> None:
        """Main trading loop."""
        while self.is_running:
            try:
                # Update positions
                self._update_positions()

                # Get market data for all symbols
                for symbol in self.symbols:
                    data = self.get_historical_data(symbol, TimeFrame.Minute, limit=100)
                    if data:
                        # Generate signals
                        signals = self.strategy.generate_signals(pd.DataFrame(data))
                        if signals is not None:
                            # Execute trades based on signals
                            self._execute_signals(symbol, signals)

                # Sleep for a short time
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(5)

    def _execute_signals(self, symbol: str, signals: pd.DataFrame) -> None:
        """Execute trades based on signals.

        Args:
            symbol: Trading symbol
            signals: DataFrame containing trading signals
        """
        # TODO: Implement signal execution logic
        pass

    def backtest(self) -> Dict[str, Any]:
        """Run backtest simulation.

        Returns:
            Dict[str, Any]: Backtest results
        """
        try:
            from src.backtesting.engine import BacktestEngine

            # Get historical data for backtesting
            data = self.get_historical_data(
                symbol=self.symbols[0] if self.symbols else "SPY",
                timeframe=TimeFrame.Day,
                limit=1000,
            )
            if not data:
                raise ValueError("No historical data available for backtesting")

            # Convert data to DataFrame
            df = pd.DataFrame(
                {
                    "timestamp": [bar.timestamp for bar in data],
                    "open": [float(bar.open) for bar in data],
                    "high": [float(bar.high) for bar in data],
                    "low": [float(bar.low) for bar in data],
                    "close": [float(bar.close) for bar in data],
                    "volume": [float(bar.volume) for bar in data],
                }
            )
            df.set_index("timestamp", inplace=True)

            engine = BacktestEngine(
                strategy=cast(Strategy, self.strategy),
                initial_capital=self.config.INITIAL_CAPITAL,
            )

            # Run backtest
            results = engine.run(data=df)

            # Add additional metrics
            results.update(
                {
                    "strategy": self.strategy.__class__.__name__,
                    "initial_capital": self.config.INITIAL_CAPITAL,
                    "risk_settings": {
                        "max_position_size": self.config.RISK_MAX_POSITION_SIZE,
                        "stop_loss_pct": self.config.RISK_STOP_LOSS_PCT,
                        "take_profit_pct": self.config.RISK_TAKE_PROFIT_PCT,
                        "max_drawdown": self.config.RISK_MAX_DRAWDOWN,
                        "max_leverage": self.config.RISK_MAX_LEVERAGE,
                        "risk_per_trade": self.config.RISK_PER_TRADE,
                    },
                }
            )

            return results

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
            }
