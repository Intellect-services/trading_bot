"""Signal repository for signal-specific database operations."""

from sqlalchemy.orm import Session

from src.business.strategy.models import Signal
from src.common.repositories.base_repository import BaseRepository


class SignalRepository(BaseRepository[Signal]):
    """Repository for Signal model with custom methods."""

    def __init__(self, session: Session):
        """Initialize signal repository.

        Args:
            session: Database session
        """
        super().__init__(Signal, session)

    def get_by_strategy(self, strategy_id: int, limit: int = 100) -> list[Signal]:
        """Get signals for a strategy.

        Args:
            strategy_id: Strategy ID
            limit: Maximum number of signals

        Returns:
            List of signals
        """
        return (
            self.session.query(Signal)
            .filter_by(strategy_id=strategy_id)
            .order_by(Signal.generated_at.desc())
            .limit(limit)
            .all()
        )

    def get_unexecuted_signals(self, strategy_id: int) -> list[Signal]:
        """Get unexecuted signals for a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            List of unexecuted signals
        """
        return self.session.query(Signal).filter_by(strategy_id=strategy_id, executed=False).all()

    def mark_executed(self, signal_id: int) -> Signal | None:
        """Mark signal as executed.

        Args:
            signal_id: Signal ID

        Returns:
            Updated signal or None
        """
        return self.update(signal_id, executed=True)
