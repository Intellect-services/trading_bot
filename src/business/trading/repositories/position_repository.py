"""Position repository for position-specific database operations."""

from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.business.trading.models import Position
from src.common.repositories.base_repository import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """Repository for Position model with custom methods."""

    def __init__(self, session: Session):
        """Initialize position repository.

        Args:
            session: Database session
        """
        super().__init__(Position, session)

    def get_by_portfolio(self, portfolio_id: int) -> list[Position]:
        """Get all positions for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of positions
        """
        return self.get_by_filter(portfolio_id=portfolio_id)

    def get_by_symbol(self, portfolio_id: int, symbol: str) -> Position | None:
        """Get position for a specific symbol in portfolio.

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol

        Returns:
            Position or None
        """
        return (
            self.session.query(Position)
            .filter(and_(Position.portfolio_id == portfolio_id, Position.symbol == symbol))
            .first()
        )

    def get_long_positions(self, portfolio_id: int) -> list[Position]:
        """Get all long positions for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of long positions
        """
        return (
            self.session.query(Position)
            .filter(and_(Position.portfolio_id == portfolio_id, Position.side == "long"))
            .all()
        )

    def get_short_positions(self, portfolio_id: int) -> list[Position]:
        """Get all short positions for a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of short positions
        """
        return (
            self.session.query(Position)
            .filter(and_(Position.portfolio_id == portfolio_id, Position.side == "short"))
            .all()
        )

    def update_price(self, position_id: int, current_price: Decimal) -> Position | None:
        """Update position with current price and recalculate P&L.

        Args:
            position_id: Position ID
            current_price: Current market price

        Returns:
            Updated position or None
        """
        position = self.get_by_id(position_id)
        if not position:
            return None

        # Calculate market value and P&L
        market_value = float(position.quantity) * float(current_price)
        unrealized_pl = market_value - (float(position.quantity) * float(position.avg_entry_price))
        unrealized_pl_percent = (
            unrealized_pl / (float(position.quantity) * float(position.avg_entry_price))
        ) * 100

        return self.update(
            position_id,
            current_price=current_price,
            market_value=market_value,
            unrealized_pl=unrealized_pl,
            unrealized_pl_percent=unrealized_pl_percent,
        )

    def close_position(self, position_id: int) -> bool:
        """Close (delete) a position.

        Args:
            position_id: Position ID

        Returns:
            True if closed, False otherwise
        """
        return self.delete(position_id)
