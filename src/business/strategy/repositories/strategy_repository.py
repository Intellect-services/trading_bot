"""Strategy repository for strategy-specific database operations."""

from sqlalchemy.orm import Session

from src.business.strategy.models import Strategy
from src.common.repositories.base_repository import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for Strategy model with custom methods."""

    def __init__(self, session: Session):
        """Initialize strategy repository.

        Args:
            session: Database session
        """
        super().__init__(Strategy, session)

    def get_by_user(self, user_id: int) -> list[Strategy]:
        """Get all strategies for a user.

        Args:
            user_id: User ID

        Returns:
            List of user's strategies
        """
        return self.get_by_filter(user_id=user_id)

    def get_active_strategies(self, user_id: int) -> list[Strategy]:
        """Get active strategies for a user.

        Args:
            user_id: User ID

        Returns:
            List of active strategies
        """
        return self.session.query(Strategy).filter_by(user_id=user_id, is_active=True).all()

    def get_by_type(self, user_id: int, strategy_type: str) -> list[Strategy]:
        """Get strategies by type."""
        return self.session.query(Strategy).filter_by(user_id=user_id, type=strategy_type).all()

    def create_strategy(
        self,
        user_id: int,
        name: str,
        strategy_type: str,
        parameters: dict,
        description: str | None = None,
    ) -> Strategy:
        """Create and persist a new strategy."""

        strategy = Strategy(
            user_id=user_id,
            name=name,
            type=strategy_type,
            parameters=parameters,
            description=description,
        )
        self.session.add(strategy)
        self.session.commit()
        return strategy
