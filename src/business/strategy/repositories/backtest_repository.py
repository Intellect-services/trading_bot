"""BacktestResult repository for backtest-specific database operations."""

from sqlalchemy.orm import Session

from src.business.strategy.models import BacktestResult
from src.common.repositories.base_repository import BaseRepository


class BacktestResultRepository(BaseRepository[BacktestResult]):
    """Repository for BacktestResult model with custom methods."""

    def __init__(self, session: Session):
        """Initialize backtest result repository.

        Args:
            session: Database session
        """
        super().__init__(BacktestResult, session)

    def get_by_strategy(self, strategy_id: int, limit: int = 10) -> list[BacktestResult]:
        """Get backtest results for a strategy.

        Args:
            strategy_id: Strategy ID
            limit: Maximum number of results

        Returns:
            List of backtest results
        """
        return (
            self.session.query(BacktestResult)
            .filter_by(strategy_id=strategy_id)
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_best_result(self, strategy_id: int) -> BacktestResult | None:
        """Get best backtest result for a strategy (by Sharpe ratio).

        Args:
            strategy_id: Strategy ID

        Returns:
            Best backtest result or None
        """
        return (
            self.session.query(BacktestResult)
            .filter_by(strategy_id=strategy_id)
            .order_by(BacktestResult.sharpe_ratio.desc())
            .first()
        )
