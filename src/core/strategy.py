"""Base strategy class for trading strategies."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self) -> None:
        """Initialize the strategy."""
        pass

    @abstractmethod
    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        """Calculate the position size based on the current price and risk amount.

        Args:
            price: Current price of the asset
            risk_amount: Amount of capital to risk on the trade

        Returns:
            Position size in units/shares
        """
        pass

    @abstractmethod
    def should_open_position(self, price: float) -> bool:
        """Check if a new position should be opened.

        Args:
            price: Current price of the asset

        Returns:
            True if a position should be opened, False otherwise
        """
        pass

    @abstractmethod
    def should_close_position(self, price: float) -> bool:
        """Check if an existing position should be closed.

        Args:
            price: Current price of the asset

        Returns:
            True if the position should be closed, False otherwise
        """
        pass

    @abstractmethod
    def get_stop_loss(self, price: float) -> Optional[float]:
        """Calculate the stop loss price for a position.

        Args:
            price: Current price of the asset

        Returns:
            Stop loss price or None if no stop loss
        """
        pass

    @abstractmethod
    def get_take_profit(self, price: float) -> Optional[float]:
        """Calculate the take profit price for a position.

        Args:
            price: Current price of the asset

        Returns:
            Take profit price or None if no take profit
        """
        pass

    @abstractmethod
    def generate_signals(self, bars: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate trading signals from price data.

        Args:
            bars: DataFrame containing OHLCV price data

        Returns:
            List of signal dictionaries containing at least:
            - side: "long" or "short"
            - price: Current price
            - timestamp: Signal timestamp
        """
        pass
