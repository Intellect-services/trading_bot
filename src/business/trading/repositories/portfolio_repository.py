"""Portfolio repository for portfolio-specific database operations."""

from sqlalchemy.orm import Session

from src.business.trading.models import Portfolio
from src.common.repositories.base_repository import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    """Repository for Portfolio model with custom methods."""

    def __init__(self, session: Session):
        """Initialize portfolio repository.

        Args:
            session: Database session
        """
        super().__init__(Portfolio, session)

    def get_by_user(self, user_id: int) -> list[Portfolio]:
        """Get all portfolios for a user.

        Args:
            user_id: User ID

        Returns:
            List of user's portfolios
        """
        return self.get_by_filter(user_id=user_id)

    def get_active_portfolio(self, user_id: int) -> Portfolio | None:
        """Get user's primary/active portfolio.

        Args:
            user_id: User ID

        Returns:
            Active portfolio or None
        """
        portfolios = self.get_by_user(user_id)
        return portfolios[0] if portfolios else None

    def get_paper_portfolios(self, user_id: int) -> list[Portfolio]:
        """Get user's paper trading portfolios.

        Args:
            user_id: User ID

        Returns:
            List of paper portfolios
        """
        return self.session.query(Portfolio).filter_by(user_id=user_id, is_paper=True).all()

    def get_live_portfolios(self, user_id: int) -> list[Portfolio]:
        """Get user's live trading portfolios.

        Args:
            user_id: User ID

        Returns:
            List of live portfolios
        """
        return self.session.query(Portfolio).filter_by(user_id=user_id, is_paper=False).all()

    def update_values(
        self, portfolio_id: int, current_value: float, cash_balance: float, buying_power: float
    ) -> Portfolio | None:
        """Update portfolio financial values.

        Args:
            portfolio_id: Portfolio ID
            current_value: Current total value
            cash_balance: Cash balance
            buying_power: Buying power

        Returns:
            Updated portfolio or None
        """
        return self.update(
            portfolio_id,
            current_value=current_value,
            cash_balance=cash_balance,
            buying_power=buying_power,
        )
