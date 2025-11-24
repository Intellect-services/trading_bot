"""Tests for configuration utilities."""

import os

import pytest

from src.utils.config import (
    Config,
    get_config,
    load_config_from_file,
    save_config_to_file,
    set_config,
    validate_config,
)


def test_get_and_set_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure helper functions read/write environment variables."""
    monkeypatch.delenv("SAMPLE_KEY", raising=False)
    set_config("SAMPLE_KEY", "value123")
    assert get_config("SAMPLE_KEY") == "value123"


def test_load_and_save_config(tmp_path) -> None:
    """Round-trip configuration to disk."""
    cfg = {"API_KEY": "abc", "TIMEOUT": "5"}
    config_path = tmp_path / "config.env"
    save_config_to_file(cfg, config_path.as_posix())

    loaded = load_config_from_file(config_path.as_posix())
    assert loaded == cfg


def test_validate_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """validate_config raises when required keys missing."""
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")
    monkeypatch.setenv("DEFAULT_SYMBOL", "AAPL")
    monkeypatch.setenv("MARKET_OPEN", "09:30")
    monkeypatch.setenv("MARKET_CLOSE", "16:00")
    assert validate_config(dict(os.environ))


def test_validate_config_missing_key() -> None:
    """Missing required key triggers ValueError."""
    with pytest.raises(ValueError):
        validate_config({"ALPACA_API_KEY": "key"})


def test_config_model_validations() -> None:
    """Pydantic validators enforce windows and percentages."""
    cfg = Config(
        trading_stop_loss=0.02,
        trading_take_profit=0.04,
        risk_max_position_size=0.1,
        risk_max_daily_loss=0.05,
        risk_max_drawdown=0.1,
        short_window=10,
        long_window=20,
    )
    assert cfg.short_window == 10
    assert cfg.long_window == 20

    with pytest.raises(ValueError):
        Config(short_window=20, long_window=10)
