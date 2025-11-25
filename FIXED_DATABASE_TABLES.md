# Database Tables Fixed ✅

## Problem
The `strategies` table was missing, causing errors when trying to create strategies:
```
sqlite3.OperationalError) no such table: strategies
```

## Solution
Created a script `scripts/create_strategy_tables.py` that manually creates the strategy-related tables using raw SQL.

## What Was Created
- ✅ `strategies` table
- ✅ `signals` table
- ✅ `backtest_results` table
- ✅ All necessary indexes

## How to Run
The script was already executed, but if you need to run it again:

```bash
python3 scripts/create_strategy_tables.py
```

## Verify Tables Exist
```python
from flask import Flask
from src.database import init_db, db

app = Flask(__name__)
init_db(app)

with app.app_context():
    result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result.fetchall()]
    print('Tables:', sorted(tables))
    # Should include: strategies, signals, backtest_results
```

## Next Steps
Now you should be able to:
1. ✅ Create strategies via the UI
2. ✅ Store strategy configurations
3. ✅ Generate signals
4. ✅ Run backtests

Try creating a strategy again - it should work now!
