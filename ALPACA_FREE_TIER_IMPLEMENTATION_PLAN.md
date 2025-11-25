# Alpaca Free Tier Implementation Plan

## Executive Summary

This plan focuses on implementing **all available free features** from Alpaca API for paper trading accounts, with workarounds for data API limitations and alternative approaches where needed.

---

## Part 1: Alpaca Free Tier Analysis

### 1.1 What's Available in Free Tier (Paper Trading)

#### ✅ **Fully Available (No Subscription Required)**

**Trading API (REST) - 100% Free:**
- ✅ Account management (`GET /account`)
- ✅ Positions (`GET /positions`, `GET /positions/{symbol}`)
- ✅ Orders (`POST /orders`, `GET /orders`, `DELETE /orders/{id}`)
- ✅ Order types: Market, Limit, Stop, Stop-Limit, Trailing Stop
- ✅ Time-in-Force: GTC, IOC, FOK, DAY, EXT, CLS
- ✅ Market clock (`GET /clock`)
- ✅ Assets (`GET /assets/{symbol}`)
- ✅ Account activities (`GET /account/activities`)
- ✅ Portfolio history (`GET /account/portfolio/history`)
- ✅ Watchlists (`GET /watchlists`, `POST /watchlists`)

**WebSocket Streaming - Free for Paper Trading:**
- ✅ Market data stream (quotes, trades, bars)
- ✅ Account updates stream
- ✅ Trade updates stream

**Data API - Limited Free Access:**
- ⚠️ Historical bars - **May require subscription** (this is our current issue)
- ⚠️ Latest trades - Available
- ⚠️ Latest quotes - May require subscription
- ⚠️ Snapshots - May require subscription

### 1.2 Current Issues & Solutions

#### **Issue: Data API Historical Bars Not Working**
**Root Cause:** Free tier may not have access to historical data API, or requires different authentication.

**Solutions:**
1. **Use Trading API Portfolio History** - Get historical account values
2. **Use WebSocket for Real-Time Data** - Build historical data from real-time stream
3. **Use Alternative Data Sources** - Yahoo Finance, Alpha Vantage (free tiers)
4. **Cache Real-Time Data** - Store bars as they come in via WebSocket
5. **Use Account Activities** - Reconstruct positions from order history

---

## Part 2: Revised Implementation Plan (Free Tier Focus)

### Phase 1: Fix Data Access & Implement WebSocket (Week 1)

#### 1.1 Fix Historical Data Access
**Priority: CRITICAL**

**Option A: Use Trading API Portfolio History**
```python
# New method in AlpacaService
def get_portfolio_history(self, period: str = "1M") -> pd.DataFrame:
    """Get portfolio history from trading API (free)."""
    # GET /account/portfolio/history
    # Returns: equity, profit_loss, profit_loss_pct, base_value, timeframe
    # This is FREE and available for paper trading
```

**Option B: Implement Data Caching from WebSocket**
```python
# Store real-time bars as they come in
# Build historical dataset over time
# Use for backtesting once we have enough data
```

**Option C: Use Alternative Free Data Source**
```python
# New file: src/core/data_providers.py
class YahooFinanceProvider:
    - Free historical data
    - No API key required
    - Good for backtesting

class AlphaVantageProvider:
    - Free tier: 5 API calls/minute
    - 500 calls/day
    - Good for limited real-time data
```

#### 1.2 Implement WebSocket Streaming
**Priority: HIGH**

```python
# New file: src/core/alpaca_websocket.py
class AlpacaWebSocket:
    """WebSocket client for real-time Alpaca data (FREE for paper trading)."""

    def __init__(self, api_key, secret_key, trading_mode="paper"):
        # Use wss://stream.data.alpaca.markets/v2/iex for paper
        # Authentication via API keys

    def connect(self):
        """Establish WebSocket connection."""

    def subscribe_quotes(self, symbols: list[str]):
        """Subscribe to real-time quotes (bid/ask)."""
        # FREE for paper trading

    def subscribe_trades(self, symbols: list[str]):
        """Subscribe to real-time trades."""
        # FREE for paper trading

    def subscribe_bars(self, symbols: list[str], timeframe: str):
        """Subscribe to real-time bars (1Min, 5Min, 1Hour, 1Day)."""
        # FREE for paper trading
        # This is KEY - we can build historical data from real-time bars!

    def subscribe_account_updates(self):
        """Subscribe to account/position/order updates."""
        # FREE for paper trading

    def on_quote(self, callback):
        """Handle quote updates."""

    def on_trade(self, callback):
        """Handle trade updates."""

    def on_bar(self, callback):
        """Handle bar updates - STORE THESE FOR HISTORICAL DATA!"""

    def on_order_update(self, callback):
        """Handle order execution updates."""
```

**Benefits:**
- ✅ Real-time data (no polling delay)
- ✅ Can build historical dataset from real-time bars
- ✅ FREE for paper trading
- ✅ Lower API rate limit usage
- ✅ Instant order execution notifications

#### 1.3 Implement Data Caching System
**Priority: HIGH**

```python
# New file: src/core/data_cache.py
class DataCache:
    """Cache market data from WebSocket for historical access."""

    def __init__(self, db_session):
        # Store bars in database or local cache

    def store_bar(self, symbol, timeframe, bar_data):
        """Store a bar from WebSocket."""
        # Save to database for historical access

    def get_historical_bars(self, symbol, timeframe, start, end):
        """Get historical bars from cache."""
        # Query cached data
        # Fallback to alternative source if not available

    def get_cached_data_availability(self, symbol):
        """Check what historical data we have cached."""
        # Return date range of available data
```

---

### Phase 2: Advanced Order Types (Week 1-2)

#### 2.1 Implement All Free Order Types
**Priority: HIGH**

```python
# Enhance: src/core/alpaca_service.py

def submit_stop_order(
    self,
    symbol: str,
    qty: int,
    side: str,
    stop_price: float,
    limit_price: float | None = None,
) -> dict[str, Any]:
    """Submit stop or stop-limit order (FREE)."""
    # POST /orders with type="stop" or "stop_limit"
    # FREE for paper trading

def submit_trailing_stop_order(
    self,
    symbol: str,
    qty: int,
    side: str,
    trail_price: float | None = None,
    trail_percent: float | None = None,
) -> dict[str, Any]:
    """Submit trailing stop order (FREE)."""
    # POST /orders with type="trailing_stop"
    # FREE for paper trading

def submit_bracket_order(
    self,
    symbol: str,
    qty: int,
    side: str,
    take_profit_limit_price: float,
    stop_loss_stop_price: float,
) -> dict[str, Any]:
    """Submit bracket order (OCO with take-profit and stop-loss) (FREE)."""
    # POST /orders with bracket order structure
    # FREE for paper trading

def submit_oco_order(
    self,
    symbol: str,
    qty: int,
    side: str,
    take_profit_price: float,
    stop_loss_price: float,
) -> dict[str, Any]:
    """Submit One-Cancels-Other order (FREE)."""
    # POST /orders with OCO structure
    # FREE for paper trading
```

**All these are FREE for paper trading!**

---

### Phase 3: Portfolio Analytics Using Free Endpoints (Week 2)

#### 3.1 Portfolio History API
**Priority: HIGH**

```python
# New method in AlpacaService
def get_portfolio_history(
    self,
    period: str = "1M",
    timeframe: str = "1Day",
    end_date: str | None = None,
) -> pd.DataFrame:
    """Get portfolio history (FREE endpoint)."""
    # GET /account/portfolio/history
    # Returns: equity, profit_loss, profit_loss_pct over time
    # This is FREE and perfect for performance charts!

    params = {
        "period": period,  # 1D, 1W, 1M, 3M, 1Y, all
        "timeframe": timeframe,  # 1Min, 5Min, 15Min, 1H, 1D
        "end_date": end_date,
    }
    # This replaces our current portfolio performance calculation!
```

#### 3.2 Account Activities
**Priority: MEDIUM**

```python
# New method in AlpacaService
def get_account_activities(
    self,
    activity_type: str | None = None,
    date: str | None = None,
    until: str | None = None,
    after: str | None = None,
    direction: str | None = None,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Get account activities (FREE endpoint)."""
    # GET /account/activities
    # Returns: fills, orders, deposits, withdrawals, etc.
    # FREE - can reconstruct trading history
```

#### 3.3 Performance Metrics from Free Data
**Priority: HIGH**

```python
# New file: src/core/portfolio_analytics.py
class PortfolioAnalytics:
    """Calculate performance metrics from free Alpaca endpoints."""

    def __init__(self, alpaca_service: AlpacaService):
        self.alpaca_service = alpaca_service

    def calculate_sharpe_ratio(self, portfolio_history: pd.DataFrame) -> float:
        """Calculate Sharpe ratio from portfolio history."""
        # Use portfolio_history from FREE endpoint

    def calculate_max_drawdown(self, portfolio_history: pd.DataFrame) -> float:
        """Calculate maximum drawdown."""
        # Use equity values from portfolio history

    def calculate_win_rate(self, activities: list[dict]) -> float:
        """Calculate win rate from account activities."""
        # Analyze fills from FREE activities endpoint

    def generate_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report using FREE endpoints."""
        portfolio_history = self.alpaca_service.get_portfolio_history()
        activities = self.alpaca_service.get_account_activities()
        # Calculate all metrics from free data
```

---

### Phase 4: Technical Indicators Library (Week 2-3)

#### 4.1 Core Indicators (No External Data Required)
**Priority: HIGH**

All indicators can be calculated from:
- Real-time bars from WebSocket (FREE)
- Cached historical bars
- Portfolio history (FREE endpoint)

```python
# New directory: src/indicators/
# All indicators work with any OHLCV data source

src/indicators/
├── __init__.py
├── trend.py          # SMA, EMA, MACD, ADX, Parabolic SAR
├── momentum.py       # RSI, Stochastic, Williams %R, CCI
├── volatility.py     # Bollinger Bands, ATR, Keltner Channels
└── volume.py         # OBV, VWAP, A/D, CMF, MFI
```

**Implementation Note:** All indicators are calculated from price/volume data, which we can get from:
1. WebSocket real-time bars (FREE)
2. Cached bars (built over time)
3. Portfolio history (FREE endpoint for account equity)

---

### Phase 5: Trading Strategies (Week 3-4)

#### 5.1 Strategy Implementation Priority

**High Priority (Work with Real-Time Data):**

1. **RSI Strategy** - Uses latest bars (from WebSocket)
2. **MACD Strategy** - Uses latest bars (from WebSocket)
3. **Moving Average Crossover** - Enhanced with real-time data
4. **Bollinger Bands** - Uses latest bars (from WebSocket)

**Medium Priority:**

5. **Breakout Strategy** - Needs some historical data (use cached)
6. **Momentum Strategy** - Uses latest bars

**Low Priority (Needs More Historical Data):**

7. **Pairs Trading** - Needs correlation analysis (use alternative data source)

---

### Phase 6: Enhanced Risk Management (Week 4)

#### 6.1 All Risk Features Work with Free Tier
**Priority: HIGH**

All risk management features work with free endpoints:
- Position sizing - Uses account equity (FREE)
- Stop-loss orders - FREE order type
- Trailing stops - FREE order type
- Portfolio limits - Uses positions (FREE)
- Drawdown protection - Uses portfolio history (FREE)

---

## Part 3: Data Access Strategy

### 3.1 Multi-Source Data Approach

```python
# New file: src/core/data_provider.py
class DataProvider:
    """Unified interface for multiple data sources."""

    def __init__(self):
        self.alpaca_service = None
        self.websocket = None
        self.cache = DataCache()
        self.fallback_providers = []

    def get_historical_bars(self, symbol, timeframe, start, end):
        """Get historical bars with fallback chain."""
        # 1. Try cached data (from WebSocket)
        # 2. Try Alpaca data API (if available)
        # 3. Try Yahoo Finance (free, no API key)
        # 4. Try Alpha Vantage (free tier)
        # 5. Return error if all fail

    def get_latest_price(self, symbol):
        """Get latest price with fallback."""
        # 1. Try WebSocket (real-time, FREE)
        # 2. Try Alpaca latest trade (FREE)
        # 3. Try fallback provider
```

### 3.2 Yahoo Finance Integration (Free, No API Key)

```python
# New file: src/core/data_providers/yahoo_finance.py
class YahooFinanceProvider:
    """Free historical data provider (no API key required)."""

    def get_historical_data(self, symbol, start, end):
        """Get historical data from Yahoo Finance."""
        # Use yfinance library (free, no API key)
        # Good for backtesting
        # Rate limits: None (but be respectful)
```

### 3.3 Alpha Vantage Integration (Free Tier)

```python
# New file: src/core/data_providers/alpha_vantage.py
class AlphaVantageProvider:
    """Free tier data provider (5 calls/min, 500/day)."""

    def __init__(self, api_key: str | None = None):
        # Free API key from alpha-vantage.com
        # 5 API calls per minute
        # 500 calls per day

    def get_intraday_data(self, symbol, interval="5min"):
        """Get intraday data (limited by free tier)."""
        # Use for real-time data when WebSocket unavailable
```

---

## Part 4: Implementation Roadmap (Revised)

### Week 1: Data Access & WebSocket
- ✅ Fix historical data access (use portfolio history + WebSocket caching)
- ✅ Implement WebSocket streaming
- ✅ Implement data caching system
- ✅ Add Yahoo Finance fallback

### Week 2: Advanced Orders & Analytics
- ✅ Implement all advanced order types (all FREE)
- ✅ Implement portfolio analytics using free endpoints
- ✅ Enhance risk management with free data

### Week 3: Technical Indicators
- ✅ Build indicators library
- ✅ Test with real-time WebSocket data
- ✅ Test with cached historical data

### Week 4: Trading Strategies
- ✅ RSI Strategy
- ✅ MACD Strategy
- ✅ Enhanced Moving Average
- ✅ Bollinger Bands Strategy

### Week 5: Integration & Testing
- ✅ Integrate WebSocket with bot
- ✅ Test all strategies with real-time data
- ✅ Performance testing
- ✅ Paper trading validation

---

## Part 5: Free Tier Feature Checklist

### ✅ Trading API (100% Free)
- [x] Account management
- [x] Positions
- [x] Orders (all types)
- [x] Market clock
- [x] Assets
- [ ] Portfolio history ← **IMPLEMENT THIS**
- [ ] Account activities ← **IMPLEMENT THIS**
- [ ] Watchlists ← **IMPLEMENT THIS**

### ✅ WebSocket Streaming (100% Free for Paper)
- [ ] Market data stream ← **IMPLEMENT THIS**
- [ ] Account updates stream ← **IMPLEMENT THIS**
- [ ] Trade updates stream ← **IMPLEMENT THIS**

### ⚠️ Data API (Limited/May Require Subscription)
- [x] Latest trades (working)
- [ ] Historical bars (may need subscription) ← **USE ALTERNATIVES**
- [ ] Latest quotes (may need subscription) ← **USE WEBSOCKET**
- [ ] Snapshots (may need subscription) ← **USE WEBSOCKET**

### ✅ Order Types (100% Free)
- [x] Market orders
- [x] Limit orders
- [ ] Stop orders ← **IMPLEMENT THIS**
- [ ] Stop-limit orders ← **IMPLEMENT THIS**
- [ ] Trailing stop orders ← **IMPLEMENT THIS**
- [ ] Bracket orders ← **IMPLEMENT THIS**

---

## Part 6: Key Implementation Details

### 6.1 WebSocket Endpoints (Free for Paper Trading)

```python
# Paper Trading WebSocket URLs (FREE):
MARKET_DATA_STREAM = "wss://stream.data.alpaca.markets/v2/iex"
ACCOUNT_UPDATES_STREAM = "wss://paper-api.alpaca.markets/stream"

# Authentication: API Key + Secret Key (same as REST API)
# No subscription required for paper trading!
```

### 6.2 Portfolio History Endpoint (FREE)

```python
# GET /account/portfolio/history
# Returns historical equity, profit/loss, profit/loss %
# Perfect for performance charts!
# FREE for paper trading
# Timeframes: 1Min, 5Min, 15Min, 1H, 1D
# Periods: 1D, 1W, 1M, 3M, 1Y, all
```

### 6.3 Data Caching Strategy

```python
# Store WebSocket bars in database
# Build historical dataset over time
# Use for:
# - Backtesting (once we have enough data)
# - Strategy analysis
# - Performance metrics

# Database schema:
# bars_cache:
#   - symbol
#   - timeframe
#   - timestamp
#   - open, high, low, close, volume
#   - source (websocket, api, yahoo, etc.)
```

---

## Part 7: Alternative Data Sources (Free)

### 7.1 Yahoo Finance (yfinance)
- ✅ **Completely Free**
- ✅ **No API Key Required**
- ✅ Historical data (years of data)
- ✅ Real-time quotes
- ✅ Company information
- ⚠️ Rate limits: None (but be respectful)
- ✅ Perfect for backtesting

### 7.2 Alpha Vantage
- ✅ **Free Tier Available**
- ✅ **Free API Key** (sign up at alpha-vantage.com)
- ✅ Historical data
- ✅ Real-time quotes
- ⚠️ Rate limits: 5 calls/minute, 500/day
- ✅ Good for limited real-time data

### 7.3 Polygon.io (Free Tier)
- ✅ **Free Tier Available**
- ✅ Historical data (limited)
- ⚠️ Rate limits: 5 calls/minute
- ✅ Good backup option

---

## Part 8: Revised Success Metrics

### 8.1 Data Access Metrics
- ✅ **WebSocket Uptime**: > 99%
- ✅ **Data Cache Hit Rate**: > 80% (after 30 days)
- ✅ **Historical Data Availability**: 100% via fallbacks
- ✅ **Real-Time Latency**: < 100ms

### 8.2 Feature Completeness
- ✅ **All Free Order Types**: 100% implemented
- ✅ **WebSocket Streaming**: 100% implemented
- ✅ **Portfolio Analytics**: 100% using free endpoints
- ✅ **Technical Indicators**: 100% implemented
- ✅ **Trading Strategies**: 4+ strategies implemented

---

## Part 9: Implementation Priority (Revised)

### 🔴 Critical (Week 1)
1. **Fix Historical Data Access**
   - Implement portfolio history endpoint
   - Implement WebSocket data caching
   - Add Yahoo Finance fallback

2. **WebSocket Integration**
   - Real-time market data stream
   - Account updates stream
   - Data caching from WebSocket

### 🟠 High Priority (Week 2)
3. **Advanced Order Types**
   - Stop orders
   - Trailing stops
   - Bracket orders

4. **Portfolio Analytics**
   - Use portfolio history endpoint
   - Calculate performance metrics
   - Generate reports

### 🟡 Medium Priority (Week 3-4)
5. **Technical Indicators Library**
6. **Trading Strategies** (RSI, MACD, Bollinger Bands)
7. **Enhanced Risk Management**

---

## Part 10: Code Structure (Revised)

```
src/
├── core/
│   ├── alpaca_service.py (Enhanced - add portfolio history, activities)
│   ├── alpaca_websocket.py (NEW - WebSocket streaming)
│   ├── data_cache.py (NEW - Cache WebSocket data)
│   ├── data_provider.py (NEW - Unified data interface)
│   └── bot.py (Enhanced - use WebSocket)
├── core/data_providers/
│   ├── __init__.py
│   ├── yahoo_finance.py (NEW - Free historical data)
│   └── alpha_vantage.py (NEW - Free tier backup)
├── indicators/ (Same as before)
├── strategies/ (Same as before)
└── backtesting/ (Enhanced - use cached data)
```

---

## Next Steps

1. **Review and approve revised plan**
2. **Start with Week 1: Data Access & WebSocket**
3. **Implement portfolio history endpoint first** (immediate fix for charts)
4. **Implement WebSocket streaming** (real-time data + historical building)
5. **Add Yahoo Finance fallback** (backtesting data)

---

## Key Takeaways

1. **WebSocket is FREE** for paper trading - use it for real-time data!
2. **Portfolio History API is FREE** - use it for performance charts!
3. **All Order Types are FREE** - implement stop, trailing, bracket orders!
4. **Data API may require subscription** - use WebSocket + caching + fallbacks!
5. **Yahoo Finance is completely free** - use for backtesting data!

This revised plan focuses on **100% free features** and provides workarounds for any limitations!
