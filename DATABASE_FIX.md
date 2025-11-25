# Database Fix - Strategies Table

## Problem
After running `isbot reset-db`, the `strategies` table was missing, causing errors when trying to create strategies.

## Solution
Updated two files to automatically create BaseModel tables:

### 1. `scripts/reset_db.py`
- Now creates BaseModel tables (`strategies`, `signals`, `backtest_results`) after resetting
- Uses raw SQL to avoid foreign key metadata issues

### 2. `src/database.py`
- Added `_create_base_model_tables()` function
- Automatically creates strategy tables on app startup if they don't exist
- Uses raw SQL to create tables (avoids SQLAlchemy metadata conflicts)

## What Happens Now

### On `isbot reset-db`:
1. ✅ Drops all Flask-SQLAlchemy tables (users, etc.)
2. ✅ Creates Flask-SQLAlchemy tables
3. ✅ Creates BaseModel tables (strategies, signals, backtest_results)

### On `isbot restart`:
1. ✅ `init_db()` creates Flask-SQLAlchemy tables
2. ✅ `_create_base_model_tables()` creates BaseModel tables if missing

## Result
- ✅ `strategies` table always exists after reset
- ✅ `signals` table always exists after reset
- ✅ `backtest_results` table always exists after reset
- ✅ No more "table does not exist" errors

## Test It
```bash
isbot reset-db
isbot restart
# Now try creating a strategy - it should work!
```
