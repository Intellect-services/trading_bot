import time
from datetime import datetime, time as dt_time
import pytz
import random
from typing import Dict, Any, Optional

class MockTradingBot:
    def __init__(self):
        self.positions = {}
        self.start_time = datetime.now()
        self.last_price = 100.0  # Starting price
        self.mock_symbol = "AAPL"
        
    def is_market_open(self) -> bool:
        """Mock market hours check"""
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        current_time = now.time()
        market_open = dt_time.fromisoformat('09:30')
        market_close = dt_time.fromisoformat('16:00')
        
        is_open = (now.weekday() < 5 and 
                  market_open <= current_time <= market_close)
        return is_open
    
    def get_account_info(self) -> Dict[str, float]:
        """Mock account information"""
        return {
            'equity': 100000.0 + random.uniform(-1000, 1000),
            'cash': 50000.0 + random.uniform(-500, 500),
            'buying_power': 200000.0 + random.uniform(-2000, 2000)
        }
    
    def get_positions(self) -> Dict[str, Dict[str, float]]:
        """Mock positions"""
        if random.random() < 0.3:  # 30% chance to have a position
            self.positions = {
                self.mock_symbol: {
                    'quantity': random.randint(1, 100),
                    'current_price': self.last_price,
                    'market_value': self.last_price * random.randint(1, 100)
                }
            }
        return self.positions
    
    def get_latest_price(self) -> float:
        """Mock price updates"""
        # Simulate price movement
        change = random.uniform(-2.0, 2.0)
        self.last_price = max(1.0, self.last_price + change)
        return self.last_price
    
    def get_price_change(self) -> float:
        """Mock price change percentage"""
        return random.uniform(-5.0, 5.0)
    
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