"""Integration tests for Alpaca API."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import OrderSide, OrderType, TimeFrame, TimeInForce
from src.utils.config import Config


class TestAlpacaIntegration(unittest.TestCase):
    """Integration test cases for Alpaca API."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Config(
            ALPACA_API_KEY="test_key",
            ALPACA_SECRET_KEY="test_secret",
            ALPACA_PAPER=True,
            INITIAL_CAPITAL=100000.0,
            RISK_MAX_POSITION_SIZE=0.1,
            RISK_PER_TRADE=0.02,
            RISK_MAX_DRAWDOWN=0.1,
            RISK_MAX_LEVERAGE=1.0,
            STRATEGY_SYMBOLS=["SPY"],
            STRATEGY_TIMEFRAME="1Min",
            SHORT_WINDOW=20,
            LONG_WINDOW=50,
            LOOKBACK_DAYS=10,
        )
        self.service = AlpacaService(self.config)

    def test_account_integration(self):
        """Test account integration."""
        account = self.service.get_account()
        self.assertIsNotNone(account)
        self.assertIn("account_number", account)
        self.assertIn("buying_power", account)
        self.assertIn("cash", account)
        self.assertIn("equity", account)

    def test_positions_integration(self):
        """Test positions integration."""
        positions = self.service.get_positions()
        self.assertIsInstance(positions, list)
        for position in positions:
            self.assertIn("symbol", position)
            self.assertIn("qty", position)
            self.assertIn("side", position)

    def test_position_integration(self):
        """Test single position integration."""
        position = self.service.get_position("SPY")
        if position:
            self.assertIn("symbol", position)
            self.assertIn("qty", position)
            self.assertIn("side", position)

    def test_order_integration(self):
        """Test order integration."""
        order_data = {
            "symbol": "SPY",
            "qty": "1",
            "side": OrderSide.BUY,
            "type": OrderType.MARKET,
            "time_in_force": TimeInForce.DAY,
        }
        order = self.service.submit_order(order_data)
        self.assertIsNotNone(order)
        self.assertIn("id", order)
        self.assertIn("symbol", order)
        self.assertIn("qty", order)
        self.assertIn("side", order)

    def test_asset_integration(self):
        """Test asset integration."""
        asset = self.service.get_asset("SPY")
        if asset:
            self.assertIn("symbol", asset)
            self.assertIn("name", asset)
            self.assertIn("tradable", asset)

    def test_bars_integration(self):
        """Test bars integration."""
        bars = self.service.get_bars(
            symbols=["SPY"],
            timeframe=TimeFrame(amount=1, unit="m"),
            start=datetime.now() - timedelta(days=1),
            end=datetime.now(),
        )
        if bars:
            self.assertIn("bars", bars)
            self.assertGreater(len(bars["bars"]), 0)
            self.assertIn("close", bars["bars"][0])


if __name__ == "__main__":
    unittest.main()
