"""Tests for AlpacaService."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import OrderSide, OrderType, TimeFrame, TimeInForce
from src.utils.config import Config


class TestAlpacaService(unittest.TestCase):
    """Test cases for AlpacaService."""

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

    def test_get_account(self):
        """Test getting account information."""
        mock_account = MagicMock()
        mock_account.account_number = "123456"
        mock_account.buying_power = "100000.0"
        mock_account.cash = "50000.0"
        mock_account.equity = "150000.0"
        mock_account.initial_margin = "10000.0"
        mock_account.maintenance_margin = "5000.0"
        mock_account.pattern_day_trader = False
        mock_account.portfolio_value = "150000.0"
        mock_account.status = "ACTIVE"
        mock_account.trade_suspended_by_user = False
        mock_account.trading_blocked = False
        mock_account.transfers_blocked = False

        with patch.object(self.service.api, "get_account", return_value=mock_account):
            account = self.service.get_account()
            self.assertEqual(account["account_number"], "123456")
            self.assertEqual(account["buying_power"], 100000.0)
            self.assertEqual(account["cash"], 50000.0)
            self.assertEqual(account["equity"], 150000.0)

    def test_get_positions(self):
        """Test getting positions."""
        mock_position = MagicMock()
        mock_position.asset_id = "123"
        mock_position.symbol = "SPY"
        mock_position.exchange = "NYSE"
        mock_position.asset_class = "us_equity"
        mock_position.avg_entry_price = "100.0"
        mock_position.qty = "10"
        mock_position.side = "long"
        mock_position.market_value = "1000.0"
        mock_position.cost_basis = "1000.0"
        mock_position.unrealized_pl = "0.0"
        mock_position.unrealized_plpc = "0.0"
        mock_position.current_price = "100.0"
        mock_position.lastday_price = "100.0"
        mock_position.change_today = "0.0"

        with patch.object(self.service.api, "list_positions", return_value=[mock_position]):
            positions = self.service.get_positions()
            self.assertEqual(len(positions), 1)
            self.assertEqual(positions[0]["symbol"], "SPY")
            self.assertEqual(positions[0]["qty"], 10.0)

    def test_get_position(self):
        """Test getting a specific position."""
        mock_position = MagicMock()
        mock_position.asset_id = "123"
        mock_position.symbol = "SPY"
        mock_position.exchange = "NYSE"
        mock_position.asset_class = "us_equity"
        mock_position.avg_entry_price = "100.0"
        mock_position.qty = "10"
        mock_position.side = "long"
        mock_position.market_value = "1000.0"
        mock_position.cost_basis = "1000.0"
        mock_position.unrealized_pl = "0.0"
        mock_position.unrealized_plpc = "0.0"
        mock_position.current_price = "100.0"
        mock_position.lastday_price = "100.0"
        mock_position.change_today = "0.0"

        with patch.object(self.service.api, "get_position", return_value=mock_position):
            position = self.service.get_position("SPY")
            self.assertIsNotNone(position)
            self.assertEqual(position["symbol"], "SPY")
            self.assertEqual(position["qty"], 10.0)

    def test_submit_order(self):
        """Test submitting an order."""
        mock_order = MagicMock()
        mock_order.id = "123"
        mock_order.client_order_id = "test"
        mock_order.created_at = datetime.now()
        mock_order.updated_at = None
        mock_order.submitted_at = None
        mock_order.filled_at = None
        mock_order.expired_at = None
        mock_order.canceled_at = None
        mock_order.failed_at = None
        mock_order.replaced_at = None
        mock_order.replaced_by = None
        mock_order.replaces = None
        mock_order.asset_id = "123"
        mock_order.symbol = "SPY"
        mock_order.asset_class = "us_equity"
        mock_order.qty = "10"
        mock_order.filled_qty = "0"
        mock_order.type = "market"
        mock_order.side = "buy"
        mock_order.time_in_force = "day"
        mock_order.limit_price = None
        mock_order.stop_price = None
        mock_order.filled_avg_price = None
        mock_order.status = "new"
        mock_order.extended_hours = False
        mock_order.legs = None

        with patch.object(self.service.api, "submit_order", return_value=mock_order):
            order_data = {
                "symbol": "SPY",
                "qty": "10",
                "side": OrderSide.BUY,
                "type": OrderType.MARKET,
                "time_in_force": TimeInForce.DAY,
            }
            order = self.service.submit_order(order_data)
            self.assertEqual(order["symbol"], "SPY")
            self.assertEqual(order["qty"], 10.0)

    def test_get_bars(self):
        """Test getting historical bars."""
        mock_bar = MagicMock()
        mock_bar.timestamp = datetime.now()
        mock_bar.open = "100.0"
        mock_bar.high = "101.0"
        mock_bar.low = "99.0"
        mock_bar.close = "100.5"
        mock_bar.volume = "1000"
        mock_bar.trade_count = "100"
        mock_bar.vwap = "100.25"

        with patch.object(self.service.api, "get_bars", return_value=[mock_bar]):
            bars = self.service.get_bars(
                symbols=["SPY"],
                timeframe=TimeFrame(amount=1, unit="m"),
                start=datetime.now() - timedelta(days=1),
                end=datetime.now(),
            )
            self.assertIsNotNone(bars)
            self.assertEqual(len(bars["bars"]), 1)
            self.assertEqual(bars["bars"][0]["close"], 100.5)


if __name__ == "__main__":
    unittest.main()
