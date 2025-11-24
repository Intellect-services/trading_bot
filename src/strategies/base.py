"""Base strategy module.

This module provides BaseStrategy which extends the core Strategy ABC
with additional functionality for more complex strategies.
"""

import logging
from abc import abstractmethod
from typing import Any

import pandas as pd

from src.core.strategy import Strategy
from src.utils.config import Config

logger = logging.getLogger(__name__)


class BaseStrategy(Strategy):
    """Abstract base class for all trading strategies.

    Extends the core Strategy ABC with additional methods for data validation,
    preprocessing, and more complex signal generation.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the strategy.

        Args:
            config: Configuration object containing strategy parameters
        """
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate trading signals based on the strategy logic.

        Args:
            data: DataFrame containing market data

        Returns:
            A list of signal dictionaries describing the intended trades
        """

    def calculate_position_size(self, signal: float, available_capital: float) -> float:
        """Calculate the position size for a trade.

        Args:
            signal: The trading signal (-1, 0, or 1)
            available_capital: Amount of capital available for the trade

        Returns:
            Position size as a float
        """
        return signal * available_capital

    @abstractmethod
    def get_required_data(self) -> list[str]:
        """Get the list of required data fields for the strategy.

        Returns:
            List of required column names
        """
        return ["timestamp", "open", "high", "low", "close", "volume"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate that the input data contains all required fields.

        Args:
            data: DataFrame to validate

        Returns:
            True if data is valid, False otherwise
        """
        required_columns = self.get_required_data()
        return all(col in data.columns for col in required_columns)

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the input data before generating signals.

        Args:
            data: Raw input data

        Returns:
            Preprocessed DataFrame
        """
        if not self.validate_data(data):
            return pd.DataFrame()
        return data.copy()

    def postprocess_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Post-process the generated signals.

        Args:
            signals: DataFrame containing raw signals

        Returns:
            DataFrame with processed signals
        """
        return signals

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the strategy.

        Returns:
            Dictionary containing strategy status information
        """
        return {"name": self.__class__.__name__, "parameters": self.get_parameters()}

    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators used by the strategy.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with calculated indicators
        """

    @abstractmethod
    def get_parameters(self) -> dict[str, float]:
        """Get the strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """

    @abstractmethod
    def set_parameters(self, params: dict[str, Any]) -> None:
        """Update strategy parameters.

        Args:
            params: Dictionary of parameters to update
        """

    @abstractmethod
    def update_state(self, data: pd.DataFrame) -> None:
        """Update strategy state with new market data.

        Args:
            data: DataFrame containing market data with columns:
                - symbol: Asset symbol
                - timestamp: Data timestamp
                - open: Opening price
                - high: High price
                - low: Low price
                - close: Closing price
                - volume: Trading volume
        """

    @abstractmethod
    def should_buy(self, symbol: str) -> bool:
        """Check if we should buy the asset.

        Args:
            symbol: Asset symbol

        Returns:
            True if we should buy, False otherwise
        """

    @abstractmethod
    def should_sell(self, symbol: str) -> bool:
        """Check if we should sell the asset.

        Args:
            symbol: Asset symbol

        Returns:
            True if we should sell, False otherwise
        """

    def reset(self) -> None:
        """Reset the strategy state."""
