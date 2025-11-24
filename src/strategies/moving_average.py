"""Moving average crossover strategy implementation."""

import logging
from typing import Any

import pandas as pd

from src.core.strategy import Strategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovingAverageCrossover(Strategy):
    """Moving average crossover strategy."""

    def __init__(self, short_window: int = 20, long_window: int = 50) -> None:
        """Initialize the strategy.

        Args:
            short_window: Short moving average window
            long_window: Long moving average window
        """
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window

        # State variables
        self.short_ma: float | None = None
        self.long_ma: float | None = None
        self.current_price: float | None = None
        self.position_side: str | None = None

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        """Calculate the position size based on the current price and risk amount.

        Args:
            price: Current price of the asset
            risk_amount: Amount of capital to risk on the trade

        Returns:
            Position size in units/shares
        """
        stop_loss = self.get_stop_loss(price)
        if stop_loss is None:
            return 0.0

        risk_per_share = abs(price - stop_loss)
        if risk_per_share <= 0:
            return 0.0

        return risk_amount / risk_per_share

    def should_open_position(self, price: float) -> bool:  # noqa: ARG002
        """Check if a new position should be opened.

        Args:
            price: Current price of the asset

        Returns:
            True if a position should be opened, False otherwise
        """
        if self.short_ma is None or self.long_ma is None:
            return False

        # Long signal: short MA crosses above long MA
        if self.short_ma > self.long_ma and self.position_side != "long":
            self.position_side = "long"
            return True

        # Short signal: short MA crosses below long MA
        if self.short_ma < self.long_ma and self.position_side != "short":
            self.position_side = "short"
            return True

        return False

    def should_close_position(self, price: float) -> bool:  # noqa: ARG002
        """Check if an existing position should be closed.

        Args:
            price: Current price of the asset

        Returns:
            True if the position should be closed, False otherwise
        """
        if self.short_ma is None or self.long_ma is None or self.position_side is None:
            return False

        # Close long position: short MA crosses below long MA
        if self.position_side == "long" and self.short_ma < self.long_ma:
            self.position_side = None
            return True

        # Close short position: short MA crosses above long MA
        if self.position_side == "short" and self.short_ma > self.long_ma:
            self.position_side = None
            return True

        return False

    def get_stop_loss(self, price: float) -> float | None:
        """Calculate the stop loss price for a position.

        Args:
            price: Current price of the asset

        Returns:
            Stop loss price or None if no stop loss
        """
        if self.position_side is None:
            return None

        # Calculate stop loss based on ATR or fixed percentage
        stop_loss_pct = 0.02  # 2% stop loss

        if self.position_side == "long":
            return price * (1 - stop_loss_pct)
        return price * (1 + stop_loss_pct)

    def get_take_profit(self, price: float) -> float | None:
        """Calculate the take profit price for a position.

        Args:
            price: Current price of the asset

        Returns:
            Take profit price or None if no take profit
        """
        if self.position_side is None:
            return None

        # Calculate take profit based on risk/reward ratio
        take_profit_pct = 0.04  # 4% take profit

        if self.position_side == "long":
            return price * (1 + take_profit_pct)
        return price * (1 - take_profit_pct)

    def generate_signals(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate trading signals from price data.

        Args:
            bars: DataFrame containing OHLCV price data

        Returns:
            List of signal dictionaries containing at least:
            - side: "long" or "short"
            - price: Current price
            - timestamp: Signal timestamp
        """
        if len(bars) < self.long_window:
            return []

        # Calculate moving averages
        short_ma_series = bars["close"].rolling(window=self.short_window).mean()
        long_ma_series = bars["close"].rolling(window=self.long_window).mean()

        if short_ma_series.empty or long_ma_series.empty:
            return []

        self.short_ma = float(short_ma_series.iloc[-1])
        self.long_ma = float(long_ma_series.iloc[-1])
        self.current_price = float(bars["close"].iloc[-1])

        signals = []

        # Generate signal if moving averages cross
        if self.short_ma > self.long_ma and self.position_side != "long":
            signals.append(
                {
                    "side": "long",
                    "price": self.current_price,
                    "timestamp": bars.index[-1],
                    "short_ma": self.short_ma,
                    "long_ma": self.long_ma,
                }
            )
        elif self.short_ma < self.long_ma and self.position_side != "short":
            signals.append(
                {
                    "side": "short",
                    "price": self.current_price,
                    "timestamp": bars.index[-1],
                    "short_ma": self.short_ma,
                    "long_ma": self.long_ma,
                }
            )

        return signals
