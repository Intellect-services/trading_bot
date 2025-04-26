"""Helper functions for trading calculations and formatting."""

from typing import Union, Optional
from decimal import Decimal


def calculate_position_size(
    portfolio_value: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss: Optional[float] = None,
    leverage: float = 1.0,
) -> float:
    """
    Calculate the position size based on risk parameters.

    Args:
        portfolio_value: Current portfolio value
        risk_per_trade: Maximum risk per trade as a percentage (e.g., 0.02 for 2%)
        entry_price: Entry price of the trade
        stop_loss: Stop loss price (optional)
        leverage: Leverage multiplier (default: 1.0)

    Returns:
        float: Position size in base currency
    """
    if stop_loss is not None and stop_loss > 0:
        # Calculate position size based on stop loss
        risk_amount = portfolio_value * risk_per_trade
        price_difference = abs(entry_price - stop_loss)
        if price_difference > 0:
            position_size = (risk_amount / price_difference) * leverage
        else:
            position_size = 0
    else:
        # Use a default position size based on risk percentage
        position_size = (portfolio_value * risk_per_trade * leverage) / entry_price

    return position_size


def format_price(
    price: Union[float, Decimal],
    decimals: int = 8,
    include_currency: bool = False,
    currency_symbol: str = "$",
) -> str:
    """
    Format a price value with specified decimal places and optional currency symbol.

    Args:
        price: Price value to format
        decimals: Number of decimal places (default: 8)
        include_currency: Whether to include currency symbol (default: False)
        currency_symbol: Currency symbol to use (default: "$")

    Returns:
        str: Formatted price string
    """
    formatted_price = f"{float(price):.{decimals}f}"

    # Remove trailing zeros after decimal point
    if "." in formatted_price:
        formatted_price = formatted_price.rstrip("0").rstrip(".")

    if include_currency:
        return f"{currency_symbol}{formatted_price}"

    return formatted_price
