"""Order Manager for automated order lifecycle tracking and management."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, cast

from src.business.trading.models import Order
from src.core.bot_persistence import TradingBotPersistence

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order lifecycle tracking and automated updates."""

    def __init__(
        self, bot: Any, persistence: TradingBotPersistence, check_interval: int = 5
    ) -> None:
        """Initialize OrderManager.

        Args:
            bot: Reference to TradingBot instance
            persistence: Database persistence helper
            check_interval: Seconds between order checks (default: 5)
        """
        self.bot = bot
        self.persistence = persistence
        self.check_interval = check_interval
        self.is_monitoring = False
        self.monitor_thread: threading.Thread | None = None
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self) -> None:
        """Start background order monitoring."""
        if self.is_monitoring:
            self.logger.warning("Order monitoring already running")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True, name="OrderMonitor"
        )
        self.monitor_thread.start()
        self.logger.info("Order monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background order monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        self.logger.info("Order monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        self.logger.info("Order monitoring loop started")

        while self.is_monitoring:
            try:
                self._check_pending_orders()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

    def _check_pending_orders(self) -> None:
        """Check status of all pending orders."""
        try:
            # Get pending orders from database
            pending_orders = self.persistence.get_pending_orders()

            if not pending_orders:
                return

            self.logger.debug(f"Checking {len(pending_orders)} pending orders")

            for db_order in pending_orders:
                try:
                    self._sync_order_status(db_order)
                except Exception as e:
                    self.logger.error(f"Error syncing order {db_order.id}: {e}")

        except Exception as e:
            self.logger.error(f"Error checking pending orders: {e}")

    def _sync_order_status(self, db_order: Order) -> None:
        """Sync order status with Alpaca.

        Args:
            db_order: Database order record
        """
        if not db_order.alpaca_order_id:
            self.logger.warning(f"Order {db_order.id} has no Alpaca ID")
            return

        try:
            alpaca_order_id = cast("str", db_order.alpaca_order_id)
            order_id = int(db_order.id)

            # Get current status from Alpaca
            alpaca_order = self.bot.alpaca_service.get_order(alpaca_order_id)

            if not alpaca_order:
                self.logger.warning(f"Order not found in Alpaca: {alpaca_order_id}")
                return

            alpaca_status = alpaca_order.get("status")

            # Check if status changed
            if alpaca_status != db_order.status:
                self.logger.info(
                    f"Order {order_id} status changed: {db_order.status} -> {alpaca_status}"
                )

                # Update status in database
                self.persistence.update_order_status(
                    alpaca_order_id,
                    alpaca_status,
                    float(alpaca_order.get("filled_qty", 0)),
                    float(alpaca_order.get("filled_avg_price", 0))
                    if alpaca_order.get("filled_avg_price")
                    else None,
                )

                # Handle different status changes
                if alpaca_status == "filled":
                    self._handle_filled_order(db_order, alpaca_order)
                elif alpaca_status == "partial":
                    self._handle_partial_fill(db_order, alpaca_order)
                elif alpaca_status == "cancelled":
                    self._handle_cancelled_order(db_order)
                elif alpaca_status == "rejected":
                    self._handle_rejected_order(db_order, alpaca_order)

        except Exception as e:
            self.logger.error(f"Error syncing order {order_id}: {e}")

    def _handle_filled_order(self, db_order: Order, alpaca_order: dict[str, Any]) -> None:
        """Handle filled order by creating trade record.

        Args:
            db_order: Database order record
            alpaca_order: Alpaca order data
        """
        try:
            order_id = int(db_order.id)

            self.logger.info(
                f"Order {order_id} filled: {db_order.symbol} {db_order.side} {db_order.quantity}"
            )

            # Create trade record
            trade_data = {
                "symbol": alpaca_order["symbol"],
                "qty": alpaca_order["filled_qty"],
                "price": alpaca_order["filled_avg_price"],
                "side": alpaca_order["side"],
                "commission": 0.0,  # Alpaca is commission-free
                "timestamp": alpaca_order.get("filled_at", datetime.utcnow()),
            }

            trade = self.persistence.persist_trade(trade_data, order_id)

            if trade:
                self.logger.info(f"Trade {trade.id} created for order {order_id}")

                # Update position
                self._update_position_from_trade(trade_data)

                # Add status message to bot
                if hasattr(self.bot, "add_status_message"):
                    self.bot.add_status_message(
                        f"Order filled: {trade_data['symbol']} {trade_data['side']} {trade_data['qty']} @ ${float(trade_data['price']):.2f}",
                        "trade",
                    )
            else:
                self.logger.error(f"Failed to create trade for order {order_id}")

        except Exception as e:
            self.logger.error(f"Error handling filled order {order_id}: {e}")

    def _handle_partial_fill(self, db_order: Order, alpaca_order: dict[str, Any]) -> None:
        """Handle partially filled order.

        Args:
            db_order: Database order record
            alpaca_order: Alpaca order data
        """
        try:
            filled_qty = float(alpaca_order.get("filled_qty", 0))
            total_qty = float(alpaca_order.get("qty", 0))

            self.logger.info(
                f"Order {db_order.id} partially filled: {filled_qty}/{total_qty} shares"
            )

            # Add status message
            if hasattr(self.bot, "add_status_message"):
                self.bot.add_status_message(
                    f"Partial fill: {db_order.symbol} {filled_qty}/{total_qty} shares", "info"
                )

        except Exception as e:
            self.logger.error(f"Error handling partial fill {db_order.id}: {e}")

    def _handle_cancelled_order(self, db_order: Order) -> None:
        """Handle cancelled order.

        Args:
            db_order: Database order record
        """
        self.logger.info(f"Order {db_order.id} cancelled: {db_order.symbol}")

        if hasattr(self.bot, "add_status_message"):
            self.bot.add_status_message(
                f"Order cancelled: {db_order.symbol} {db_order.side}", "warning"
            )

    def _handle_rejected_order(self, db_order: Order, alpaca_order: dict[str, Any]) -> None:
        """Handle rejected order.

        Args:
            db_order: Database order record
            alpaca_order: Alpaca order data
        """
        reason = alpaca_order.get("reject_reason", "Unknown")
        self.logger.warning(f"Order {db_order.id} rejected: {reason}")

        if hasattr(self.bot, "add_status_message"):
            self.bot.add_status_message(f"Order rejected: {db_order.symbol} - {reason}", "error")

    def _update_position_from_trade(self, trade_data: dict[str, Any]) -> None:
        """Update position based on trade execution.

        Args:
            trade_data: Trade data
        """
        try:
            symbol = trade_data["symbol"]
            float(trade_data["qty"])
            float(trade_data["price"])
            side = trade_data["side"]

            # Get current position from Alpaca
            positions = self.bot.alpaca_service.get_positions()
            position = next((p for p in positions if p["symbol"] == symbol), None)

            if position:
                # Update existing position
                self.persistence.update_position(
                    symbol=symbol,
                    quantity=float(position["qty"]),
                    avg_price=float(position["avg_entry_price"]),
                    current_price=float(position["current_price"]),
                    side=position.get("side", "long"),
                )
            elif side == "sell":
                # Position closed
                self.persistence.close_position(symbol)
                self.logger.info(f"Position closed: {symbol}")

        except Exception as e:
            self.logger.error(f"Error updating position from trade: {e}")

    def cancel_stale_orders(self, max_age_minutes: int = 60) -> int:
        """Cancel orders older than specified age.

        Args:
            max_age_minutes: Maximum age in minutes

        Returns:
            Number of orders cancelled
        """
        try:
            pending_orders = self.persistence.get_pending_orders()
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            cancelled_count = 0

            for order in pending_orders:
                if order.created_at < cutoff_time:
                    try:
                        # Cancel with Alpaca
                        alpaca_id = cast("str", order.alpaca_order_id)
                        self.bot.alpaca_service.cancel_order(alpaca_id)

                        # Update database
                        self.persistence.update_order_status(alpaca_id, "cancelled")

                        cancelled_count += 1
                        self.logger.info(f"Cancelled stale order: {order.id}")

                    except Exception as e:
                        self.logger.error(f"Error cancelling order {order.id}: {e}")

            return cancelled_count

        except Exception as e:
            self.logger.error(f"Error cancelling stale orders: {e}")
            return 0

    def get_order_statistics(self) -> dict[str, Any]:
        """Get order statistics.

        Returns:
            Dictionary with order statistics
        """
        try:
            from src.business.trading.repositories import OrderRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                portfolio = self.persistence.portfolio
                if portfolio is None:
                    return {}
                order_repo = OrderRepository(session)
                portfolio_id = int(portfolio.id)

                all_orders = order_repo.get_by_portfolio(portfolio_id, limit=1000)
                pending = order_repo.get_pending_orders(portfolio_id)
                filled = order_repo.get_filled_orders(portfolio_id, limit=100)

                return {
                    "total_orders": len(all_orders),
                    "pending_orders": len(pending),
                    "filled_orders": len(filled),
                    "fill_rate": len(filled) / len(all_orders) if all_orders else 0,
                }

        except Exception as e:
            self.logger.error(f"Error getting order statistics: {e}")
            return {}
