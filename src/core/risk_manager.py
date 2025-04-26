"""Risk management module for the trading bot."""
from typing import Dict, Any
import logging
import pandas as pd
from datetime import datetime

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import calculate_position_size, format_price

logger = setup_logger(__name__)


class RiskManager:
    """Risk management class for controlling trading risk."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize risk manager with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing risk parameters
        """
        self.config = config
        self.risk_config = config['risk']
        self.max_drawdown = config['risk']['RISK_MAX_DRAWDOWN']
        self.max_leverage = config['risk']['RISK_MAX_LEVERAGE']
        self.stop_loss = config['risk']['RISK_STOP_LOSS']
        self.take_profit = config['risk']['RISK_TAKE_PROFIT']
        self.risk_per_trade = config['risk']['RISK_PER_TRADE']
        self.max_position_size = config['risk']['MAX_POSITION_SIZE']
        self.initial_capital = config['risk']['INITIAL_CAPITAL']
        self.current_capital = self.initial_capital
        self.positions: Dict[str, Dict] = {}
        logger.info("Initialized risk manager")

    def initialize(self) -> None:
        """Initialize or reset the risk manager state."""
        self.current_capital = self.initial_capital
        self.positions.clear()
        logger.info("Risk Manager state reset")

    def apply_risk_management(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Apply risk management rules to trading signals.

        Args:
            signals (pd.DataFrame): DataFrame containing trading signals

        Returns:
            pd.DataFrame: DataFrame with risk-managed signals
        """
        # Apply position sizing
        signals['position_size'] = signals.apply(
            lambda row: calculate_position_size(
                portfolio_value=self.risk_config['initial_capital'],
                risk_per_trade=self.risk_config['risk_per_trade'],
                entry_price=row['price'],
                stop_loss=row['price'] * (1 - self.risk_config['stop_loss_percent']),
                leverage=1.0
            ),
            axis=1
        )

        # Apply stop loss
        signals['stop_loss'] = signals.apply(
            lambda row: row['price'] * (1 - self.risk_config['stop_loss_percent']),
            axis=1
        )

        # Apply take profit
        signals['take_profit'] = signals.apply(
            lambda row: row['price'] * (1 + self.risk_config['take_profit_percent']),
            axis=1
        )

        return signals

    def update_capital(self, pnl: float) -> None:
        """Update current capital based on realized PnL.

        Args:
            pnl (float): Realized profit/loss amount.
        """
        self.current_capital += pnl
        logger.info("Capital updated: %s", format_price(self.current_capital))

    def update_position(self, symbol: str, size: float, price: float) -> None:
        """Update position information.

        Args:
            symbol (str): Trading symbol.
            size (float): Position size (negative for short positions).
            price (float): Entry price.
        """
        if size == 0:
            if symbol in self.positions:
                del self.positions[symbol]
        else:
            self.positions[symbol] = {'size': size, 'price': price}
        logger.info("Position updated for %s: size=%s, price=%s",
                   symbol, size, format_price(price))

    def calculate_position_size(self, price: float, risk_per_trade: float) -> float:
        """Calculate position size based on risk parameters.

        Args:
            price: Current price of the asset
            risk_per_trade: Maximum risk per trade as a percentage of portfolio

        Returns:
            Position size in units of the asset
        """
        portfolio_value = float(self.config['risk']['INITIAL_CAPITAL'])
        return calculate_position_size(
            portfolio_value=portfolio_value,
            risk_per_trade=risk_per_trade,
            entry_price=price,
            stop_loss=price * (1 - self.stop_loss),
            leverage=1.0
        )

    def check_stop_loss(self, current_price: float, entry_price: float) -> bool:
        """Check if stop loss has been hit.

        Args:
            current_price: Current price of the asset
            entry_price: Entry price of the position

        Returns:
            True if stop loss has been hit, False otherwise
        """
        return current_price <= entry_price * (1 - self.stop_loss)

    def check_take_profit(self, current_price: float, entry_price: float) -> bool:
        """Check if take profit has been hit.

        Args:
            current_price: Current price of the asset
            entry_price: Entry price of the position

        Returns:
            True if take profit has been hit, False otherwise
        """
        return current_price >= entry_price * (1 + self.take_profit)

    def check_max_drawdown(self, portfolio_value: float, peak_value: float) -> bool:
        """Check if maximum drawdown has been exceeded.

        Args:
            portfolio_value: Current portfolio value
            peak_value: Peak portfolio value

        Returns:
            True if maximum drawdown has been exceeded, False otherwise
        """
        drawdown = (peak_value - portfolio_value) / peak_value
        return drawdown > self.max_drawdown

    def check_leverage(self, position_value: float, portfolio_value: float) -> bool:
        """Check if leverage exceeds maximum allowed.

        Args:
            position_value: Value of the position
            portfolio_value: Current portfolio value

        Returns:
            True if leverage is within limits, False otherwise
        """
        leverage = position_value / portfolio_value
        return leverage <= self.max_leverage 