#!/usr/bin/env python3
"""Script to run the trading bot."""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.bot import TradingBot
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.utils.config import Config
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)


def main():
    """Main function to run the trading bot."""
    try:
        # Initialize configuration
        config = Config()

        # Initialize strategy
        strategy = Strategy(config)

        # Initialize risk manager
        risk_manager = RiskManager(config)

        # Initialize trading bot
        bot = TradingBot(config=config, strategy=strategy, risk_manager=risk_manager)

        logger.info("Starting trading bot...")
        bot.run()

    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Error running trading bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
