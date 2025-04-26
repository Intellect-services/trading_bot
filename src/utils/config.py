import os
from typing import Dict, Any
from dotenv import load_dotenv

def get_config() -> Dict[str, Any]:
    """Get configuration settings"""
    load_dotenv()
    
    config = {
        # API Configuration
        'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
        'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
        
        # Trading Parameters
        'DEFAULT_SYMBOL': os.getenv('DEFAULT_SYMBOL', 'AAPL'),
        'DEFAULT_QUANTITY': float(os.getenv('DEFAULT_QUANTITY', '1')),
        'DEFAULT_TIMEFRAME': os.getenv('DEFAULT_TIMEFRAME', '1D'),
        
        # Risk Management
        'MAX_POSITION_SIZE': float(os.getenv('MAX_POSITION_SIZE', '1000')),
        'STOP_LOSS_PERCENTAGE': float(os.getenv('STOP_LOSS_PERCENTAGE', '0.02')),
        'TAKE_PROFIT_PERCENTAGE': float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.05')),
        
        # Trading Hours
        'MARKET_OPEN': os.getenv('MARKET_OPEN', '09:30'),
        'MARKET_CLOSE': os.getenv('MARKET_CLOSE', '16:00'),
        
        # Data Storage
        'DATA_DIR': os.getenv('DATA_DIR', 'data'),
        'HISTORICAL_DATA_FILE': os.path.join(
            os.getenv('DATA_DIR', 'data'),
            os.getenv('HISTORICAL_DATA_FILE', 'historical_data.csv')
        ),
        
        # System Configuration
        'UPDATE_INTERVAL': int(os.getenv('UPDATE_INTERVAL', '60')),
        'ERROR_RETRY_INTERVAL': int(os.getenv('ERROR_RETRY_INTERVAL', '60')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        
        # Backtesting Configuration
        'BACKTEST_START_DATE': os.getenv('BACKTEST_START_DATE', '2020-01-01'),
        'BACKTEST_END_DATE': os.getenv('BACKTEST_END_DATE', '2023-12-31'),
        'BACKTEST_INITIAL_CAPITAL': float(os.getenv('BACKTEST_INITIAL_CAPITAL', '100000')),
        'BACKTEST_COMMISSION': float(os.getenv('BACKTEST_COMMISSION', '0.001')),
    }
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration settings"""
    required_keys = [
        'ALPACA_API_KEY',
        'ALPACA_SECRET_KEY',
        'DEFAULT_SYMBOL',
        'MARKET_OPEN',
        'MARKET_CLOSE'
    ]
    
    for key in required_keys:
        if not config.get(key):
            raise ValueError(f"Missing required configuration: {key}")
    
    return True 