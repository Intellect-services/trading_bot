"""Alpaca trading service built on top of the REST API."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import pandas as pd
import requests

from src.core.alpaca_types import OrderSide, OrderType, TimeInForce
from src.utils.config import Config

logger = logging.getLogger(__name__)

TRADING_BASE_URLS = {
    "paper": "https://paper-api.alpaca.markets",
    "live": "https://api.alpaca.markets",
}


class AlpacaService:
    """Lightweight wrapper around the Alpaca REST and data APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        trading_mode: str = "paper",
        config: Config | None = None,
        timeout: int = 30,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        if api_key and secret_key:
            self.api_key = api_key
            self.secret_key = secret_key
            self.trading_mode = trading_mode
        elif config and config.alpaca_api_key_id and config.alpaca_api_secret_key:
            self.api_key = config.alpaca_api_key_id
            self.secret_key = config.alpaca_api_secret_key
            self.trading_mode = config.trading_mode
        else:
            raise ValueError(
                "Alpaca credentials must be provided either directly or via Config object",
            )

        base_url = TRADING_BASE_URLS.get(self.trading_mode, TRADING_BASE_URLS["paper"])
        self.base_url = f"{base_url.rstrip('/')}/v2"
        self.data_url = "https://data.alpaca.markets/v2"
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        try:
            self._request("GET", "/account")
            self.logger.info("Connected to Alpaca trading API (%s)", self.trading_mode)
        except Exception as exc:
            self.logger.error("Unable to verify Alpaca credentials: %s", exc)
            raise

    @classmethod
    def from_user_credentials(cls, user_id: int) -> "AlpacaService":
        """Create AlpacaService instance from user's stored credentials.

        Args:
            user_id: User ID to load credentials for.

        Returns:
            AlpacaService instance.

        Raises:
            ValueError: If user has no credentials configured.
        """
        from src.models.user_credentials import UserCredentials

        credentials = UserCredentials.get_by_user_id(user_id)
        if not credentials or not credentials.has_credentials():
            raise ValueError(f"User {user_id} has no Alpaca credentials configured")

        api_key = credentials.get_api_key()
        secret_key = credentials.get_secret_key()
        trading_mode = credentials.trading_mode

        return cls(api_key=api_key, secret_key=secret_key, trading_mode=trading_mode)

    def get_account(self) -> dict[str, Any]:
        """Get the trading account information."""
        account = self._request("GET", "/account")
        return {
            "id": account.get("id"),
            "status": account.get("status"),
            "currency": account.get("currency"),
            "cash": float(account.get("cash", 0.0)),
            "portfolio_value": float(account.get("portfolio_value", 0.0)),
            "buying_power": float(account.get("buying_power", 0.0)),
            "initial_margin": float(account.get("initial_margin", 0.0)),
            "maintenance_margin": float(account.get("maintenance_margin", 0.0)),
            "daytrading_buying_power": float(account.get("daytrading_buying_power", 0.0)),
            "equity": float(account.get("equity", 0.0)),
            "last_equity": float(account.get("last_equity", 0.0)),
            "multiplier": float(account.get("multiplier", 0.0)),
            "shorting_enabled": account.get("shorting_enabled", False),
            "pattern_day_trader": account.get("pattern_day_trader", False),
            "trading_blocked": account.get("trading_blocked", False),
            "transfers_blocked": account.get("transfers_blocked", False),
            "account_blocked": account.get("account_blocked", False),
            "created_at": account.get("created_at"),
            "trade_suspended_by_user": account.get("trade_suspended_by_user", False),
        }

    def get_positions(self) -> list[dict]:
        """Get current positions."""
        positions = self._request("GET", "/positions")
        return [
            {
                "symbol": pos.get("symbol"),
                "qty": float(pos.get("qty", 0.0)),
                "avg_entry_price": float(pos.get("avg_entry_price", 0.0)),
                "market_value": float(pos.get("market_value", 0.0)),
                "unrealized_pl": float(pos.get("unrealized_pl", 0.0)),
                "current_price": float(pos.get("current_price", 0.0)),
                "lastday_price": float(pos.get("lastday_price", 0.0)),
                "change_today": float(pos.get("change_today", 0.0)),
            }
            for pos in positions
        ]

    def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol."""
        trade = self._request("GET", f"/stocks/{symbol}/trades/latest", use_data_api=True)
        price = trade.get("trade", {}).get("p")
        if price is None:
            raise ValueError(f"No latest trade available for {symbol}")
        return float(price)

    def submit_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        type: str | OrderType = "market",
        time_in_force: str | TimeInForce = "day",
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> dict:
        """Submit a new order."""
        payload = {
            "symbol": symbol,
            "qty": int(qty),
            "side": side.value if isinstance(side, OrderSide) else side,
            "type": type.value if isinstance(type, OrderType) else type,
            "time_in_force": (
                time_in_force.value if isinstance(time_in_force, TimeInForce) else time_in_force
            ),
        }
        if limit_price is not None:
            payload["limit_price"] = float(limit_price)
        if stop_price is not None:
            payload["stop_price"] = float(stop_price)

        return cast("dict[str, Any]", self._request("POST", "/orders", body=payload))

    def submit_stop_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        *,
        stop_price: float,
        time_in_force: str | TimeInForce = "day",
    ) -> dict[str, Any]:
        """Submit a stop order."""

        if stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        return self.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="stop",
            time_in_force=time_in_force,
            stop_price=stop_price,
        )

    def submit_stop_limit_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        *,
        stop_price: float,
        limit_price: float,
        time_in_force: str | TimeInForce = "day",
    ) -> dict[str, Any]:
        """Submit a stop-limit order."""

        if stop_price is None or limit_price is None:
            raise ValueError("stop_price and limit_price are required for stop-limit orders")
        return self.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="stop_limit",
            time_in_force=time_in_force,
            stop_price=stop_price,
            limit_price=limit_price,
        )

    def submit_trailing_stop_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        *,
        trail_price: float | None = None,
        trail_percent: float | None = None,
        time_in_force: str | TimeInForce = "day",
    ) -> dict[str, Any]:
        """Submit a trailing stop order."""

        if trail_price is None and trail_percent is None:
            raise ValueError("Either trail_price or trail_percent must be provided")

        payload = {
            "symbol": symbol,
            "qty": int(qty),
            "side": side.value if isinstance(side, OrderSide) else side,
            "type": "trailing_stop",
            "time_in_force": (
                time_in_force.value if isinstance(time_in_force, TimeInForce) else time_in_force
            ),
        }
        if trail_price is not None:
            payload["trail_price"] = float(trail_price)
        if trail_percent is not None:
            payload["trail_percent"] = float(trail_percent)

        return cast("dict[str, Any]", self._request("POST", "/orders", body=payload))

    def submit_bracket_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        *,
        order_type: str | OrderType = "market",
        time_in_force: str | TimeInForce = "day",
        limit_price: float | None = None,
        take_profit_limit_price: float,
        stop_loss_stop_price: float,
        stop_loss_limit_price: float | None = None,
    ) -> dict[str, Any]:
        """Submit a bracket order (entry + TP + SL)."""

        if take_profit_limit_price is None or stop_loss_stop_price is None:
            raise ValueError(
                "Bracket orders require both take_profit_limit_price and stop_loss_stop_price"
            )

        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": int(qty),
            "side": side.value if isinstance(side, OrderSide) else side,
            "type": order_type.value if isinstance(order_type, OrderType) else order_type,
            "time_in_force": (
                time_in_force.value if isinstance(time_in_force, TimeInForce) else time_in_force
            ),
            "order_class": "bracket",
            "take_profit": {"limit_price": float(take_profit_limit_price)},
            "stop_loss": {"stop_price": float(stop_loss_stop_price)},
        }
        if limit_price is not None:
            payload["limit_price"] = float(limit_price)
        if stop_loss_limit_price is not None:
            payload["stop_loss"]["limit_price"] = float(stop_loss_limit_price)

        return cast("dict[str, Any]", self._request("POST", "/orders", body=payload))

    def submit_oco_order(
        self,
        symbol: str,
        qty: int | float,
        side: str | OrderSide,
        *,
        time_in_force: str | TimeInForce = "gtc",
        take_profit_limit_price: float,
        stop_loss_stop_price: float,
        order_type: str | OrderType = "limit",
        limit_price: float | None = None,
    ) -> dict[str, Any]:
        """Submit an OCO (one-cancels-other) order."""

        if take_profit_limit_price is None or stop_loss_stop_price is None:
            raise ValueError(
                "OCO orders require both take_profit_limit_price and stop_loss_stop_price"
            )

        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": int(qty),
            "side": side.value if isinstance(side, OrderSide) else side,
            "type": order_type.value if isinstance(order_type, OrderType) else order_type,
            "time_in_force": (
                time_in_force.value if isinstance(time_in_force, TimeInForce) else time_in_force
            ),
            "order_class": "oco",
            "take_profit": {"limit_price": float(take_profit_limit_price)},
            "stop_loss": {"stop_price": float(stop_loss_stop_price)},
        }
        if limit_price is not None:
            payload["limit_price"] = float(limit_price)

        return cast("dict[str, Any]", self._request("POST", "/orders", body=payload))

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        self._request("DELETE", f"/orders/{order_id}")
        return True

    def get_clock(self) -> dict[str, Any]:
        """Get the market clock."""
        clock = self._request("GET", "/clock")
        return {
            "timestamp": clock.get("timestamp"),
            "is_open": clock.get("is_open", False),
            "next_open": clock.get("next_open"),
            "next_close": clock.get("next_close"),
        }

    def get_orders(
        self,
        status: str | None = None,
        limit: int | None = None,
        after: str | None = None,
        until: str | None = None,
        direction: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get orders."""
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit
        if after:
            params["after"] = after
        if until:
            params["until"] = until
        if direction:
            params["direction"] = direction

        orders = self._request("GET", "/orders", params=params or None)
        return [
            {
                "id": order.get("id"),
                "client_order_id": order.get("client_order_id"),
                "created_at": order.get("created_at"),
                "updated_at": order.get("updated_at"),
                "submitted_at": order.get("submitted_at"),
                "filled_at": order.get("filled_at"),
                "expired_at": order.get("expired_at"),
                "canceled_at": order.get("canceled_at"),
                "failed_at": order.get("failed_at"),
                "asset_id": order.get("asset_id"),
                "symbol": order.get("symbol"),
                "asset_class": order.get("asset_class"),
                "qty": float(order.get("qty", 0.0)),
                "filled_qty": float(order.get("filled_qty", 0.0)),
                "type": order.get("type"),
                "side": order.get("side"),
                "time_in_force": order.get("time_in_force"),
                "limit_price": float(order.get("limit_price", 0.0))
                if order.get("limit_price") is not None
                else None,
                "stop_price": float(order.get("stop_price", 0.0))
                if order.get("stop_price") is not None
                else None,
                "status": order.get("status"),
            }
            for order in orders
        ]

    def get_account_activities(
        self,
        activity_type: str | None = None,
        *,
        date: str | None = None,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch account activities such as fills and transfers."""

        params: dict[str, Any] = {}
        if activity_type:
            params["activity_types"] = activity_type
        if date:
            params["date"] = date
        if page_size:
            params["page_size"] = page_size

        activities = self._request(
            "GET",
            "/account/activities",
            params=params,
        )
        return cast("list[dict[str, Any]]", activities or [])

    def get_portfolio_history(
        self,
        *,
        period: str = "1M",
        timeframe: str = "1D",
        date_end: str | None = None,
        extended_hours: bool = False,
    ) -> list[dict[str, Any]]:
        """Return account equity history derived from the trading API."""

        # Convert common timeframe formats to Alpaca API format
        timeframe_map = {
            "1Day": "1D",
            "1day": "1D",
            "1D": "1D",
            "1Min": "1Min",
            "5Min": "5Min",
            "15Min": "15Min",
            "1H": "1H",
            "1Hour": "1H",
        }
        alpaca_timeframe = timeframe_map.get(timeframe, timeframe)

        params: dict[str, Any] = {
            "period": period,
            "timeframe": alpaca_timeframe,
            "extended_hours": str(extended_hours).lower(),
        }
        if date_end:
            params["date_end"] = date_end

        history = self._request(
            "GET",
            "/account/portfolio/history",
            params=params,
        )
        if not history:
            logger.debug(
                f"Portfolio history API returned empty response for period={period}, timeframe={timeframe}"
            )
            return []

        equity = history.get("equity", [])
        timestamps = history.get("timestamp", [])
        profit_loss = history.get("profit_loss", [])
        profit_loss_pct = history.get("profit_loss_pct", [])

        # Log if we got empty arrays
        if not timestamps or not equity:
            logger.debug(
                f"Portfolio history API returned empty arrays: equity={len(equity) if equity else 0}, timestamps={len(timestamps) if timestamps else 0}"
            )
            return []

        points: list[dict[str, Any]] = []
        for idx, timestamp in enumerate(timestamps):
            points.append(
                {
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                    "equity": float(equity[idx]) if idx < len(equity) else 0.0,
                    "profit_loss": float(profit_loss[idx]) if idx < len(profit_loss) else 0.0,
                    "profit_loss_pct": float(profit_loss_pct[idx] or 0.0)
                    if idx < len(profit_loss_pct)
                    else 0.0,
                }
            )
        return points

    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1D",
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
    ) -> pd.DataFrame | None:
        """Get historical price data for a symbol."""
        try:
            # Ensure dates are not in the future and properly formatted
            now = datetime.now()
            if end is None or end > now:
                end = now.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of current day
            if start is None:
                start = end - timedelta(days=30)

            # Ensure start date is not before 2015 (Alpaca's data limit)
            min_date = datetime(2015, 1, 1)
            if start < min_date:
                start = min_date

            # Format dates for API request
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")

            self.logger.debug(
                f"Fetching historical bars for {symbol} from {start_str} to {end_str}"
            )

            timeframe_map = {
                "1m": "1Min",
                "5m": "5Min",
                "15m": "15Min",
                "30m": "30Min",
                "1h": "1Hour",
                "1D": "1Day",
                "1W": "1Week",
                "1M": "1Month",
            }
            alpaca_timeframe = timeframe_map.get(timeframe, "1Day")

            params = {
                "timeframe": alpaca_timeframe,
                "start": start_str,
                "end": end_str,
                "limit": limit,
            }
            response = self._request(
                "GET",
                f"/stocks/{symbol}/bars",
                params=params,
                use_data_api=True,
            )
            bars = response.get("bars", [])
            if not bars:
                return None

            bars_df = pd.DataFrame(bars)
            bars_df.rename(
                columns={
                    "t": "timestamp",
                    "o": "open",
                    "h": "high",
                    "l": "low",
                    "c": "close",
                    "v": "volume",
                },
                inplace=True,
            )
            bars_df["timestamp"] = pd.to_datetime(bars_df["timestamp"], errors="coerce")
            bars_df.set_index("timestamp", inplace=True)
            return bars_df

        except Exception as e:
            self.logger.error("Error getting historical bars for %s: %s", symbol, e)
            return None

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list[dict[str, float | str]]]:
        """Get historical bars in the format expected by data_feed.py.

        This is a compatibility method for the old AlpacaClient interface.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (e.g., '1Min', '5Min', '1Day')
            start: Start datetime
            end: End datetime (optional)
            limit: Maximum number of bars (optional)

        Returns:
            Dictionary with symbol as key and list of bar dictionaries as value
        """
        try:
            timeframe_map = {
                "1Min": "1Min",
                "5Min": "5Min",
                "15Min": "15Min",
                "30Min": "30Min",
                "1Hour": "1Hour",
                "1H": "1Hour",
                "1D": "1Day",
                "1Day": "1Day",
                "1W": "1Week",
                "1Week": "1Week",
                "1M": "1Month",
                "1Month": "1Month",
            }
            alpaca_timeframe = timeframe_map.get(timeframe, "1Day")
            if timeframe not in timeframe_map:
                self.logger.warning(f"Unknown timeframe '{timeframe}', using '1Day' as default")
            elif timeframe != alpaca_timeframe:
                self.logger.debug(f"Mapped timeframe '{timeframe}' to '{alpaca_timeframe}'")

            if end is None:
                end = datetime.now(timezone.utc)
            start_str = start.astimezone(timezone.utc).isoformat()
            end_str = end.astimezone(timezone.utc).isoformat()

            params = {
                "timeframe": alpaca_timeframe,
                "start": start_str,
                "end": end_str,
                "limit": limit or 100,
            }

            # Try data API first
            response = None
            data_api_error = None
            try:
                response = self._request(
                    "GET",
                    f"/stocks/{symbol}/bars",
                    params=params,
                    use_data_api=True,
                )
            except Exception as e:
                data_api_error = e
                self.logger.warning(
                    f"Data API failed for {symbol}: {e}. "
                    "This may indicate that data API access is not available for your account."
                )

            # Check if response has error message
            if response and isinstance(response, dict) and "message" in response:
                error_msg = response.get("message", "")
                self.logger.error(f"API returned error message for {symbol}: {error_msg}")
                if "subscription" in error_msg.lower() or "access" in error_msg.lower():
                    self.logger.error(
                        f"Data API subscription may be required for {symbol}. "
                        "Paper trading accounts may have limited data API access."
                    )
                return {symbol: []}

            if not response:
                if data_api_error:
                    # If we got an error, don't try fallback - the issue is likely account-related
                    self.logger.error(
                        f"Cannot fetch data for {symbol}. "
                        "Please check if your Alpaca account has data API access enabled."
                    )
                else:
                    self.logger.warning(f"Empty response from Alpaca API for {symbol}")
                return {symbol: []}

            # Handle different response formats
            bars = response.get("bars", [])
            if not bars and isinstance(response, list):
                # Some endpoints return a list directly
                bars = response

            if not bars:
                # Log the full response for debugging
                self.logger.warning(
                    f"No bars returned for {symbol} (timeframe: {alpaca_timeframe}, "
                    f"start: {start_str}, end: {end_str}). "
                    f"Response structure: {list(response.keys()) if isinstance(response, dict) else type(response)}"
                )
                return {symbol: []}

            self.logger.info(f"Retrieved {len(bars)} bars for {symbol}")
            return {
                symbol: [
                    {
                        "open": float(bar.get("o", 0.0)),
                        "high": float(bar.get("h", 0.0)),
                        "low": float(bar.get("l", 0.0)),
                        "close": float(bar.get("c", 0.0)),
                        "volume": float(bar.get("v", 0.0)),
                        "timestamp": bar.get("t"),
                    }
                    for bar in bars
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting bars for {symbol}: {e}", exc_info=True)
            return {symbol: []}

    def get_all_positions(self) -> list[dict[str, Any]]:
        """Get all positions in the format expected by data_feed.py.

        This is a compatibility method for the old AlpacaClient interface.

        Returns:
            List of position dictionaries
        """
        return self.get_positions()

    def get_open_position(self, symbol: str) -> dict[str, Any] | None:
        """Get open position for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Position dictionary or None if not found
        """
        try:
            positions = self.get_positions()
            for pos in positions:
                if pos.get("symbol") == symbol:
                    return pos
            return None
        except Exception as e:
            self.logger.error(f"Error getting open position for {symbol}: {e!s}")
            return None

    def get_asset(self, symbol: str) -> dict[str, Any]:
        """Get asset information.

        Args:
            symbol: Stock symbol

        Returns:
            Asset information dictionary
        """
        asset = self._request("GET", f"/assets/{symbol}")
        return {
            "symbol": asset.get("symbol"),
            "name": asset.get("name"),
            "exchange": asset.get("exchange"),
            "class": asset.get("class"),
            "status": asset.get("status"),
            "tradable": asset.get("tradable", False),
            "marginable": asset.get("marginable", False),
            "shortable": asset.get("shortable", False),
            "easy_to_borrow": asset.get("easy_to_borrow", False),
            "fractionable": asset.get("fractionable", False),
        }

    def get_market_clock(self) -> dict[str, Any]:
        """Get market clock information.

        Returns:
            Market clock dictionary
        """
        return self.get_clock()

    def test_credentials(self) -> bool:
        """Test if the Alpaca credentials are valid.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self._request("GET", "/account")
            return True
        except Exception as exc:
            self.logger.error("Error testing credentials: %s", exc)
            return False

    def cancel_order_by_id(self, order_id: str) -> bool:
        """Compatibility wrapper for bot_service."""
        return self.cancel_order(order_id)

    def get_order_by_id(self, order_id: str) -> dict[str, Any]:
        """Fetch a single order."""
        return cast("dict[str, Any]", self._request("GET", f"/orders/{order_id}"))

    def get_order(self, order_id: str) -> dict[str, Any]:
        """Alias for compatibility with older code paths."""
        return self.get_order_by_id(order_id)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        use_data_api: bool = False,
    ) -> Any:
        """Perform an HTTP request against the Alpaca APIs."""
        base = self.data_url if use_data_api else self.base_url
        url = f"{base}{path}"

        self.logger.debug(f"Making {method} request to {url} with params: {params}")

        response = self.session.request(
            method,
            url,
            params=params,
            json=body,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            error_text = response.text
            self.logger.error(
                "Alpaca API error [%s] %s: %s",
                response.status_code,
                url,
                error_text,
            )
            # Try to parse error message from response
            try:
                error_json = response.json()
                error_message = error_json.get("message", error_text)
                self.logger.error(f"API error message: {error_message}")
            except ValueError:
                pass
            response.raise_for_status()

        if not response.content:
            self.logger.debug(f"Empty response from {url}")
            return {}

        try:
            result = response.json()
            self.logger.debug(
                f"Response from {url}: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}"
            )
            return result
        except ValueError as e:
            self.logger.warning(f"Failed to parse JSON response from {url}: {e}")
            return {}
