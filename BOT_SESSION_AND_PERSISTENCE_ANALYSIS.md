# Bot Session & Persistence Analysis

## Current Architecture

### ❌ **PROBLEM: Bot is Session-Dependent**

#### Current Workflow:

1. **Bot Storage:**
   - Bots are stored in **in-memory cache** (`_user_bot_cache` dictionary in `src/app.py:204`)
   - Each user gets their own `TradingBot` instance
   - Cache is lost when Flask server restarts

2. **Bot Startup:**
   - User must be **logged in** (session required)
   - Bot started via `/api/start` endpoint (requires `@login_required`)
   - Bot instance created on-demand: `get_user_trading_bot(user_id)`
   - Bot runs in **daemon thread** (`daemon=True` in `bot.py:181`)

3. **Bot Execution:**
   - Trading loop runs in separate thread (`_trading_loop()`)
   - Thread is **daemon thread** - dies when main process ends
   - No database persistence of "should be running" state

### ❌ **Issues:**

1. **Session Dependency:**
   - User must be logged in to start bot
   - Bot can be stopped if user logs out and cache is cleared
   - Session expiration = bot stops

2. **No Persistence:**
   - Bot state only in memory (`is_running` flag)
   - Server restart = all bots stop
   - No database record of "should be running"

3. **Daemon Threads:**
   - Daemon threads die when Flask app stops
   - Server restart = threads killed
   - No automatic restart mechanism

## What Happens When You Log Out?

1. **Session expires** (or is cleared)
2. **Bot instance stays in cache** (if Flask server still running)
3. **Bot continues running** (threads are independent of session)
4. **BUT:** You can't control it without logging back in

## What Happens on Server Restart?

1. **Flask app restarts**
2. **In-memory cache is cleared** (`_user_bot_cache` is empty)
3. **All daemon threads are killed**
4. **All bots stop**
5. **No automatic restart** - user must log in and start again

## What Happens on Deployment?

1. **If using Railway/Render/etc:**
   - Server may restart automatically
   - Cache is lost
   - Bots stop
   - User must log in and restart

2. **If using Docker:**
   - Container restart = cache lost
   - Bots stop
   - User must restart

## Solution Required for Continuous Trading

To make bots trade even when logged out, you need:

### 1. **Database Persistence of Bot State**

Add a field to track "should be running":
- UserSettings or BotState table
- `bot_auto_start: bool` flag
- `bot_is_running: bool` status
- Store in database (not just memory)

### 2. **Auto-Restart on Server Start**

On Flask app startup:
- Check database for users with `bot_auto_start=True`
- Recreate bot instances
- Restart bots automatically

### 3. **Non-Daemon Threads or Separate Process**

Options:
- Use non-daemon threads (but Flask shutdown will hang)
- Use separate worker process (Celery, RQ)
- Use systemd service for bot processes
- Use separate microservice for bots

### 4. **Background Service Architecture**

Best approach for production:
- Separate bot service/process
- Communicates with Flask app via database/Redis
- Flask app just controls start/stop commands
- Bot service persists independently

## Recommended Implementation

### Option A: Quick Fix (Database State + Auto-Restart)

1. Add `bot_auto_start` to UserSettings table
2. Store `bot_is_running` state in database
3. On Flask startup, auto-restart bots where `bot_auto_start=True`
4. Keep in-memory cache but sync with database

**Pros:** Quick, minimal changes
**Cons:** Still dependent on Flask process staying alive

### Option B: Separate Bot Service (Recommended for Production)

1. Create separate bot service/worker
2. Use Celery or separate Python process
3. Flask app sends commands via database/Redis
4. Bot service runs independently

**Pros:** Robust, survives Flask restarts
**Cons:** More complex architecture

### Option C: Systemd Service (For VPS/Self-Hosted)

1. Create systemd service for bot
2. Flask app controls via database flags
3. Bot runs as system service

**Pros:** Very robust
**Cons:** Requires VPS, more deployment complexity

## Current Status: ❌ Won't Work for Continuous Trading

**The bot will STOP when:**
- ✅ Server restarts (cache lost)
- ⚠️ You log out (can't control it, but it may continue if server running)
- ✅ Flask app crashes or is killed
- ✅ Deployment/redeployment happens

**The bot will CONTINUE when:**
- ✅ You log out (if server stays running, threads continue)
- ❌ Server restarts (cache lost, threads killed)

## Next Steps

Would you like me to implement:
1. **Database persistence** of bot state?
2. **Auto-restart** mechanism on server startup?
3. **Separate bot service** architecture?

Let me know which approach you prefer!
