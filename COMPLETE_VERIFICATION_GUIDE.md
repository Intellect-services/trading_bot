# Complete Verification & Testing Guide

## Market Hours

**US Stock Market (Alpaca Paper Trading):**
- **Market Open:** Monday-Friday, 9:30 AM - 4:00 PM Eastern Time (ET)
- **Pre-Market:** 4:00 AM - 9:30 AM ET
- **After Hours:** 4:00 PM - 8:00 PM ET
- **Closed:** Weekends and US holidays

**Current Time Check:**
```python
from src.core.alpaca_service import AlpacaService
from src.utils.config import Config

config = Config()
alpaca = AlpacaService(
    api_key=config.alpaca_api_key_id,
    secret_key=config.alpaca_api_secret_key,
    trading_mode="paper"
)

clock = alpaca.get_clock()
print(f"Market is: {'OPEN' if clock['is_open'] else 'CLOSED'}")
print(f"Next open: {clock.get('next_open', 'N/A')}")
print(f"Next close: {clock.get('next_close', 'N/A')}")
```

---

## 🧪 COMPLETE VERIFICATION CHECKLIST

### ✅ Backend Features (Test These Anytime - Even When Market Closed)

#### 1. Portfolio History API ✅
**Status:** FULLY IMPLEMENTED
**Test:**
```python
from src.core.alpaca_service import AlpacaService
from src.utils.config import Config

config = Config()
alpaca = AlpacaService(
    api_key=config.alpaca_api_key_id,
    secret_key=config.alpaca_api_secret_key,
    trading_mode="paper"
)

# Get portfolio history (works even when market closed!)
history = alpaca.get_portfolio_history(period="1M", timeframe="1Day")
print(f"✅ Got {len(history)} history points")
for point in history[:3]:
    print(f"  {point['timestamp']}: ${point['equity']:.2f}")
```
**UI Location:** Dashboard portfolio chart

#### 2. Account Activities API ✅
**Status:** FULLY IMPLEMENTED
**Test:**
```python
activities = alpaca.get_account_activities(activity_type="FILL", page_size=10)
print(f"✅ Got {len(activities)} activities")
```
**UI Location:** Not exposed yet (backend only)

#### 3. Advanced Order Types ✅
**Status:** ALL IMPLEMENTED
**Test (even when market closed - orders will queue):**
```python
# Bracket Order (Entry + TP + SL)
result = alpaca.submit_bracket_order(
    symbol="AAPL",
    qty=1,
    side="buy",
    take_profit_limit_price=200.0,
    stop_loss_stop_price=180.0
)
print(f"✅ Bracket order: {result.get('id', 'submitted')}")

# Trailing Stop
result = alpaca.submit_trailing_stop_order(
    symbol="AAPL",
    qty=10,
    side="sell",
    trail_percent=2.0
)
print(f"✅ Trailing stop: {result.get('id', 'submitted')}")
```
**UI Location:** Order form (may need order type selector)

#### 4. WebSocket Streaming ✅
**Status:** IMPLEMENTED (runs in background)
**Test:**
```python
from src.core.alpaca_websocket import AlpacaWebSocket
# WebSocket runs automatically when bot starts
```
**UI Location:** Background (invisible, but working)

#### 5. Data Cache & Provider ✅
**Status:** IMPLEMENTED
**Test:**
```python
from src.core.data_provider import DataProvider
from src.core.data_cache import DataCache

cache = DataCache()
provider = DataProvider(alpaca_service=alpaca, cache=cache)

# Get historical data (works even when market closed)
from datetime import datetime, timedelta
bars = provider.get_historical_bars(
    symbol="AAPL",
    timeframe="1Day",
    start=datetime.now() - timedelta(days=30),
    end=datetime.now()
)
print(f"✅ Got {len(bars)} bars from cache/provider")
```

#### 6. AI Strategy System ✅
**Status:** FULLY IMPLEMENTED
**Test:**
```python
# Verify AI strategy can be created
from src.ml import AIStrategy, AIStrategyConfig
from src.ml.models import SklearnClassificationModel

model = SklearnClassificationModel(model_id="test", version="1.0.0")
config = AIStrategyConfig(model=model, min_confidence=0.65)
strategy = AIStrategy(config)
print("✅ AI Strategy created successfully")
```
**UI Location:** Strategy creation (type="ai")

---

### ⚠️ What You Can Test When Market is CLOSED

#### Backend Testing (Works Anytime):
1. ✅ **Portfolio History** - Get historical equity data
2. ✅ **Account Activities** - View past trades/fills
3. ✅ **Submit Orders** - Orders will queue for next market open
4. ✅ **Data Provider** - Get historical market data
5. ✅ **Feature Engineering** - Test ML feature creation
6. ✅ **Model Training** - Train AI models
7. ✅ **Backtesting** - Run backtests on historical data

#### Frontend Testing (Works Anytime):
1. ✅ **Dashboard** - View portfolio chart (uses portfolio history)
2. ✅ **Account Info** - See account balance, positions
3. ✅ **Strategy Management** - Create/edit strategies
4. ✅ **Settings** - Configure bot settings

---

### ❌ What Requires Market to be OPEN

1. **Live Trading** - Bot won't execute trades when closed
2. **Real-Time Data Streaming** - WebSocket only streams when market open
3. **Live Order Execution** - Orders execute only during market hours

---

## 📍 WHERE TO FIND FEATURES IN UI

### Dashboard (`/` or `/dashboard`)
- ✅ Portfolio chart (uses portfolio history API)
- ✅ Account balance
- ✅ Current positions
- ✅ Bot status panel

### Strategy Management (`/strategies`)
- ✅ Create strategies (RSI, MACD, Bollinger, AI)
- ✅ View active strategies
- ✅ Edit strategy parameters

### Bot Control Panel (on Dashboard)
- ✅ Start/Stop bot buttons
- ⚠️ Market status indicator (but may not show next open time)
- ✅ Active strategies count
- ✅ Open positions count

### Settings/Account (`/account` or `/settings`)
- ✅ Alpaca credentials configuration
- ✅ Trading symbols
- ✅ Risk parameters

---

## 🔍 FEATURES STATUS API

Create this endpoint to see what's available:

```python
# Add to src/app.py
@app.route("/api/features/status", methods=["GET"])
@login_required
def get_features_status():
    """Get comprehensive features status."""
    try:
        user_id = session.get("user_id")
        alpaca_service = get_user_alpaca_service(user_id)

        features = {
            "portfolio_history": {"implemented": True, "ui": "Dashboard chart"},
            "account_activities": {"implemented": True, "ui": "Not exposed"},
            "bracket_orders": {"implemented": True, "ui": "Order form"},
            "trailing_stops": {"implemented": True, "ui": "Order form"},
            "websocket_streaming": {"implemented": True, "ui": "Background"},
            "data_cache": {"implemented": True, "ui": "Transparent"},
            "ai_strategies": {"implemented": True, "ui": "Strategy creation"},
            "market_hours": {},
        }

        if alpaca_service:
            clock = alpaca_service.get_clock()
            features["market_hours"] = {
                "is_open": clock.get("is_open", False),
                "next_open": clock.get("next_open"),
                "next_close": clock.get("next_close"),
            }

        return jsonify({"status": "success", "features": features})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

---

## 🎯 TESTING STRATEGY

### When Market is CLOSED:

1. **Test Backend APIs:**
   ```bash
   python3 scripts/verify_implementation.py
   ```

2. **Test Portfolio History:**
   - Go to Dashboard
   - Portfolio chart should show (even when market closed)

3. **Test Strategy Creation:**
   - Create RSI/MACD/Bollinger strategies
   - Create AI strategy (if model trained)

4. **Test Backtesting:**
   - Run backtests on historical data
   - Market doesn't need to be open!

5. **Test Order Submission:**
   - Submit orders (they'll queue for market open)
   - Check order status

### When Market is OPEN:

1. **Start Bot** - Live trading
2. **Watch Real-Time Data** - WebSocket streaming
3. **See Live Orders** - Order execution
4. **Monitor Performance** - Real-time P&L

---

## 📊 QUICK STATUS CHECK

Run this script to see everything:

```bash
python3 scripts/verify_implementation.py
```

Then check market status:
```python
python3 -c "
from src.core.alpaca_service import AlpacaService
from src.utils.config import Config
config = Config()
alpaca = AlpacaService(
    api_key=config.alpaca_api_key_id,
    secret_key=config.alpaca_api_secret_key,
    trading_mode='paper'
)
clock = alpaca.get_clock()
print(f'Market: {'OPEN' if clock['is_open'] else 'CLOSED'}')
print(f'Next open: {clock.get('next_open', 'N/A')}')
"
```

---

## 🚀 WHAT TO DO RIGHT NOW (Market Closed)

1. **Verify Implementation:**
   ```bash
   python3 scripts/verify_implementation.py
   ```

2. **Check Dashboard:**
   - Portfolio chart should work (uses portfolio history)
   - Account info should show
   - Bot status should display

3. **Create Strategies:**
   - Add RSI strategy
   - Add MACD strategy
   - Prepare AI strategy config

4. **Run Backtests:**
   - Test strategies on historical data
   - Market doesn't need to be open!

5. **Test Order Types:**
   - Submit bracket orders (they'll queue)
   - Check order status

---

## ⏰ Market Opens Tomorrow (If Weekday)

**US Market Hours:**
- Monday-Friday: 9:30 AM - 4:00 PM ET
- That's 6:30 AM - 1:00 PM PT, 2:30 PM - 9:00 PM UTC

Check current status:
```bash
python3 -c "
from datetime import datetime
from src.core.alpaca_service import AlpacaService
from src.utils.config import Config
config = Config()
alpaca = AlpacaService(api_key=config.alpaca_api_key_id, secret_key=config.alpaca_api_secret_key, trading_mode='paper')
clock = alpaca.get_clock()
print('Current time:', datetime.now())
print('Market open:', clock.get('is_open'))
print('Next open:', clock.get('next_open'))
"
```
