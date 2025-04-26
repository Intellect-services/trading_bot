"""Backtesting engine module."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestingEngine:
    """Engine for backtesting trading strategies."""

    def __init__(
        self,
        config: Config,
        strategy: Strategy,
        data_feed: DataFeed,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.001
    ):
        """Initialize backtesting engine.
        
        Args:
            config: Configuration object
            strategy: Trading strategy to test
            data_feed: Data feed for historical data
            initial_capital: Initial capital (default: 100000.0)
            commission: Commission rate (default: 0.001)
            slippage: Slippage rate (default: 0.001)
        """
        self.config = config
        self.strategy = strategy
        self.data_feed = data_feed
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(config)
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.current_time: Optional[datetime] = None
        self.current_data: Dict[str, pd.DataFrame] = {}
        
        logger.info("Backtesting engine initialized")

    def run(self, symbol: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Run backtest simulation.
        
        Args:
            symbol: Symbol to backtest
            start: Start date
            end: End date
            
        Returns:
            Dictionary containing backtest results
        """
        try:
            logger.info(f"Starting backtest for {symbol} from {start} to {end}")
            
            # Get historical data
            data = self.data_feed.get_historical_data(
                symbol=symbol,
                lookback_days=(end - start).days,
                timeframe="1D"
            )
            if data.empty:
                logger.error("No historical data available")
                return {}
            
            # Initialize strategy
            self.strategy.initialize_symbol(symbol, data)
            
            # Run simulation
            for timestamp in data.index:
                self.current_time = timestamp
                row_data = data.loc[timestamp].to_dict()
                row_data["timestamp"] = timestamp
                self._update_portfolio(symbol, row_data)
            
            # Calculate performance metrics
            results = self._calculate_performance_metrics()
            logger.info("Backtest completed")
            return results
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {}

    def _update_portfolio(self, symbol: str, data: Dict[str, Any]) -> None:
        """Update portfolio based on new data.
        
        Args:
            symbol: Symbol being traded
            data: Current market data
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
                logger.debug("Risk check failed at %s", self.current_time)
                return
            
            # Execute trades
            self._execute_trades(symbol, signal, data)
        except Exception as e:
            logger.error("Error updating portfolio: %s", e)

    def _execute_trades(self, symbol: str, signal: int, data: Dict[str, Any]) -> None:
        """Execute trades based on signal.
        
        Args:
            symbol: Symbol to trade
            signal: Trading signal (1: buy, -1: sell, 0: hold)
            data: Current market data
        """
        try:
            if signal == 0:
                return
            
            position = self.portfolio.get_position(symbol)
            size = self.portfolio.calculate_position_size(float(data["close"]))
            
            if size == 0:
                logger.debug(f"Position size is 0 at {self.current_time}")
                return
            
            price = float(data["close"]) * (1 + self.slippage if signal > 0 else 1 - self.slippage)
            commission = price * size * self.commission
            
            if signal > 0 and (position is None or position["size"] < size):
                # Buy or increase position
                qty = size - (position["size"] if position else 0)
                cost = price * qty + commission
                
                if cost <= self.portfolio.get_balance():
                    self.portfolio.execute_order(
                        symbol=symbol,
                        qty=qty,
                        side="buy",
                        price=price
                    )
                    self.trades.append({
                        "timestamp": self.current_time,
                        "symbol": symbol,
                        "side": "buy",
                        "qty": qty,
                        "price": price,
                        "commission": commission,
                        "portfolio_value": self.portfolio.get_value()
                    })
                    logger.debug(f"Buy {qty} shares at {price} at {self.current_time}")
            
            elif signal < 0 and position is not None and position["size"] > 0:
                # Sell or decrease position
                qty = position["size"]
                self.portfolio.execute_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    price=price
                )
                self.trades.append({
                    "timestamp": self.current_time,
                    "symbol": symbol,
                    "side": "sell",
                    "qty": qty,
                    "price": price,
                    "commission": commission,
                    "portfolio_value": self.portfolio.get_value()
                })
                logger.debug(f"Sell {qty} shares at {price} at {self.current_time}")
        except Exception as e:
            logger.error(f"Error executing trades: {e}")

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        try:
            # Get portfolio value history
            equity_curve = pd.Series(
                [trade["portfolio_value"] for trade in self.trades],
                index=[trade["timestamp"] for trade in self.trades]
            )
            
            # Calculate returns
            returns = equity_curve.pct_change().dropna()
            
            # Calculate metrics
            total_return = (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(equity_curve)
            
            return {
                "initial_capital": self.initial_capital,
                "final_capital": float(equity_curve.iloc[-1]),
                "total_return": float(total_return),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "total_trades": len(self.trades),
                "equity_curve": equity_curve.to_dict(),
                "trades": self.trades
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio.
        
        Args:
            returns: Series of returns
            
        Returns:
            Sharpe ratio
        """
        try:
            if returns.empty:
                return 0.0
            
            risk_free_rate = 0.02  # Assume 2% annual risk-free rate
            excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
            
            if excess_returns.std() == 0:
                return 0.0
            
            sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            return float(sharpe)
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Maximum drawdown as a percentage
        """
        try:
            if equity_curve.empty:
                return 0.0
            
            rolling_max = equity_curve.expanding().max()
            drawdowns = equity_curve / rolling_max - 1
            max_drawdown = drawdowns.min()
            return float(max_drawdown)
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
