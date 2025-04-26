import secrets
import time
from datetime import datetime, time as dt_time
import pytz
import random
from typing import Dict, Any, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MockTradingBot:
    def __init__(self):
        self.positions = {}
        self.start_time = datetime.now()
        self.last_price = 100.0  # Starting price
        self.mock_symbol = "AAPL"

    def is_market_open(self) -> bool:
        """Mock market hours check"""
        eastern = pytz.timezone("US/Eastern")
        now = datetime.now(eastern)
        current_time = now.time()
        market_open = dt_time.fromisoformat("09:30")
        market_close = dt_time.fromisoformat("16:00")

        is_open = now.weekday() < 5 and market_open <= current_time <= market_close
        return is_open

    def get_account_info(self) -> Dict[str, float]:
        """Mock account information"""
        # Use secrets for better security
        equity_change = secrets.SystemRandom().uniform(-1000, 1000)
        cash_change = secrets.SystemRandom().uniform(-500, 500)
        buying_power_change = secrets.SystemRandom().uniform(-2000, 2000)

        return {
            "equity": 100000.0 + equity_change,
            "cash": 50000.0 + cash_change,
            "buying_power": 200000.0 + buying_power_change,
        }

    def get_positions(self) -> Dict[str, Dict[str, float]]:
        """Mock positions"""
        # Use secrets for better security
        if secrets.SystemRandom().random() < 0.3:  # 30% chance to have a position
            self.positions = {
                self.mock_symbol: {
                    "quantity": secrets.SystemRandom().randint(1, 100),
                    "current_price": self.last_price,
                    "market_value": self.last_price
                    * secrets.SystemRandom().randint(1, 100),
                }
            }
        return self.positions

    def get_latest_price(self) -> float:
        """Mock price updates"""
        # Use secrets for better security
        change = secrets.SystemRandom().uniform(-2.0, 2.0)
        self.last_price = max(1.0, self.last_price + change)
        return self.last_price

    def get_price_change(self) -> float:
        """Mock price change percentage"""
        # Use secrets for better security
        return secrets.SystemRandom().uniform(-5.0, 5.0)

    def run(self):
        """Mock main loop"""
        print("Starting mock trading bot...")

        while True:
            try:
                if self.is_market_open():
                    # Update mock data
                    self.get_positions()
                    self.get_latest_price()

                time.sleep(5)  # Update every 5 seconds

            except KeyboardInterrupt:
                print("\nStopping mock trading bot...")
                break
            except Exception as e:
                print(f"Error in mock loop: {e}")
                time.sleep(5)
