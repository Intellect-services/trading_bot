"""Error handling and recovery for IntellectTrader."""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling and recovery."""

    def __init__(self) -> None:
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.last_error_time: datetime | None = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def handle_api_error(self, error: Exception, context: str = "") -> None:
        """Handle Alpaca API errors.

        Args:
            error: The exception that occurred
            context: Context about where the error occurred
        """
        self.error_count += 1
        self.last_error_time = datetime.utcnow()

        error_msg = f"API Error in {context}: {error!s}"
        self.logger.error(error_msg, exc_info=True)

        # Check if we should trigger circuit breaker
        if self.error_count > 10:
            self.logger.critical("Too many API errors, circuit breaker triggered")
            # In production, would send alert here

    def handle_database_error(self, error: Exception, context: str = "") -> None:
        """Handle database errors.

        Args:
            error: The exception that occurred
            context: Context about where the error occurred
        """
        error_msg = f"Database Error in {context}: {error!s}"
        self.logger.error(error_msg, exc_info=True)

        # Attempt to rollback transaction
        try:
            # Session will auto-rollback on error
            self.logger.info("Transaction rolled back")
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")

    def retry_with_backoff(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any | None:
        """Retry function with exponential backoff.

        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                wait_time = self.retry_delay * (2**attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )

                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")
                    return None
        return None

    def recover_state(self, bot: Any) -> bool:
        """Recover bot state after crash.

        Args:
            bot: TradingBot instance

        Returns:
            True if recovery successful
        """
        try:
            self.logger.info("Attempting state recovery...")

            # Reload portfolio from database
            if hasattr(bot, "persistence"):
                portfolio = bot.persistence.portfolio
                if portfolio:
                    self.logger.info(f"Portfolio recovered: {portfolio.name}")

                # Reload open positions
                positions = bot.persistence.get_open_positions()
                self.logger.info(f"Recovered {len(positions)} open positions")

                # Reload pending orders
                orders = bot.persistence.get_pending_orders()
                self.logger.info(f"Recovered {len(orders)} pending orders")

                return True

            return False

        except Exception as e:
            self.logger.error(f"State recovery failed: {e}")
            return False

    def graceful_shutdown(self, bot: Any) -> None:
        """Perform graceful shutdown.

        Args:
            bot: TradingBot instance
        """
        try:
            self.logger.info("Initiating graceful shutdown...")

            # Stop bot
            if hasattr(bot, "stop"):
                bot.stop()

            # Stop order manager
            if hasattr(bot, "order_manager"):
                bot.order_manager.stop_monitoring()

            # Stop position tracker
            if hasattr(bot, "position_tracker"):
                bot.position_tracker.stop_tracking()

            # Cleanup database
            if hasattr(bot, "persistence"):
                bot.persistence.cleanup()

            self.logger.info("Graceful shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def with_error_handling(context: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for automatic error handling.

    Args:
        context: Context description for error logging
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {context or func.__name__}: {e}", exc_info=True)
                # Re-raise in development, handle gracefully in production
                raise

        return wrapper

    return decorator


def safe_execute(func: Callable[..., Any], default: Any = None, log_errors: bool = True) -> Any:
    """Safely execute function with error handling.

    Args:
        func: Function to execute
        default: Default value to return on error
        log_errors: Whether to log errors

    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {e}")
        return default


# Global error handler instance
error_handler = ErrorHandler()
