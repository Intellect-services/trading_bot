"""Order repository for order-specific database operations."""

from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.business.trading.models import Order
from src.common.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order model with custom methods."""

    def __init__(self, session: Session):
        """Initialize order repository.

        Args:
            session: Database session
        """
        super().__init__(Order, session)

    def get_by_portfolio(self, portfolio_id: int, limit: int = 100) -> list[Order]:
        """Get orders for a portfolio.

        Args:
            portfolio_id: Portfolio ID
            limit: Maximum number of orders to return

        Returns:
            List of orders
        """
        return (
            self.session.query(Order)
            .filter_by(portfolio_id=portfolio_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_alpaca_id(self, alpaca_order_id: str) -> Order | None:
        """Get order by Alpaca order ID.

        Args:
            alpaca_order_id: Alpaca order ID

        Returns:
            Order or None
        """
        return self.get_one_by_filter(alpaca_order_id=alpaca_order_id)

    def get_pending_orders(self, portfolio_id: int) -> list[Order]:
        """Get all pending orders for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of pending orders
        """
        return (
            self.session.query(Order)
            .filter(
                and_(
                    Order.portfolio_id == portfolio_id,
                    or_(Order.status == "pending", Order.status == "partial"),
                )
            )
            .all()
        )

    def get_filled_orders(self, portfolio_id: int, limit: int = 50) -> list[Order]:
        """Get filled orders for a portfolio.

        Args:
            portfolio_id: Portfolio ID
            limit: Maximum number of orders

        Returns:
            List of filled orders
        """
        return (
            self.session.query(Order)
            .filter(and_(Order.portfolio_id == portfolio_id, Order.status == "filled"))
            .order_by(Order.filled_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_symbol(self, portfolio_id: int, symbol: str) -> list[Order]:
        """Get orders for a specific symbol.

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol

        Returns:
            List of orders
        """
        return (
            self.session.query(Order)
            .filter(and_(Order.portfolio_id == portfolio_id, Order.symbol == symbol))
            .order_by(Order.created_at.desc())
            .all()
        )

    def mark_filled(
        self,
        order_id: int,
        filled_quantity: float,
        filled_avg_price: float,
        commission: float = 0.0,
    ) -> Order | None:
        """Mark order as filled.

        Args:
            order_id: Order ID
            filled_quantity: Quantity filled
            filled_avg_price: Average fill price
            commission: Commission paid

        Returns:
            Updated order or None
        """
        return self.update(
            order_id,
            status="filled",
            filled_quantity=filled_quantity,
            filled_avg_price=filled_avg_price,
            commission=commission,
            filled_at=datetime.utcnow(),
        )

    def mark_partial(
        self, order_id: int, filled_quantity: float, filled_avg_price: float
    ) -> Order | None:
        """Mark order as partially filled.

        Args:
            order_id: Order ID
            filled_quantity: Quantity filled so far
            filled_avg_price: Average fill price

        Returns:
            Updated order or None
        """
        return self.update(
            order_id,
            status="partial",
            filled_quantity=filled_quantity,
            filled_avg_price=filled_avg_price,
        )

    def mark_cancelled(self, order_id: int) -> Order | None:
        """Mark order as cancelled.

        Args:
            order_id: Order ID

        Returns:
            Updated order or None
        """
        return self.update(order_id, status="cancelled", cancelled_at=datetime.utcnow())

    def mark_rejected(self, order_id: int) -> Order | None:
        """Mark order as rejected.

        Args:
            order_id: Order ID

        Returns:
            Updated order or None
        """
        return self.update(order_id, status="rejected")
