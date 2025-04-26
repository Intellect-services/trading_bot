"""Trading bot implementation."""
import time
from datetime import datetime, time as dt_time
import pytz
from typing import Dict, Any, Optional
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd

from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.alpaca_client import AlpacaClient

logger = setup_logger(__name__)


class TradingBot:
    """Trading bot that executes strategies and manages trades."""

    def __init__(self, config: Config):
        """Initialize the trading bot with configuration.

        Args:
            config (Config): Configuration object containing bot parameters
        """
        self.config = config
        self.strategy = Strategy(config.to_dict())
        self.risk_manager = RiskManager(config.to_dict())
        self.positions: Dict[str, Dict] = {}
        self.logger = logger
        self.alpaca_client = AlpacaClient()
        self.last_update: Optional[datetime] = None
        self.start_time: datetime = datetime.now()
        self.last_price: Optional[float] = None

        self.trading_client = TradingClient(
            api_key=self.config.ALPACA_API_KEY,
            secret_key=self.config.ALPACA_SECRET_KEY,
            paper=True
        )

        self.data_client = StockHistoricalDataClient(
            api_key=self.config.ALPACA_API_KEY,
            secret_key=self.config.ALPACA_SECRET_KEY
        )

        logger.info("Initialized trading bot")

    def is_market_open(self) -> bool:
        """Check if the market is currently open.

        Returns:
            bool: True if market is open, False otherwise
        """
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        current_time = now.time()
        market_open = dt_time.fromisoformat(self.config.MARKET_OPEN)
        market_close = dt_time.fromisoformat(self.config.MARKET_CLOSE)

        is_open = (now.weekday() < 5 and
                  market_open <= current_time <= market_close)

        if not is_open:
            self.logger.info("Market is currently closed")
        return is_open

    def get_account_info(self) -> Optional[Dict[str, float]]:
        """Get account information.

        Returns:
            Optional[Dict[str, float]]: Account information or None if error occurs
        """
        try:
            account = self.trading_client.get_account()
            info = {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power)
            }
            self.logger.info(
                "Account update - Equity: $%.2f, Cash: $%.2f, Buying Power: $%.2f",
                info['equity'], info['cash'], info['buying_power']
            )
            return info
        except Exception as e:
            self.logger.error("Error getting account info: %s", str(e))
            return None

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = 'market'
    ) -> Optional[Dict[str, Any]]:
        """Place a trading order.

        Args:
            symbol: Trading symbol
            qty: Order quantity
            side: Order side ('buy' or 'sell')
            order_type: Order type (default: 'market')

        Returns:
            Optional[Dict[str, Any]]: Order information or None if error occurs
        """
        try:
            order = self.trading_client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force='day'
            )
            self.logger.info(
                "Order placed - Symbol: %s, Side: %s, Qty: %.2f, Price: $%.2f, Status: %s",
                symbol, side, qty, float(order.filled_avg_price), order.status
            )
            return order
        except Exception as e:
            self.logger.error("Error placing order: %s", str(e))
            return None

    def update_positions(self) -> None:
        """Update current positions."""
        try:
            positions = self.trading_client.get_all_positions()
            for position in positions:
                symbol = position.symbol
                current_price = float(position.current_price)
                qty = float(position.qty)
                self.positions[symbol] = {
                    'quantity': qty,
                    'current_price': current_price,
                    'market_value': float(position.market_value)
                }
                self.logger.info(
                    "Position update - Symbol: %s, Qty: %.2f shares @ $%.2f",
                    symbol, qty, current_price
                )
        except Exception as e:
            self.logger.error("Error monitoring positions: %s", str(e))

    def get_market_data(self, symbol: str, timeframe: str = '1D', limit: int = 100) -> Optional[pd.DataFrame]:
        """Get market data for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe for the data (default: '1D')
            limit: Number of bars to retrieve (default: 100)

        Returns:
            Optional[pd.DataFrame]: Market data or None if error occurs
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                limit=limit
            )
            bars = self.data_client.get_stock_bars(request_params)
            return bars.df
        except Exception as e:
            self.logger.error("Error getting market data: %s", str(e))
            return None

    def execute_strategy(self) -> None:
        """Execute the trading strategy."""
        if not self.is_market_open():
            return

        try:
            # Get latest market data
            data = self.get_market_data(self.config.DEFAULT_SYMBOL)
            if data is None:
                return

            # Generate signals from strategy
            signals = self.strategy.generate_signals(data)

            # Apply risk management
            signals = self.risk_manager.apply_risk_management(signals)

            # Execute trades based on signals
            for _, signal in signals.iterrows():
                if signal['signal'] != 0:  # Buy or sell signal
                    self.place_order(
                        symbol=self.config.DEFAULT_SYMBOL,
                        qty=signal['position_size'],
                        side='buy' if signal['signal'] > 0 else 'sell'
                    )

        except Exception as e:
            self.logger.error("Error executing strategy: %s", str(e))

    def run(self) -> None:
        """Main trading loop."""
        self.logger.info("Starting trading bot...")

        while True:
            try:
                if self.is_market_open():
                    self.update_positions()
                    self.execute_strategy()

                time.sleep(int(self.config.get('UPDATE_INTERVAL', 60)))

            except KeyboardInterrupt:
                self.logger.info("Stopping trading bot...")
                break
            except Exception as e:
                self.logger.error("Error in main loop: %s", str(e))
                time.sleep(int(self.config.get('ERROR_RETRY_INTERVAL', 60))) 