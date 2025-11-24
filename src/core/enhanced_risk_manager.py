"""Enhanced Risk Manager with database integration and advanced risk controls."""

import logging
from typing import Any

from src.core.bot_persistence import TradingBotPersistence

logger = logging.getLogger(__name__)


class EnhancedRiskManager:
    """Enhanced risk management with dynamic controls and database integration."""

    def __init__(self, persistence: TradingBotPersistence, config: Any):
        """Initialize Enhanced RiskManager.

        Args:
            persistence: Database persistence helper
            config: Configuration object with risk parameters
        """
        self.persistence = persistence
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Risk limits from config
        self.max_position_size = getattr(config, "risk_max_position_size", 0.10)  # 10%
        self.max_portfolio_heat = 0.50  # 50% max portfolio risk
        self.max_correlation = 0.70  # Max correlation between positions
        self.stop_loss_pct = 0.02  # 2% stop loss per position
        self.daily_loss_limit = 0.05  # 5% daily loss limit
        self.max_drawdown = getattr(config, "risk_max_drawdown", 0.15)  # 15%

        self.logger.info("Enhanced RiskManager initialized")

    def calculate_position_size(
        self,
        symbol: str,
        signal_strength: float,
        current_price: float,
        portfolio_value: float,
        volatility: float | None = None,
    ) -> int:
        """Calculate optimal position size based on risk parameters.

        Args:
            symbol: Stock symbol
            signal_strength: Signal strength (0-100)
            current_price: Current stock price
            portfolio_value: Total portfolio value
            volatility: Optional volatility measure (default: use fixed sizing)

        Returns:
            Number of shares to trade
        """
        try:
            # Base position size (percentage of portfolio)
            base_size = portfolio_value * self.max_position_size

            # Adjust for signal strength (50-100% of base size)
            strength_factor = 0.5 + (signal_strength / 200.0)  # 0.5 to 1.0
            adjusted_size = base_size * strength_factor

            # Adjust for volatility if provided
            if volatility and volatility > 0:
                # Reduce size for high volatility
                volatility_factor = min(1.0, 0.02 / volatility)  # Target 2% volatility
                adjusted_size *= volatility_factor

            # Calculate shares
            shares = int(adjusted_size / current_price)

            # Ensure minimum of 1 share if we're trading
            if shares == 0 and signal_strength > 70:
                shares = 1

            self.logger.info(
                f"Position size for {symbol}: {shares} shares "
                f"(strength: {signal_strength}, price: ${current_price:.2f})"
            )

            return shares

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0

    def check_position_risk(
        self, symbol: str, quantity: int, price: float, portfolio_value: float
    ) -> tuple[bool, str]:
        """Check if position meets risk requirements.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            portfolio_value: Total portfolio value

        Returns:
            Tuple of (is_allowed, reason)
        """
        try:
            position_value = quantity * price
            position_pct = position_value / portfolio_value

            # Check max position size
            if position_pct > self.max_position_size:
                return (
                    False,
                    f"Position size {position_pct:.1%} exceeds limit {self.max_position_size:.1%}",
                )

            # Check portfolio heat
            current_heat = self.calculate_portfolio_heat()
            position_risk = position_pct * self.stop_loss_pct

            if current_heat + position_risk > self.max_portfolio_heat:
                return (
                    False,
                    f"Portfolio heat {current_heat + position_risk:.1%} exceeds limit {self.max_portfolio_heat:.1%}",
                )

            # Check correlation with existing positions
            correlation = self.check_correlation(symbol)
            if correlation > self.max_correlation:
                return (
                    False,
                    f"Correlation {correlation:.2f} exceeds limit {self.max_correlation:.2f}",
                )

            return True, "Risk checks passed"

        except Exception as e:
            self.logger.error(f"Error checking position risk: {e}")
            return False, f"Error: {e!s}"

    def calculate_portfolio_heat(self) -> float:
        """Calculate total portfolio risk (heat).

        Returns:
            Portfolio heat as percentage (0.0 to 1.0)
        """
        try:
            positions = self.persistence.get_open_positions()

            if not positions:
                return 0.0

            # Get portfolio value
            portfolio = self.persistence.portfolio
            if not portfolio or portfolio.current_value == 0:
                return 0.0

            total_risk = 0.0

            for position in positions:
                # Calculate position size as % of portfolio
                position_pct = float(position.market_value) / float(portfolio.current_value)

                # Position risk = position size * stop loss %
                position_risk = position_pct * self.stop_loss_pct
                total_risk += position_risk

            self.logger.debug(f"Portfolio heat: {total_risk:.2%}")
            return total_risk

        except Exception as e:
            self.logger.error(f"Error calculating portfolio heat: {e}")
            return 0.0

    def check_correlation(self, symbol: str) -> float:
        """Check correlation of symbol with existing positions.

        Args:
            symbol: Stock symbol to check

        Returns:
            Maximum correlation with existing positions (0.0 to 1.0)
        """
        try:
            positions = self.persistence.get_open_positions()

            if not positions:
                return 0.0

            # For now, return 0 (no correlation check)
            # In production, would fetch price history and calculate correlation
            # This requires historical price data storage

            # Placeholder: assume low correlation for different symbols
            existing_symbols = [p.symbol for p in positions]
            if symbol in existing_symbols:
                return 1.0  # Perfect correlation with itself

            # Simple heuristic: same sector = higher correlation
            # Would need sector data for real implementation
            return 0.3  # Assume moderate correlation

        except Exception as e:
            self.logger.error(f"Error checking correlation: {e}")
            return 0.0

    def check_stop_loss(self, position_id: int) -> tuple[bool, float]:
        """Check if position hit stop loss.

        Args:
            position_id: Position ID

        Returns:
            Tuple of (should_close, loss_pct)
        """
        try:
            from src.business.trading.repositories import PositionRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                position_repo = PositionRepository(session)
                position = position_repo.get_by_id(position_id)

                if not position:
                    return False, 0.0

                # Calculate loss percentage
                if position.unrealized_pl_percent:
                    loss_pct = float(position.unrealized_pl_percent) / 100.0

                    # Check if loss exceeds stop loss
                    if loss_pct < -self.stop_loss_pct:
                        self.logger.warning(
                            f"Stop loss triggered for {position.symbol}: {loss_pct:.2%}"
                        )
                        return True, loss_pct

                return False, 0.0

        except Exception as e:
            self.logger.error(f"Error checking stop loss: {e}")
            return False, 0.0

    def enforce_stop_losses(self, bot: Any) -> list[str]:
        """Check all positions and enforce stop losses.

        Args:
            bot: TradingBot instance for executing orders

        Returns:
            List of symbols that were closed
        """
        closed_symbols = []

        try:
            positions = self.persistence.get_open_positions()

            for position in positions:
                position_id = int(position.id)
                symbol = str(position.symbol)
                should_close, loss_pct = self.check_stop_loss(position_id)

                if should_close:
                    try:
                        # Execute sell order
                        self.logger.info(f"Enforcing stop loss for {symbol}")

                        # Use bot to execute sell
                        if hasattr(bot, "_execute_sell"):
                            bot._execute_sell(symbol)
                            closed_symbols.append(symbol)

                            if hasattr(bot, "add_status_message"):
                                bot.add_status_message(
                                    f"Stop loss executed: {symbol} ({loss_pct:.2%})",
                                    "warning",
                                )
                    except Exception as e:
                        self.logger.error(f"Error enforcing stop loss for {position.symbol}: {e}")

            return closed_symbols

        except Exception as e:
            self.logger.error(f"Error enforcing stop losses: {e}")
            return closed_symbols

    def check_daily_loss_limit(self) -> tuple[bool, float]:
        """Check if daily loss limit has been reached.

        Returns:
            Tuple of (limit_reached, daily_pnl_pct)
        """
        try:
            from src.business.trading.repositories import TradeRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                portfolio = self.persistence.portfolio
                if portfolio is None:
                    return False, 0.0
                trade_repo = TradeRepository(session)
                portfolio_id = int(portfolio.id)

                # Get today's trades
                today_trades = trade_repo.get_today_trades(portfolio_id)

                if not today_trades:
                    return False, 0.0

                # Calculate total P&L
                total_pnl = sum(float(t.realized_pl) for t in today_trades if t.realized_pl)

                # Calculate as percentage of portfolio
                portfolio_value = float(portfolio.current_value)
                daily_pnl_pct = total_pnl / portfolio_value if portfolio_value > 0 else 0.0

                # Check if limit reached
                if daily_pnl_pct < -self.daily_loss_limit:
                    self.logger.warning(f"Daily loss limit reached: {daily_pnl_pct:.2%}")
                    return True, daily_pnl_pct

                return False, daily_pnl_pct

        except Exception as e:
            self.logger.error(f"Error checking daily loss limit: {e}")
            return False, 0.0

    def get_risk_metrics(self) -> dict[str, Any]:
        """Get current risk metrics.

        Returns:
            Dictionary of risk metrics
        """
        try:
            positions = self.persistence.get_open_positions()
            portfolio = self.persistence.portfolio
            if portfolio is None:
                return {}

            # Calculate metrics
            portfolio_heat = self.calculate_portfolio_heat()
            daily_limit_reached, daily_pnl = self.check_daily_loss_limit()

            # Position count
            position_count = len(positions)

            # Total exposure
            total_exposure = sum(float(p.market_value) for p in positions)
            exposure_pct = (
                total_exposure / float(portfolio.current_value)
                if portfolio.current_value > 0
                else 0.0
            )

            return {
                "portfolio_heat": portfolio_heat,
                "daily_pnl_pct": daily_pnl,
                "daily_limit_reached": daily_limit_reached,
                "position_count": position_count,
                "total_exposure": total_exposure,
                "exposure_pct": exposure_pct,
                "max_position_size": self.max_position_size,
                "max_portfolio_heat": self.max_portfolio_heat,
                "stop_loss_pct": self.stop_loss_pct,
                "daily_loss_limit": self.daily_loss_limit,
            }

        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {}
