"""Position Tracker for real-time position monitoring and reconciliation."""

import logging
import threading
import time
from decimal import Decimal
from typing import Any

from src.core.bot_persistence import TradingBotPersistence

logger = logging.getLogger(__name__)


class PositionTracker:
    """Tracks positions in real-time with Alpaca reconciliation."""

    def __init__(
        self, bot: Any, persistence: TradingBotPersistence, check_interval: int = 300
    ) -> None:
        """Initialize PositionTracker.

        Args:
            bot: Reference to TradingBot instance
            persistence: Database persistence helper
            check_interval: Seconds between position checks (default: 300 = 5 minutes)
        """
        self.bot = bot
        self.persistence = persistence
        self.check_interval = check_interval
        self.is_tracking = False
        self.tracker_thread: threading.Thread | None = None
        self.logger = logging.getLogger(__name__)

    def start_tracking(self) -> None:
        """Start background position tracking."""
        if self.is_tracking:
            self.logger.warning("Position tracking already running")
            return

        self.is_tracking = True
        self.tracker_thread = threading.Thread(
            target=self._tracking_loop, daemon=True, name="PositionTracker"
        )
        self.tracker_thread.start()
        self.logger.info("Position tracking started")

    def stop_tracking(self) -> None:
        """Stop background position tracking."""
        if not self.is_tracking:
            return

        self.is_tracking = False
        if self.tracker_thread:
            self.tracker_thread.join(timeout=10)
        self.logger.info("Position tracking stopped")

    def _tracking_loop(self) -> None:
        """Main tracking loop running in background thread."""
        self.logger.info("Position tracking loop started")

        while self.is_tracking:
            try:
                # Sync positions with Alpaca
                self.sync_positions()

                # Update P&L for all positions
                self.update_pnl()

                # Check for reconciliation issues
                discrepancies = self.reconcile_positions()
                if discrepancies:
                    self.logger.warning(f"Found {len(discrepancies)} position discrepancies")

                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in tracking loop: {e}")
                time.sleep(self.check_interval)

    def sync_positions(self) -> None:
        """Sync positions with Alpaca."""
        try:
            # Get positions from Alpaca
            alpaca_positions = self.bot.alpaca_service.get_positions()

            if not alpaca_positions:
                self.logger.debug("No positions from Alpaca")
                return

            self.logger.debug(f"Syncing {len(alpaca_positions)} positions")

            # Update each position in database
            for alpaca_pos in alpaca_positions:
                try:
                    self.persistence.update_position(
                        symbol=alpaca_pos["symbol"],
                        quantity=float(alpaca_pos["qty"]),
                        avg_price=float(alpaca_pos["avg_entry_price"]),
                        current_price=float(alpaca_pos["current_price"]),
                        side=alpaca_pos.get("side", "long"),
                    )
                except Exception as e:
                    self.logger.error(f"Error syncing position {alpaca_pos['symbol']}: {e}")

            # Check for positions in DB that are not in Alpaca (should be closed)
            db_positions = self.persistence.get_open_positions()
            alpaca_symbols = {p["symbol"] for p in alpaca_positions}

            for db_pos in db_positions:
                if db_pos.symbol not in alpaca_symbols:
                    # Position closed in Alpaca but still in DB
                    self.logger.info(f"Closing position {db_pos.symbol} (not in Alpaca)")
                    self.persistence.close_position(str(db_pos.symbol))

        except Exception as e:
            self.logger.error(f"Error syncing positions: {e}")

    def update_pnl(self) -> None:
        """Update P&L for all positions."""
        try:
            db_positions = self.persistence.get_open_positions()

            for position in db_positions:
                try:
                    # Get current price from Alpaca
                    current_price = self.bot.alpaca_service.get_latest_price(position.symbol)

                    if current_price:
                        # Update position with current price (triggers P&L recalculation)
                        from src.business.trading.repositories import PositionRepository
                        from src.infrastructure import db_config

                        with db_config.get_session() as session:
                            position_repo = PositionRepository(session)
                            position_id = int(position.id)
                            position_repo.update_price(position_id, Decimal(str(current_price)))

                except Exception as e:
                    self.logger.error(f"Error updating P&L for {position.symbol}: {e}")

        except Exception as e:
            self.logger.error(f"Error updating P&L: {e}")

    def reconcile_positions(self) -> list[dict[str, Any]]:
        """Reconcile positions between database and Alpaca.

        Returns:
            List of discrepancies found
        """
        discrepancies = []

        try:
            # Get positions from both sources
            db_positions = self.persistence.get_open_positions()
            alpaca_positions = self.bot.alpaca_service.get_positions()

            # Create lookup dictionaries
            db_pos_dict = {p.symbol: p for p in db_positions}
            alpaca_pos_dict = {p["symbol"]: p for p in alpaca_positions}

            # Check for quantity mismatches
            for symbol in db_pos_dict:
                if symbol in alpaca_pos_dict:
                    db_qty = float(db_pos_dict[symbol].quantity)
                    alpaca_qty = float(alpaca_pos_dict[symbol]["qty"])

                    if abs(db_qty - alpaca_qty) > 0.01:  # Allow small floating point differences
                        discrepancy = {
                            "symbol": symbol,
                            "type": "quantity_mismatch",
                            "db_quantity": db_qty,
                            "alpaca_quantity": alpaca_qty,
                            "difference": alpaca_qty - db_qty,
                        }
                        discrepancies.append(discrepancy)
                        self.logger.warning(
                            f"Quantity mismatch for {symbol}: DB={db_qty}, Alpaca={alpaca_qty}"
                        )

            # Check for positions in DB but not in Alpaca
            for symbol in db_pos_dict:
                if symbol not in alpaca_pos_dict:
                    discrepancy = {
                        "symbol": symbol,
                        "type": "missing_in_alpaca",
                        "db_quantity": float(db_pos_dict[symbol].quantity),
                    }
                    discrepancies.append(discrepancy)
                    self.logger.warning(f"Position {symbol} in DB but not in Alpaca")

            # Check for positions in Alpaca but not in DB
            for symbol in alpaca_pos_dict:
                if symbol not in db_pos_dict:
                    discrepancy = {
                        "symbol": symbol,
                        "type": "missing_in_db",
                        "alpaca_quantity": float(alpaca_pos_dict[symbol]["qty"]),
                    }
                    discrepancies.append(discrepancy)
                    self.logger.warning(f"Position {symbol} in Alpaca but not in DB")

            return discrepancies

        except Exception as e:
            self.logger.error(f"Error reconciling positions: {e}")
            return discrepancies

    def alert_discrepancy(self, discrepancy: dict[str, Any]) -> None:
        """Alert on position discrepancy.

        Args:
            discrepancy: Discrepancy details
        """
        try:
            message = f"Position discrepancy: {discrepancy['type']} for {discrepancy['symbol']}"

            # Add to bot status messages
            if hasattr(self.bot, "add_status_message"):
                self.bot.add_status_message(message, "warning")

            # Log the discrepancy
            self.logger.warning(f"Discrepancy: {discrepancy}")

            # In production, could send email/SMS alert

        except Exception as e:
            self.logger.error(f"Error alerting discrepancy: {e}")

    def get_position_summary(self) -> dict[str, Any]:
        """Get summary of current positions.

        Returns:
            Dictionary with position summary
        """
        try:
            db_positions = self.persistence.get_open_positions()

            total_value = sum(float(p.market_value) for p in db_positions if p.market_value)
            total_unrealized_pl = sum(
                float(p.unrealized_pl) for p in db_positions if p.unrealized_pl
            )

            # Count long and short positions
            long_positions = [p for p in db_positions if p.side == "long"]
            short_positions = [p for p in db_positions if p.side == "short"]

            # Get portfolio value
            portfolio = self.persistence.portfolio
            portfolio_value = float(portfolio.current_value) if portfolio else 0

            return {
                "total_positions": len(db_positions),
                "long_positions": len(long_positions),
                "short_positions": len(short_positions),
                "total_market_value": total_value,
                "total_unrealized_pl": total_unrealized_pl,
                "portfolio_value": portfolio_value,
                "exposure_pct": (total_value / portfolio_value * 100) if portfolio_value > 0 else 0,
                "positions": [
                    {
                        "symbol": p.symbol,
                        "quantity": float(p.quantity),
                        "market_value": float(p.market_value) if p.market_value else 0,
                        "unrealized_pl": float(p.unrealized_pl) if p.unrealized_pl else 0,
                        "unrealized_pl_pct": float(p.unrealized_pl_percent)
                        if p.unrealized_pl_percent
                        else 0,
                    }
                    for p in db_positions
                ],
            }

        except Exception as e:
            self.logger.error(f"Error getting position summary: {e}")
            return {}
