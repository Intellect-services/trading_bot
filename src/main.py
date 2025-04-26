import time
from datetime import datetime
from typing import Dict, Optional

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.alpaca_client import AlpacaClient

logger = setup_logger(__name__)


class TradingBot:
    """Main trading bot class."""

    def __init__(self):
        """Initialize trading bot components."""
        self.config = Config()
        self.client = AlpacaClient(
            api_key=self.config.ALPACA_API_KEY,
            secret_key=self.config.ALPACA_SECRET_KEY
        )

        # Set up components
        self.data_feed = DataFeed(self.config)
        self.strategy = Strategy(self.config)
        self.risk_manager = RiskManager(self.config)
        self.portfolio = Portfolio(self.config)

        # Track state
        self.start_time = datetime.now()
        self.last_price = None
        self.positions = {}

        logger.info("Trading bot initialized")

    def is_market_open(self) -> bool:
        """Check if market is currently open.

        Returns:
            True if market is open, False otherwise
        """
        now = datetime.now().time()
        return self.config.MARKET_OPEN <= now <= self.config.MARKET_CLOSE

    def get_account_info(self) -> Optional[Dict]:
        """Get current account information.

        Returns:
            Dictionary with account info if successful, None otherwise
        """
        try:
            account = self.client.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None

    def run(self):
        """Run the trading bot."""
        try:
            logger.info("Starting trading bot...")

            while True:
                if not self.is_market_open():
                    logger.info("Market closed. Waiting...")
                    time.sleep(60)
                    continue

                # Get latest data
                data = self.data_feed.get_latest_data(self.config.DEFAULT_SYMBOL)
                if not data:
                    logger.warning("No market data available")
                    time.sleep(60)
                    continue

                # Generate signals
                signals = self.strategy.generate_signals(data)

                # Apply risk management
                filtered_signals = self.risk_manager.apply_risk_rules(
                    signals, self.portfolio.positions
                )

                # Execute trades
                for signal in filtered_signals:
                    self._execute_trade(signal)

                # Update state
                self.portfolio.update()
                time.sleep(60)

        except Exception as e:
            logger.error(f"Error running trading bot: {str(e)}")
            raise

    def _execute_trade(self, signal: Dict) -> None:
        """Execute a trade based on signal.

        Args:
            signal: Trading signal dictionary
        """
        try:
            # Calculate position size
            size = self.portfolio.calculate_position_size(signal["price"])

            # Submit order
            self.client.submit_order(
                symbol=signal["symbol"],
                qty=size,
                side=signal["action"],
                type="market"
            )

            msg = (
                f"Executed {signal['action']} order: {size} shares "
                f"at {signal['price']}"
            )
            logger.info(msg)

        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            raise


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
