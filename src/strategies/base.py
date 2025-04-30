"""Base strategy module."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, config: Config):
        """Initialize the strategy.

        Args:
            config: Configuration object
        """
        self.config = config
        self.symbols = config.STRATEGY_PARAMS["symbols"]
        self.timeframe = config.STRATEGY_PARAMS["timeframe"]
        self.parameters = config.STRATEGY_PARAMS["parameters"]
        self.name = self.__class__.__name__
        logger.info(f"Strategy initialized: {self.name}")

    @abstractmethod
    def generate_signals(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate trading signals based on the given data.

        Args:
            data: Dictionary containing market data

        Returns:
            Dictionary mapping symbols to signals ('buy', 'sell', or 'hold')
        """
        pass

    @abstractmethod
    def calculate_position_size(self, symbol: str, price: float) -> float:
        """Calculate the position size for a given symbol and price.

        Args:
            symbol: Trading symbol
            price: Current price

        Returns:
            Number of shares to trade
        """
        pass

    def get_required_data(self) -> List[str]:
        """Get the list of required data fields for the strategy.

        Returns:
            List of required data field names
        """
        return ["open", "high", "low", "close", "volume"]

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the input data.

        Args:
            data: Dictionary containing market data

        Returns:
            True if data is valid, False otherwise
        """
        required_fields = self.get_required_data()
        return all(field in data for field in required_fields)

    def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess the input data.

        Args:
            data: Dictionary containing market data

        Returns:
            Preprocessed data dictionary
        """
        return data

    def postprocess_signals(self, signals: Dict[str, str]) -> Dict[str, str]:
        """Postprocess the generated signals.

        Args:
            signals: Dictionary mapping symbols to signals

        Returns:
            Postprocessed signals dictionary
        """
        return signals

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy.

        Returns:
            Dictionary containing strategy status information
        """
        return {
            "name": self.name,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "parameters": self.parameters,
            "timestamp": datetime.now().isoformat(),
        }

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators.

        Args:
            data: Market data as a DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        pass

    def get_parameters(self) -> Dict[str, float]:
        """Get strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """
        return {
            name: value
            for name, value in vars(self).items()
            if isinstance(value, (int, float)) and not name.startswith("_")
        }
