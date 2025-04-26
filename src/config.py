import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Trading Parameters
DEFAULT_SYMBOL = 'AAPL'  # Default stock symbol to trade
DEFAULT_QUANTITY = 1     # Default number of shares to trade
DEFAULT_TIMEFRAME = '1D' # Default timeframe for data (1D = 1 day)

# Risk Management
MAX_POSITION_SIZE = 1000  # Maximum position size in dollars
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.05  # 5% take profit

# Trading Hours (in Eastern Time)
MARKET_OPEN = '09:30'
MARKET_CLOSE = '16:00'

# Data Storage
DATA_DIR = 'data'
HISTORICAL_DATA_FILE = os.path.join(DATA_DIR, 'historical_data.csv') 