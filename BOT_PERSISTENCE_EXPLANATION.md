# Bot Persistence & Session Dependency - Current State

## ⚠️ **CRITICAL ISSUE: Bot Will NOT Trade When You're Logged Out**

### Current Architecture Problems

#### 1. **In-Memory Cache (Lost on Restart)**
```python
# src/app.py:204
_user_bot_cache: dict[int, TradingBot] = {}  # ❌ Lost when Flask restarts!
```

**Problem:**
- Bot instances stored in Python dictionary (RAM only)
- Server restart = all bots lost
- No persistence to database

#### 2. **Session-Dependent Bot Control**
```python
# src/app.py:1060-1084
@app.route("/api/start", methods=["POST"])
@login_required  # ❌ Requires active session!
def start_bot():
    user_id = session.get("user_id")  # ❌ Session-based
    trading_bot = get_user_trading_bot(user_id)
    trading_bot.start()
```

**Problem:**
- Must be logged in to start/stop bot
- Session expiration = can't control bot
- No "auto-start on login" mechanism

#### 3. **Daemon Threads (Die on Server Stop)**
```python
# src/core/bot.py:181
self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
# ❌ Daemon threads die when Flask app stops!
```

**Problem:**
- Daemon threads = automatically killed when main process ends
- Server restart = all trading loops stop
- No automatic restart mechanism

## Current Workflow

### When You Start the Bot:
1. ✅ You log in (create session)
2. ✅ Click "Start Bot" in UI
3. ✅ Flask receives POST to `/api/start` (requires session)
4. ✅ Creates `TradingBot` instance
5. ✅ Stores in `_user_bot_cache[user_id]`
6. ✅ Starts trading loop in daemon thread
7. ✅ Bot trades in background

### When You Log Out:
1. ❌ Session expires/cleared
2. ✅ Bot instance **stays in cache** (if Flask running)
3. ✅ Trading thread **continues running** (independent of session)
4. ❌ **BUT:** You can't control it (no session = can't call API)

### When Server Restarts (Deployment/Update):
1. ❌ Flask app restarts
2. ❌ `_user_bot_cache` is **cleared** (empty dictionary)
3. ❌ All daemon threads are **killed**
4. ❌ All bots **stop trading**
5. ❌ **NO auto-restart** - bots stay stopped

## What Actually Happens

### ✅ **Will Continue Trading:**
- After you log out (if server stays running)
- During your browser session (if you just close browser but don't log out)

### ❌ **Will STOP Trading:**
- **Server restart** (deployment, update, crash, Railway restart)
- **Flask process killed** (OOM, crash, manual stop)
- **Container restart** (Docker redeploy)
- **Any process interruption**

## Deployment Scenarios

### Scenario 1: Railway/Render Deployment
```
1. Deploy new code → Server restarts
2. _user_bot_cache = {} (empty)
3. All bots stop ❌
4. User must log in and manually restart bot
```

### Scenario 2: Log Out
```
1. User logs out → Session cleared
2. Bot instance in cache (if server running)
3. Trading thread continues ✅
4. But user can't control it ❌
```

### Scenario 3: Server Crash
```
1. Server crashes → Process dies
2. Daemon threads killed ❌
3. All bots stop
4. No recovery mechanism
```

## Required Solution

To make bots trade continuously, you need:

### 1. **Database Persistence of Bot State**
Store in database (not just memory):
- `bot_auto_start: bool` - should bot start automatically?
- `bot_is_running: bool` - current running status
- `bot_started_at: datetime` - when was it started
- `bot_stopped_at: datetime` - when was it stopped

### 2. **Auto-Restart on Server Startup**
On Flask app initialization:
```python
def auto_start_bots():
    # Check database for users with bot_auto_start=True
    # Recreate bot instances
    # Start bots automatically
```

### 3. **Persistent Bot Process**
Options:
- **Option A:** Non-daemon threads + graceful shutdown handling
- **Option B:** Separate worker process (Celery, RQ, etc.)
- **Option C:** Separate microservice for bots
- **Option D:** Systemd service (for VPS)

## Recommended Implementation

### Phase 1: Quick Fix (Database State + Auto-Restart)

1. Add `bot_auto_start` flag to `UserSettings` table
2. Store bot state in database (synced with memory)
3. On Flask startup: Check database → Auto-restart bots
4. Keep current architecture but add persistence

**Pros:** Quick, minimal changes
**Cons:** Still dies if Flask crashes

### Phase 2: Robust Solution (Separate Worker)

1. Create separate bot worker service
2. Use Celery/Redis or separate Python process
3. Flask sends commands via database/queue
4. Worker runs independently

**Pros:** Very robust, survives Flask restarts
**Cons:** More complex, requires Redis/queue

## Next Steps

Would you like me to implement:

1. **Quick Fix:** Database persistence + auto-restart on startup?
2. **Robust Solution:** Separate bot worker service?
3. **Hybrid:** Database persistence first, then worker later?

The bot currently **WILL NOT** trade continuously - it stops on every server restart and requires manual restart after login.
