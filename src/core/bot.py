import time
from datetime import datetime, time as dt_time
import pytz
from typing import Dict, Any, Optional
from alpaca.trading.client import TradingClient
from src.core.strategy import Strategy
from ..utils.config import get_config
from ..utils.logger import BotLogger
import logging
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.alpaca_client import AlpacaClient
from src.core.risk_manager import RiskManager
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trade_api.stream import Stream
from src.utils.helpers import calculate_position_size, format_price

logger = setup_logger(__name__)

class TradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(__name__)
        self.alpaca_client = AlpacaClient()
        self.risk_manager = RiskManager()
        self.positions = {}
        self.last_update = None
        self.strategy = Strategy()
        self.trading_client = TradingClient(
            self.config['ALPACA_API_KEY'],
            self.config['ALPACA_SECRET_KEY'],
            paper=True
        )
        self.start_time = datetime.now()
        self.last_price: Optional[float] = None
        
    def is_market_open(self) -> bool:
        """Check if the market is currently open"""
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        current_time = now.time()
        market_open = dt_time.fromisoformat(self.config['MARKET_OPEN'])
        market_close = dt_time.fromisoformat(self.config['MARKET_CLOSE'])
        
        is_open = (now.weekday() < 5 and 
                  market_open <= current_time <= market_close)
        
        if not is_open:
            self.logger.log_info("Market is currently closed")
        return is_open
    
    def get_account_info(self) -> Optional[Dict[str, float]]:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            info = {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power)
            }
            self.logger.log_account_update(info['equity'], info['cash'], info['buying_power'])
            return info
        except Exception as e:
            self.logger.log_error(f"Error getting account info: {e}")
            return None
    
    def place_order(self, symbol: str, qty: float, side: str, order_type: str = 'market') -> Optional[Dict[str, Any]]:
        """Place a trading order"""
        try:
            order = self.trading_client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force='day'
            )
            self.logger.log_trade(symbol, side, qty, float(order.filled_avg_price), order.status)
            return order
        except Exception as e:
            self.logger.log_error(f"Error placing order: {e}")
            return None
    
    def update_positions(self):
        """Update current positions"""
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
                self.logger.log_info(f"Position: {symbol} - {qty} shares @ ${current_price:.2f}")
        except Exception as e:
            self.logger.log_error(f"Error monitoring positions: {e}")
    
    def execute_strategy(self):
        """Execute the trading strategy"""
        if not self.is_market_open():
            return
        
        try:
            # Get latest market data
            # This would be implemented based on your data source
            # For example, using Alpaca's market data API
            
            # Generate signals from strategy
            # signals = self.strategy.generate_signals(data)
            
            # Execute trades based on signals
            # This would be implemented based on your strategy's signals
            
            pass
        except Exception as e:
            self.logger.log_error(f"Error executing strategy: {e}")
    
    def run(self):
        """Main trading loop"""
        self.logger.log_info("Starting trading bot...")
        
        while True:
            try:
                if self.is_market_open():
                    self.update_positions()
                    self.execute_strategy()
                
                time.sleep(self.config.get('UPDATE_INTERVAL', 60))
                
            except KeyboardInterrupt:
                self.logger.log_info("Stopping trading bot...")
                break
            except Exception as e:
                self.logger.log_error(f"Error in main loop: {e}")
                time.sleep(self.config.get('ERROR_RETRY_INTERVAL', 60)) 