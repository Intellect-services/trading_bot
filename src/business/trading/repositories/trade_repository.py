"""Trade repository for trade-specific database operations."""

from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.business.trading.models import Trade
from src.common.repositories.base_repository import BaseRepository


class TradeRepository(BaseRepository[Trade]):
    """Repository for Trade model with custom methods."""

    def __init__(self, session: Session):
        """Initialize trade repository.

        Args:
            session: Database session
        """
        super().__init__(Trade, session)

    def get_by_portfolio(self, portfolio_id: int, limit: int = 100) -> list[Trade]:
        """Get trades for a portfolio.

        Args:
            portfolio_id: Portfolio ID
            limit: Maximum number of trades

        Returns:
            List of trades
        """
        return (
            self.session.query(Trade)
            .filter_by(portfolio_id=portfolio_id)
            .order_by(Trade.executed_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_order(self, order_id: int) -> list[Trade]:
        """Get all trades for an order.

        Args:
            order_id: Order ID

        Returns:
            List of trades
        """
        return self.get_by_filter(order_id=order_id)

    def get_by_symbol(self, portfolio_id: int, symbol: str) -> list[Trade]:
        """Get trades for a specific symbol.

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol

        Returns:
            List of trades
        """
        return (
            self.session.query(Trade)
            .filter(and_(Trade.portfolio_id == portfolio_id, Trade.symbol == symbol))
            .order_by(Trade.executed_at.desc())
            .all()
        )

    def get_today_trades(self, portfolio_id: int) -> list[Trade]:
        """Get today's trades for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of today's trades
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.session.query(Trade)
            .filter(and_(Trade.portfolio_id == portfolio_id, Trade.executed_at >= today_start))
            .all()
        )

    def get_trades_by_date_range(
        self, portfolio_id: int, start_date: datetime, end_date: datetime
    ) -> list[Trade]:
        """Get trades within a date range.

        Args:
            portfolio_id: Portfolio ID
            start_date: Start date
            end_date: End date

        Returns:
            List of trades
        """
        return (
            self.session.query(Trade)
            .filter(
                and_(
                    Trade.portfolio_id == portfolio_id,
                    Trade.executed_at >= start_date,
                    Trade.executed_at <= end_date,
                )
            )
            .order_by(Trade.executed_at.desc())
            .all()
        )

    def get_winning_trades(self, portfolio_id: int) -> list[Trade]:
        """Get all winning trades (realized P&L > 0).

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of winning trades
        """
        return (
            self.session.query(Trade)
            .filter(and_(Trade.portfolio_id == portfolio_id, Trade.realized_pl > 0))
            .all()
        )

    def get_losing_trades(self, portfolio_id: int) -> list[Trade]:
        """Get all losing trades (realized P&L < 0).

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of losing trades
        """
        return (
            self.session.query(Trade)
            .filter(and_(Trade.portfolio_id == portfolio_id, Trade.realized_pl < 0))
            .all()
        )

    def get_total_pnl(self, portfolio_id: int) -> float:
        """Calculate total realized P&L for portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Total realized P&L
        """
        result = (
            self.session.query(func.sum(Trade.realized_pl))
            .filter_by(portfolio_id=portfolio_id)
            .scalar()
        )

        return float(result) if result else 0.0

    def get_trade_count(self, portfolio_id: int) -> int:
        """Get total trade count for portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Total number of trades
        """
        return self.count(portfolio_id=portfolio_id)
