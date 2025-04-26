"""Trading bot core module."""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import logging
import pandas as pd
from alpaca.trading.models import TradeAccount, Position, Order
from alpaca.data.models import BarSet
from alpaca.trading.enums import OrderSide, TimeInForce

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.alpaca_client import AlpacaClient
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio

logger = setup_logger(__name__)

class TradingBot:
    """Main trading bot class."""

    def __init__(
        self,
        config: Config,
        strategy: Strategy,
        risk_manager: RiskManager,
        data_feed: Optional[DataFeed] = None,
        portfolio: Optional[Portfolio] = None
    ) -> None:
        """Initialize the trading bot.

        Args:
            config: Configuration object
            strategy: Trading strategy instance
            risk_manager: Risk management instance
            data_feed: Optional data feed instance
            portfolio: Optional portfolio instance
        """
        self.config = config
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.client = AlpacaClient(config)
        self.data_feed = data_feed or DataFeed(config, self.client)
        self.portfolio = portfolio or Portfolio(initial_capital=100000.0)  # Default initial capital
        logger.info("Trading bot initialized")

    def get_account_info(self) -> Dict[str, float]:
        """Get current account information.

        Returns:
            Dictionary containing account metrics
        """
        try:
            account = self.client.get_account()
            if isinstance(account, TradeAccount):
                return {
                    "equity": float(account.equity) if account.equity else 0.0,
                    "cash": float(account.cash) if account.cash else 0.0,
                    "buying_power": float(account.buying_power) if account.buying_power else 0.0
                }
            return {"equity": 0.0, "cash": 0.0, "buying_power": 0.0}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"equity": 0.0, "cash": 0.0, "buying_power": 0.0}

    def execute_trade(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: str = "market",
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> Optional[Dict[str, Any]]:
        """Execute a trading order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: Order side (buy/sell)
            type: Order type
            time_in_force: Time in force for the order

        Returns:
            Dictionary containing order information
        """
        try:
            order = self.client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force
            )
            if isinstance(order, dict):
                return order
            return None
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position information for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary containing position information
        """
        try:
            positions = self.client.get_positions()
            for pos in positions:
                if isinstance(pos, Position) and pos.symbol == symbol:
                    return {
                        "symbol": pos.symbol,
                        "qty": float(pos.qty),
                        "current_price": float(pos.current_price) if pos.current_price else 0.0,
                        "market_value": float(pos.market_value) if pos.market_value else 0.0
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return None

    def run(self) -> None:
        """Run the trading bot's main loop."""
        try:
            while True:
                # Get account information
                account_info = self.get_account_info()
                logger.info(f"Account info: {account_info}")

                # Get market data
                symbol = getattr(self.config, 'SYMBOL', 'SPY')
                data = self.data_feed.get_latest_data(symbol)
                if data is None or data.empty:
                    logger.warning("No data available")
                    continue

                # Generate trading signals
                signals = self.strategy.generate_signals(data)
                if signals is None or signals.empty:
                    logger.info("No signals generated")
                    continue

                # Apply risk management
                signals = self.risk_manager.apply_risk_management(signals)
                if signals is None or signals.empty:
                    logger.info("No valid signals after risk management")
                    continue

                # Execute trades
                for _, signal in signals.iterrows():
                    if signal['action'] == 'buy':
                        self.execute_trade(
                            symbol=signal['symbol'],
                            qty=signal['size'],
                            side=OrderSide.BUY
                        )
                    elif signal['action'] == 'sell':
                        self.execute_trade(
                            symbol=signal['symbol'],
                            qty=signal['size'],
                            side=OrderSide.SELL
                        )

                # Update portfolio with current prices
                prices = {symbol: data['close'].iloc[-1]}
                self.portfolio.update_prices(prices)

        except Exception as e:
            logger.error(f"Error in trading bot main loop: {e}")
            raise 