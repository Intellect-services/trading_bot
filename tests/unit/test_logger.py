"""Tests for logger utilities."""

import logging

from src.utils.logger import BotLogger, setup_logger


def test_setup_logger_creates_handlers(tmp_path) -> None:
    """Logger writes to console and optional file."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "bot.log"

    logger = setup_logger("tests.logger", level=logging.DEBUG, log_file=str(log_file))
    logger.info("hello world")

    assert log_file.exists()
    assert log_file.read_text() != ""


def test_bot_logger_methods(caplog) -> None:
    """BotLogger proxies helper methods to underlying logger."""
    bot_logger = BotLogger("bot.logger.test")
    with caplog.at_level(logging.INFO):
        bot_logger.log_trade("AAPL", "buy", 5, 150.5, "filled")
        bot_logger.log_account_update(100_000, 50_000, 150_000)
        bot_logger.log_position_update("MSFT", 10, 300.0, 3_000.0)
        bot_logger.log_info("informational")
        bot_logger.log_warning("caution")
    with caplog.at_level(logging.ERROR):
        bot_logger.log_error("error message")
        bot_logger.log_error("exception message", ValueError("boom"))

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "Trade executed" in messages
    assert "Account update" in messages
    assert "Position update" in messages
    assert "informational" in messages
    assert "caution" in messages
    assert "error message" in messages
    assert "exception message" in messages
