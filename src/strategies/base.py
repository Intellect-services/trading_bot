"""Base strategy module."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Strategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self):
        """Initialize strategy."""
        self.name = self.__class__.__name__
        logger.info(f"Initializing {self.name} strategy")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Generate trading signals from market data.
        
        Args:
            data: Market data as a DataFrame
            
        Returns:
            DataFrame containing trading signals or None if no signals
        """
        pass

    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators.
        
        Args:
            data: Market data as a DataFrame
            
        Returns:
            DataFrame with added indicator columns
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data format.
        
        Args:
            data: Market data as a DataFrame
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            required_columns = ["open", "high", "low", "close", "volume"]
            if not all(col in data.columns for col in required_columns):
                logger.error(f"Missing required columns: {required_columns}")
                return False
            
            if data.empty:
                logger.error("Empty DataFrame provided")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return False

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