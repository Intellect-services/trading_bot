import time
from datetime import datetime, time as dt_time
import pytz
from alpaca.trading.client import TradingClient
from data_handler import DataHandler
from logger import BotLogger
from config import *

class TradingBot:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        self.data_handler = DataHandler()
        self.logger = BotLogger()
        self.positions = {}
        self.last_price = None
        self.start_time = datetime.now()

    def is_market_open(self):
        """Check if the market is currently open"""
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        current_time = now.time()
        market_open = dt_time.fromisoformat(MARKET_OPEN)
        market_close = dt_time.fromisoformat(MARKET_CLOSE)
        
        is_open = (now.weekday() < 5 and 
                  market_open <= current_time <= market_close)
        
        if not is_open:
            self.logger.log_info("Market is currently closed")
        return is_open

    def get_account_info(self):
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

    def place_order(self, symbol, qty, side, order_type='market'):
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

    def monitor_positions(self):
        """Monitor current positions"""
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

    def print_status(self):
        """Print current bot status"""
        runtime = datetime.now() - self.start_time
        hours = runtime.seconds // 3600
        minutes = (runtime.seconds % 3600) // 60
        
        print("\n" + "="*50)
        print(f"Trading Bot Status - Running for {hours}h {minutes}m")
        print("="*50)
        
        account_info = self.get_account_info()
        if account_info:
            print(f"Account Equity: ${account_info['equity']:.2f}")
            print(f"Available Cash: ${account_info['cash']:.2f}")
            print(f"Buying Power: ${account_info['buying_power']:.2f}")
        
        if self.positions:
            print("\nCurrent Positions:")
            for symbol, pos in self.positions.items():
                print(f"{symbol}: {pos['quantity']} shares @ ${pos['current_price']:.2f}")
        else:
            print("\nNo active positions")
        
        latest_price = self.data_handler.get_latest_price()
        if latest_price:
            print(f"\nLatest {DEFAULT_SYMBOL} price: ${latest_price:.2f}")
            if self.last_price:
                change = ((latest_price - self.last_price) / self.last_price) * 100
                print(f"Price Change: {change:+.2f}%")
            self.last_price = latest_price

    def run(self):
        """Main trading loop"""
        self.logger.log_info("Starting trading bot...")
        print("Trading Bot Started - Press Ctrl+C to stop")
        
        while True:
            try:
                if self.is_market_open():
                    self.monitor_positions()
                    self.print_status()
                
                # Sleep for 60 seconds before next iteration
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.logger.log_info("Stopping trading bot...")
                print("\nTrading Bot Stopped")
                break
            except Exception as e:
                self.logger.log_error(f"Error in main loop: {e}")
                time.sleep(60)  # Sleep before retrying

if __name__ == "__main__":
    bot = TradingBot()
    bot.run() 