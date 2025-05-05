"""Base strategy module."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.config import Config

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    def __init__(self, config: Config) -> None:
        """Initialize the strategy.

        Args:
            config: Configuration object containing strategy parameters
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Generate trading signals based on the strategy logic.

        Args:
            data: DataFrame containing market data

        Returns:
            DataFrame with signals or None if signals cannot be generated
        """
        pass

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
    def get_required_data(self) -> List[str]:
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

    def get_status(self) -> Dict[str, Any]:
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
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, float]:
        """Get the strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """
        pass

    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Update strategy parameters.

        Args:
            params: Dictionary of parameters to update
        """
        pass

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
        pass

    @abstractmethod
    def should_buy(self, symbol: str) -> bool:
        """Check if we should buy the asset.

        Args:
            symbol: Asset symbol

        Returns:
            True if we should buy, False otherwise
        """
        pass

    @abstractmethod
    def should_sell(self, symbol: str) -> bool:
        """Check if we should sell the asset.

        Args:
            symbol: Asset symbol

        Returns:
            True if we should sell, False otherwise
        """
        pass

    def reset(self) -> None:
        """Reset the strategy state."""
        pass
