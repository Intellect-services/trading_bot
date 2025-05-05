"""Tests for the Alpaca service."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.models import Account, Asset, Clock, Order, Position

from src.core.alpaca_service import AlpacaService


class TestAlpacaService(unittest.TestCase):
    """Test cases for AlpacaService."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.api_key = "test_key"
        self.api_secret = "test_secret"
        self.service = AlpacaService(self.api_key, self.api_secret)

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_account(self, mock_client: MagicMock) -> None:
        """Test getting account information."""
        mock_account = MagicMock(spec=Account)
        mock_client.return_value.get_account.return_value = mock_account

        self.service.client = mock_client.return_value
        result = self.service.get_account()

        self.assertEqual(result, mock_account)
        mock_client.return_value.get_account.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_all_positions(self, mock_client: MagicMock) -> None:
        """Test getting all positions."""
        mock_positions = [MagicMock(spec=Position)]
        mock_client.return_value.get_positions.return_value = mock_positions

        self.service.client = mock_client.return_value
        result = self.service.get_all_positions()

        self.assertEqual(result, mock_positions)
        mock_client.return_value.get_positions.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_open_position(self, mock_client: MagicMock) -> None:
        """Test getting open position for a symbol."""
        symbol = "AAPL"
        mock_position = MagicMock(spec=Position)
        mock_position.symbol = symbol
        mock_client.return_value.get_positions.return_value = [mock_position]

        self.service.client = mock_client.return_value
        result = self.service.get_open_position(symbol)

        self.assertEqual(result, mock_position)
        mock_client.return_value.get_positions.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_clock(self, mock_client: MagicMock) -> None:
        """Test getting market clock."""
        mock_clock = MagicMock(spec=Clock)
        mock_client.return_value.get_clock.return_value = mock_clock

        self.service.client = mock_client.return_value
        result = self.service.get_clock()

        self.assertEqual(result, mock_clock)
        mock_client.return_value.get_clock.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_submit_order(self, mock_client: MagicMock) -> None:
        """Test submitting an order."""
        mock_order = MagicMock(spec=Order)
        mock_client.return_value.submit_order.return_value = mock_order

        self.service.client = mock_client.return_value
        result = self.service.submit_order(
            symbol="AAPL",
            qty=100.0,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        self.assertEqual(result, mock_order)
        mock_client.return_value.submit_order.assert_called_once_with(
            symbol="AAPL",
            qty=100.0,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            limit_price=None,
            stop_price=None,
        )

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_orders(self, mock_client: MagicMock) -> None:
        """Test getting orders."""
        mock_orders = [MagicMock(spec=Order)]
        mock_client.return_value.get_orders.return_value = mock_orders

        self.service.client = mock_client.return_value
        result = self.service.get_orders()

        self.assertEqual(result, mock_orders)
        mock_client.return_value.get_orders.assert_called_once_with()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_order_by_id(self, mock_client: MagicMock) -> None:
        """Test getting order by ID."""
        order_id = "test_order_id"
        mock_order = MagicMock(spec=Order)
        mock_client.return_value.get_order_by_id.return_value = mock_order

        self.service.client = mock_client.return_value
        result = self.service.get_order_by_id(order_id)

        self.assertEqual(result, mock_order)
        mock_client.return_value.get_order_by_id.assert_called_once_with(order_id)

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_cancel_order(self, mock_client: MagicMock) -> None:
        """Test canceling an order."""
        order_id = "test_order_id"

        self.service.client = mock_client.return_value
        self.service.cancel_order(order_id)

        mock_client.return_value.cancel_order.assert_called_once_with(order_id)

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_asset(self, mock_client: MagicMock) -> None:
        """Test getting asset information."""
        symbol = "AAPL"
        mock_asset = MagicMock(spec=Asset)
        mock_client.return_value.get_asset.return_value = mock_asset

        self.service.client = mock_client.return_value
        result = self.service.get_asset(symbol)

        self.assertEqual(result, mock_asset)
        mock_client.return_value.get_asset.assert_called_once_with(symbol)

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_bars(self, mock_client: MagicMock) -> None:
        """Test getting historical bars."""
        symbol = "AAPL"
        timeframe = TimeFrame.Day
        start = pd.Timestamp("2023-01-01")
        end = pd.Timestamp("2023-12-31")
        limit = 100

        mock_df = pd.DataFrame(
            {"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.5], "volume": [1000000]}
        )
        mock_client.return_value.get_bars.return_value = mock_df

        self.service.client = mock_client.return_value
        result = self.service.get_bars(
            symbol=symbol, timeframe=timeframe, start=start, end=end, limit=limit
        )

        pd.testing.assert_frame_equal(result, mock_df)
        mock_client.return_value.get_bars.assert_called_once_with(
            symbol=symbol, timeframe=timeframe, start=start, end=end, limit=limit
        )


if __name__ == "__main__":
    unittest.main()
