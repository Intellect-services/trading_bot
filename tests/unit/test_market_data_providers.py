"""Tests for external data providers."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.core.data_providers.alpha_vantage import AlphaVantageProvider
from src.core.data_providers.yahoo_finance import YahooFinanceProvider


@patch("src.core.data_providers.yahoo_finance.yf.Ticker")
def test_yahoo_finance_provider_returns_records(mock_ticker: Mock) -> None:
    """YahooFinanceProvider should convert history DataFrame into dict records."""

    df = pd.DataFrame(
        [
            {
                "Open": 100.0,
                "High": 101.0,
                "Low": 99.0,
                "Close": 100.5,
                "Volume": 1500,
            }
        ],
        index=pd.to_datetime(["2024-01-01"]),
    )
    mock_ticker.return_value.history.return_value = df

    provider = YahooFinanceProvider()
    records = provider.get_historical_data(
        symbol="AAPL",
        timeframe="1Day",
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
    )

    assert len(records) == 1
    assert records[0]["close"] == pytest.approx(100.5)
    assert records[0]["source"] == "yahoo"


@patch("src.core.data_providers.alpha_vantage.requests.get")
def test_alpha_vantage_provider_parses_response(mock_get: Mock) -> None:
    """AlphaVantageProvider should parse API payloads into dict records."""

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "Time Series (5min)": {
            "2024-01-01 10:00:00": {
                "1. open": "100",
                "2. high": "101",
                "3. low": "99",
                "4. close": "100.4",
                "5. volume": "1200",
            }
        }
    }
    mock_get.return_value = mock_response

    provider = AlphaVantageProvider(api_key="demo")
    records = provider.get_intraday_data(symbol="AAPL", timeframe="5Min", limit=1)

    assert len(records) == 1
    assert records[0]["close"] == pytest.approx(100.4)
    assert records[0]["source"] == "alpha_vantage"
