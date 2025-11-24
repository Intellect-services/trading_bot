# Database Reset Guide

## Quick Reset

To completely reset your database and start fresh:

```bash
isbot reset-db
```

This will:
1. Ask for confirmation (type `yes` to proceed)
2. Delete all SQLite database files
3. Drop all tables
4. Recreate all tables with fresh schema
5. Default admin user will be created on next app startup

## Manual Reset

If you prefer to reset manually:

### Option 1: Using the reset script
```bash
python scripts/reset_db.py
```

### Option 2: Delete database files and restart
```bash
# Stop the application first
isbot stop

# Delete database files
rm -f trading_bot.db src/trading_bot.db

# Restart the application (tables will be recreated automatically)
isbot start
```

### Option 3: Using Python directly
```python
from flask import Flask
from src.database import db, init_db

app = Flask(__name__)
init_db(app)

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset complete!")
```

## What Gets Reset

- **All users** (including admin user - will be recreated on next startup)
- **All user credentials** (Alpaca API keys)
- **All email tokens** (verification and password reset tokens)
- **All trading data** (positions, orders, etc.)

## After Reset

After resetting:
1. The default admin user (`admin@admin.com` / `admin`) will be created on next app startup
2. You'll need to register new user accounts
3. Users will need to configure their Alpaca credentials again

## PostgreSQL (Production/Staging)

If you're using PostgreSQL (via `DATABASE_URL`), the reset script will:
- Drop all tables in the connected database
- Recreate them with fresh schema
- **WARNING**: This affects the actual production/staging database if `DATABASE_URL` is set!

For production databases, consider using migrations instead:
```bash
isbot migrate
```
