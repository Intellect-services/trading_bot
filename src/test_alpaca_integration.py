"""Integration tests for the Alpaca service."""

import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.models import Account, Asset, Clock, Order, Position

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Asset as AssetProtocol
from src.core.alpaca_types import BarSet as BarSetProtocol
from src.core.alpaca_types import Clock as ClockProtocol
from src.core.alpaca_types import Order as OrderProtocol
from src.core.alpaca_types import Position as PositionProtocol
from src.core.alpaca_types import TradeAccount as TradeAccountProtocol
from src.core.config import Config


class TestAlpacaIntegration(unittest.TestCase):
    """Integration tests for the Alpaca service."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = Config.from_dict(
            {
                "ALPACA_API_KEY": "test_key",
                "ALPACA_SECRET_KEY": "test_secret",
                "ALPACA_PAPER": True,
                "INITIAL_CAPITAL": 10000.0,
                "RISK_MAX_POSITION_SIZE": 0.1,
                "RISK_PER_TRADE": 0.02,
                "RISK_STOP_LOSS_PCT": 0.02,
                "RISK_TAKE_PROFIT_PCT": 0.04,
                "RISK_MAX_DRAWDOWN": 0.2,
                "RISK_MAX_LEVERAGE": 1.0,
                "STRATEGY_SHORT_WINDOW": 20,
                "STRATEGY_LONG_WINDOW": 50,
            }
        )
        self.service = AlpacaService(self.config.api_key, self.config.api_secret)

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_account(self, mock_client: MagicMock) -> None:
        """Test getting account information."""
        mock_account = MagicMock(spec=Account)
        mock_account.buying_power = 100000.0
        mock_account.cash = 50000.0
        mock_client.return_value.get_account.return_value = mock_account

        self.service.client = mock_client.return_value
        result = self.service.get_account()

        self.assertEqual(result, mock_account)
        self.assertEqual(result.buying_power, 100000.0)
        self.assertEqual(result.cash, 50000.0)
        mock_client.return_value.get_account.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_all_positions(self, mock_client: MagicMock) -> None:
        """Test getting all positions."""
        mock_position = MagicMock(spec=Position)
        mock_position.symbol = "AAPL"
        mock_position.qty = 100
        mock_position.market_value = 15000.0
        mock_positions = [mock_position]
        mock_client.return_value.get_positions.return_value = mock_positions

        self.service.client = mock_client.return_value
        result = self.service.get_all_positions()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol, "AAPL")
        self.assertEqual(result[0].qty, 100)
        self.assertEqual(result[0].market_value, 15000.0)
        mock_client.return_value.get_positions.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_open_position(self, mock_client: MagicMock) -> None:
        """Test getting open position for a symbol."""
        mock_position = MagicMock(spec=Position)
        mock_position.symbol = "AAPL"
        mock_position.qty = 100
        mock_position.market_value = 15000.0
        mock_client.return_value.get_positions.return_value = [mock_position]

        self.service.client = mock_client.return_value
        result = self.service.get_open_position("AAPL")

        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.qty, 100)
        self.assertEqual(result.market_value, 15000.0)
        mock_client.return_value.get_positions.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_clock(self, mock_client: MagicMock) -> None:
        """Test getting market clock."""
        mock_clock = MagicMock(spec=Clock)
        mock_clock.is_open = True
        mock_client.return_value.get_clock.return_value = mock_clock

        self.service.client = mock_client.return_value
        result = self.service.get_clock()

        self.assertEqual(result, mock_clock)
        self.assertTrue(result.is_open)
        mock_client.return_value.get_clock.assert_called_once()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_submit_order(self, mock_client: MagicMock) -> None:
        """Test submitting an order."""
        mock_order = MagicMock(spec=Order)
        mock_order.symbol = "AAPL"
        mock_order.qty = 100
        mock_order.filled_qty = 100
        mock_order.status = "filled"
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
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.qty, 100)
        self.assertEqual(result.filled_qty, 100)
        self.assertEqual(result.status, "filled")
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
        mock_order = MagicMock(spec=Order)
        mock_order.symbol = "AAPL"
        mock_order.qty = 100
        mock_order.status = "filled"
        mock_orders = [mock_order]
        mock_client.return_value.get_orders.return_value = mock_orders

        self.service.client = mock_client.return_value
        result = self.service.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol, "AAPL")
        self.assertEqual(result[0].qty, 100)
        self.assertEqual(result[0].status, "filled")
        mock_client.return_value.get_orders.assert_called_once_with()

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_order_by_id(self, mock_client: MagicMock) -> None:
        """Test getting order by ID."""
        order_id = "test_order_id"
        mock_order = MagicMock(spec=Order)
        mock_order.id = order_id
        mock_order.symbol = "AAPL"
        mock_order.qty = 100
        mock_client.return_value.get_order_by_id.return_value = mock_order

        self.service.client = mock_client.return_value
        result = self.service.get_order_by_id(order_id)

        self.assertEqual(result, mock_order)
        self.assertEqual(result.id, order_id)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.qty, 100)
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
        mock_asset = MagicMock(spec=Asset)
        mock_asset.symbol = "AAPL"
        mock_asset.name = "Apple Inc."
        mock_asset.tradable = True
        mock_client.return_value.get_asset.return_value = mock_asset

        self.service.client = mock_client.return_value
        result = self.service.get_asset("AAPL")

        self.assertEqual(result, mock_asset)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.name, "Apple Inc.")
        self.assertTrue(result.tradable)
        mock_client.return_value.get_asset.assert_called_once_with("AAPL")

    @patch("src.core.alpaca_client.AlpacaClient")
    def test_get_bars(self, mock_client: MagicMock) -> None:
        """Test getting historical bars."""
        symbol = "AAPL"
        timeframe = TimeFrame.Day
        start = pd.Timestamp("2023-01-01")
        end = pd.Timestamp("2023-12-31")
        limit = 100

        mock_df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000000, 1100000],
            }
        )
        mock_client.return_value.get_bars.return_value = mock_df

        self.service.client = mock_client.return_value
        result = self.service.get_bars(
            symbol=symbol, timeframe=timeframe, start=start, end=end, limit=limit
        )

        pd.testing.assert_frame_equal(result, mock_df)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["close"].iloc[-1], 102.0)
        mock_client.return_value.get_bars.assert_called_once_with(
            symbol=symbol, timeframe=timeframe, start=start, end=end, limit=limit
        )


if __name__ == "__main__":
    unittest.main()
