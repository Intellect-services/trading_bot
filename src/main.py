"""Main module for running the trading bot."""

from typing import Optional
import argparse
import logging

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.core.bot import TradingBot
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Trading Bot")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--symbols", type=str, nargs="+", help="Symbols to trade")
    parser.add_argument("--capital", type=float, help="Initial capital")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main() -> None:
    """Main function to run the trading bot."""
    try:
        # Parse arguments
        args = parse_args()
        
        # Set logging level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Load config
        config = Config(args.config if args.config else None)
        
        # Initialize components
        strategy = Strategy(config)
        risk_manager = RiskManager(config)
        data_feed = DataFeed(config)
        portfolio: Optional[Portfolio] = None
        
        if args.capital:
            portfolio = Portfolio(args.capital)
            
        # Initialize bot
        bot = TradingBot(
            config=config,
            strategy=strategy,
            risk_manager=risk_manager,
            data_feed=data_feed,
            portfolio=portfolio
        )
        
        # Add symbols
        if args.symbols:
            for symbol in args.symbols:
                bot.add_symbol(symbol)
        else:
            bot.add_symbol(config.DEFAULT_SYMBOL)
            
        # Start bot
        bot.start()
        
        # Run main loop
        while True:
            bot.run()
            
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        if 'bot' in locals():
            bot.stop()
    except Exception as e:
        logger.error("Error in main: %s", e)
        if 'bot' in locals():
            bot.stop()
        raise

if __name__ == "__main__":
    main()
