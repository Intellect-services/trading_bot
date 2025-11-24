"""Database persistence helper for TradingBot."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
else:
    Session = Any

from src.business.trading.models import Order, Portfolio, Position, Trade
from src.business.trading.repositories import (
    OrderRepository,
    PortfolioRepository,
    PositionRepository,
    TradeRepository,
)
from src.common.models import AuditLog
from src.common.repositories import BaseRepository
from src.infrastructure import db_config

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> float:
    """Safely convert arbitrary input to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class TradingBotPersistence:
    """Helper class for persisting trading data to database."""

    def __init__(self, user_id: int) -> None:
        """Initialize persistence helper.

        Args:
            user_id: User ID for this trading session
        """
        self.user_id = user_id
        self.session: Session | None = None
        self.portfolio_repo: PortfolioRepository | None = None
        self.position_repo: PositionRepository | None = None
        self.order_repo: OrderRepository | None = None
        self.trade_repo: TradeRepository | None = None
        self.audit_repo: BaseRepository[AuditLog] | None = None
        self.portfolio: Portfolio | None = None

    def initialize(self) -> bool:
        """Initialize database session and repositories.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create database session
            self.session = next(db_config.get_db())

            # Initialize repositories
            self.portfolio_repo = PortfolioRepository(self.session)
            self.position_repo = PositionRepository(self.session)
            self.order_repo = OrderRepository(self.session)
            self.trade_repo = TradeRepository(self.session)
            self.audit_repo = BaseRepository(AuditLog, self.session)

            # Load or create portfolio
            self.portfolio = self.portfolio_repo.get_active_portfolio(self.user_id)

            portfolio = self.portfolio
            if portfolio is None:
                logger.info(f"Creating new portfolio for user {self.user_id}")
                self.portfolio = self.portfolio_repo.create(
                    user_id=self.user_id,
                    name="Main Trading Account",
                    description="Primary trading portfolio",
                    initial_capital=100000.00,
                    current_value=100000.00,
                    cash_balance=100000.00,
                    buying_power=200000.00,
                    is_paper=True,
                )

            portfolio = self.portfolio
            if portfolio is None:
                logger.error("Failed to create or load portfolio.")
                return False

            portfolio_id: int = int(portfolio.id)
            logger.info(f"Initialized persistence for portfolio {portfolio_id}")
            return True

        except Exception as e:
            logger.error(f"Error initializing persistence: {e}")
            return False

    def persist_order(self, order_data: dict[str, Any]) -> Order | None:
        """Persist order to database.

        Args:
            order_data: Order data from Alpaca

        Returns:
            Created Order or None
        """
        try:
            if self.order_repo is None or self.portfolio is None:
                return None
            portfolio_id: int = int(self.portfolio.id)
            limit_raw = order_data.get("limit_price")
            stop_raw = order_data.get("stop_price")
            filled_avg_raw = order_data.get("filled_avg_price")
            order = self.order_repo.create(
                portfolio_id=portfolio_id,
                alpaca_order_id=order_data.get("id"),
                symbol=order_data.get("symbol"),
                quantity=_to_float(order_data.get("qty")),
                filled_quantity=_to_float(order_data.get("filled_qty")),
                side=order_data.get("side"),
                type=order_data.get("type"),
                time_in_force=order_data.get("time_in_force"),
                status=order_data.get("status"),
                limit_price=float(limit_raw) if limit_raw is not None else None,
                stop_price=float(stop_raw) if stop_raw is not None else None,
                filled_avg_price=float(filled_avg_raw) if filled_avg_raw is not None else None,
            )

            # Create audit log
            order_id: int = int(order.id)
            self._create_audit_log(
                "order",
                order_id,
                "create",
                {
                    "symbol": str(order.symbol),
                    "side": str(order.side),
                    "quantity": float(order.quantity),
                },
            )

            logger.info(f"Persisted order {order.id} for {order.symbol}")
            return order

        except Exception as e:
            logger.error(f"Error persisting order: {e}")
            return None

    def update_order_status(
        self,
        alpaca_order_id: str,
        status: str,
        filled_qty: float | None = None,
        filled_avg_price: float | None = None,
    ) -> Order | None:
        """Update order status.

        Args:
            alpaca_order_id: Alpaca order ID
            status: New status
            filled_qty: Filled quantity (if applicable)
            filled_avg_price: Average fill price (if applicable)

        Returns:
            Updated Order or None
        """
        try:
            if self.order_repo is None:
                return None
            order = self.order_repo.get_by_alpaca_id(alpaca_order_id)
            if not order:
                logger.warning(f"Order not found: {alpaca_order_id}")
                return None

            order_id: int = int(order.id)
            order_qty: float = float(order.quantity)

            if status == "filled":
                order = self.order_repo.mark_filled(
                    order_id, filled_qty or order_qty, filled_avg_price or 0.0
                )
            elif status == "partial":
                order = self.order_repo.mark_partial(
                    order_id, filled_qty or 0.0, filled_avg_price or 0.0
                )
            elif status == "cancelled":
                order = self.order_repo.mark_cancelled(order_id)
            elif status == "rejected":
                order = self.order_repo.mark_rejected(order_id)

            if order:
                logger.info(f"Updated order {order_id} status to {status}")
            return order

        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return None

    def persist_trade(self, trade_data: dict[str, Any], order_id: int) -> Trade | None:
        """Persist trade to database.

        Args:
            trade_data: Trade data
            order_id: Associated order ID

        Returns:
            Created Trade or None
        """
        try:
            if self.trade_repo is None or self.portfolio is None:
                return None
            portfolio_id: int = int(self.portfolio.id)
            trade = self.trade_repo.create(
                order_id=order_id,
                portfolio_id=portfolio_id,
                symbol=trade_data.get("symbol"),
                quantity=float(trade_data.get("qty", 0)),
                price=float(trade_data.get("price", 0)),
                side=trade_data.get("side"),
                commission=float(trade_data.get("commission", 0)),
                executed_at=trade_data.get("timestamp", datetime.utcnow()),
            )

            # Create audit log
            trade_id: int = int(trade.id)
            self._create_audit_log(
                "trade",
                trade_id,
                "create",
                {
                    "symbol": str(trade.symbol),
                    "side": str(trade.side),
                    "quantity": float(trade.quantity),
                    "price": float(trade.price),
                },
            )

            logger.info(f"Persisted trade {trade.id} for {trade.symbol}")
            return trade

        except Exception as e:
            logger.error(f"Error persisting trade: {e}")
            return None

    def update_position(
        self,
        symbol: str,
        quantity: float,
        avg_price: float,
        current_price: float,
        side: str = "long",
    ) -> Position | None:
        """Update or create position.

        Args:
            symbol: Stock symbol
            quantity: Position quantity
            avg_price: Average entry price
            current_price: Current market price
            side: Position side (long/short)

        Returns:
            Updated/created Position or None
        """
        try:
            if self.position_repo is None or self.portfolio is None:
                return None
            portfolio_id: int = int(self.portfolio.id)
            position = self.position_repo.get_by_symbol(portfolio_id, symbol)

            if position:
                # Update existing position
                existing_position_id = int(position.id)
                position = self.position_repo.update_price(
                    existing_position_id, Decimal(str(current_price))
                )
            else:
                # Create new position
                market_value = quantity * current_price
                unrealized_pl = market_value - (quantity * avg_price)
                unrealized_pl_percent = (
                    (unrealized_pl / (quantity * avg_price)) * 100 if avg_price > 0 else 0
                )

                position = self.position_repo.create(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=Decimal(str(quantity)),
                    avg_entry_price=Decimal(str(avg_price)),
                    current_price=Decimal(str(current_price)),
                    market_value=Decimal(str(market_value)),
                    unrealized_pl=Decimal(str(unrealized_pl)),
                    unrealized_pl_percent=Decimal(str(unrealized_pl_percent)),
                    side=side,
                    opened_at=datetime.utcnow(),
                )

                # Create audit log
                new_position_id = int(position.id)
                self._create_audit_log(
                    "position",
                    new_position_id,
                    "create",
                    {"symbol": symbol, "quantity": quantity, "side": side},
                )

            logger.info(f"Updated position for {symbol}")
            return position

        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return None

    def close_position(self, symbol: str) -> bool:
        """Close a position.

        Args:
            symbol: Stock symbol

        Returns:
            True if closed, False otherwise
        """
        try:
            if self.position_repo is None or self.portfolio is None:
                return False
            portfolio_id: int = int(self.portfolio.id)
            position = self.position_repo.get_by_symbol(portfolio_id, symbol)
            if position:
                # Create audit log before deletion
                position_id: int = int(position.id)
                self._create_audit_log(
                    "position",
                    position_id,
                    "delete",
                    {
                        "symbol": symbol,
                        "final_pl": float(position.unrealized_pl) if position.unrealized_pl else 0,
                    },
                )

                self.position_repo.close_position(position_id)
                logger.info(f"Closed position for {symbol}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def update_portfolio_values(
        self, current_value: float, cash_balance: float, buying_power: float
    ) -> Portfolio | None:
        """Update portfolio financial values.

        Args:
            current_value: Current total value
            cash_balance: Cash balance
            buying_power: Buying power

        Returns:
            Updated Portfolio or None
        """
        try:
            if self.portfolio_repo is None or self.portfolio is None:
                return None
            portfolio_id: int = int(self.portfolio.id)
            portfolio = self.portfolio_repo.update_values(
                portfolio_id, current_value, cash_balance, buying_power
            )
            logger.info(f"Updated portfolio values: ${current_value:,.2f}")
            return portfolio

        except Exception as e:
            logger.error(f"Error updating portfolio values: {e}")
            return None

    def get_open_positions(self) -> list[Position]:
        """Get all open positions.

        Returns:
            List of Position objects
        """
        try:
            if self.position_repo is None or self.portfolio is None:
                return []
            portfolio_id: int = int(self.portfolio.id)
            return self.position_repo.get_by_portfolio(portfolio_id)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_pending_orders(self) -> list[Order]:
        """Get all pending orders.

        Returns:
            List of Order objects
        """
        try:
            if self.order_repo is None or self.portfolio is None:
                return []
            portfolio_id: int = int(self.portfolio.id)
            return self.order_repo.get_pending_orders(portfolio_id)
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []

    def _create_audit_log(
        self, entity_type: str, entity_id: int, action: str, changes: dict[str, Any]
    ) -> None:
        """Create audit log entry.

        Args:
            entity_type: Type of entity (order, trade, position)
            entity_id: Entity ID
            action: Action performed (create, update, delete)
            changes: Changes made
        """
        try:
            if self.audit_repo is None:
                return
            self.audit_repo.create(
                user_id=self.user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                changes=changes,
            )
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")

    def cleanup(self) -> None:
        """Cleanup database session."""
        if self.session:
            self.session.close()
            logger.info("Database session closed")
