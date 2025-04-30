"""Position module for managing trading positions."""

from datetime import datetime
from typing import Any, Dict


class Position:
    """Class representing a trading position."""

    def __init__(
        self, symbol: str, size: float, entry_price: float, entry_time: datetime
    ) -> None:
        """Initialize a trading position.

        Args:
            symbol: Trading symbol
            size: Position size
            entry_price: Entry price
            entry_time: Entry time
        """
        self.symbol = symbol
        self.size = size
        self.entry_price = entry_price
        self.entry_time = entry_time

    def __str__(self) -> str:
        """Return string representation of position."""
        return (
            f"Position({self.symbol}, size={self.size}, entry_price={self.entry_price})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary.

        Returns:
            Dictionary representation of position
        """
        return {
            "symbol": self.symbol,
            "size": self.size,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
        }
