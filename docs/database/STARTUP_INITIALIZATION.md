# Database Startup & Initialization Guide

## Overview

This document explains how the database is initialized and managed during application startup.

---

## How Database Creation Works

### 1. Application Startup Flow

```
App Starts
    ↓
src/app.py loads
    ↓
init_db(app) called (line 76)
    ↓
src/database.py::init_db()
    ↓
Checks if alembic_version table exists
    ↓
    ├─ NO → Fresh Database
    │         ├─ Creates Flask-SQLAlchemy tables (db.create_all())
    │         ├─ Creates BaseModel tables (Base.metadata.create_all())
    │         └─ Stamps database with latest migration
    │
    └─ YES → Existing Database
              ├─ Runs Alembic migrations (upgrade head)
              └─ If migrations fail → Falls back to create_all()
    ↓
Final Safety Check
    ↓
Verifies all required tables exist
    ↓
Creates any missing tables
    ↓
Creates default admin user (if doesn't exist)
```

---

## Environments

### Local Development (SQLite)

**Database File**: `src/trading_bot.db`

**Creation**:
- ✅ Created automatically when app starts
- ✅ Location: `src/trading_bot.db`
- ✅ All tables created via `init_db()`

**Usage**:
```bash
python run.py
# or
python src/app.py
```

**Reset**:
```bash
isbot reset-db
# or
python scripts/reset_db.py
```

---

### Docker Development (PostgreSQL)

**Database Container**: `intellecttrader_db` (PostgreSQL 15)

**Creation**:
1. ✅ Docker Compose creates PostgreSQL container
2. ✅ Database `intellecttrader` created automatically by PostgreSQL
3. ✅ Tables created when app starts (via `init_db()`)

**Configuration** (`docker-compose.yml`):
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: intellecttrader
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}

  app:
    depends_on:
      db:
        condition: service_healthy  # Waits for database
    environment:
      - DATABASE_URL=postgresql://trader:${DB_PASSWORD:-changeme}@db:5432/intellecttrader
```

**Usage**:
```bash
docker-compose up
```

**Database Initialization**:
- App waits for database healthcheck
- App starts → `init_db()` runs → Creates all tables

---

## Database Initialization Details

### Fresh Database (First Time)

**What Happens**:
1. `init_db()` detects no `alembic_version` table
2. Creates Flask-SQLAlchemy tables:
   - `users`
   - `user_credentials`
   - `email_tokens`
   - `market_data_bars`
3. Creates BaseModel tables:
   - `portfolios`, `positions`, `orders`, `trades`
   - `portfolio_snapshots`
   - `strategies`, `signals`, `backtest_results`
   - `user_settings`, `audit_log`
4. Creates `alembic_version` table
5. Stamps database with latest migration revision
6. Creates default admin user (`admin@admin.com` / `admin`)

**Total Tables Created**: 15

---

### Existing Database

**What Happens**:
1. `init_db()` detects `alembic_version` table exists
2. Runs Alembic migrations: `upgrade head`
3. Ensures schema is up-to-date
4. If migrations fail → Falls back to `create_all()`
5. Final safety check verifies all tables exist
6. Creates any missing tables

---

## Fallback Mechanisms

### Multiple Layers of Protection

1. **Primary**: Alembic migrations (`command.upgrade()`)
2. **Secondary**: Flask-SQLAlchemy `db.create_all()`
3. **Tertiary**: BaseModel `Base.metadata.create_all()`
4. **Final**: Safety check that verifies each required table exists

**Result**: Database tables are **guaranteed** to exist on startup.

---

## Default Admin User

**Created Automatically** (if doesn't exist):
- Email: `admin@admin.com`
- Password: `admin`
- Role: `owner`
- Email Verified: `True`

**Location**: `src/database.py` lines 212-225

---

## isbot Script Integration

### reset-db Command

**Command**: `isbot reset-db`

**What It Does**:
1. Shows warning about data deletion
2. Asks for confirmation (type `yes`)
3. Calls `scripts/reset_db.py`
4. `reset_db.py`:
   - Uses Alembic migrations to drop all tables
   - Recreates all tables via migrations
   - Falls back to `create_all()` if migrations fail

**Usage**:
```bash
isbot reset-db
# Type 'yes' when prompted
```

**Status**: ✅ Updated to use migration system

---

## Testing

### Manual Testing

**Test Fresh Database**:
```bash
# Stop app
isbot stop

# Delete database
rm -f src/trading_bot.db

# Start app (database will be recreated)
isbot start

# Verify tables exist
python -c "
from flask import Flask
from src.database import init_db, db
from sqlalchemy import inspect

app = Flask(__name__)
init_db(app)
with app.app_context():
    inspector = inspect(db.engine)
    print('Tables:', sorted(inspector.get_table_names()))
"
```

**Test Reset**:
```bash
isbot reset-db
# Type 'yes'
# Verify all tables recreated
```

---

### Automated Testing

**Test Files**:
- `tests/database/test_startup_initialization.py` - Startup tests
- `tests/database/test_docker_initialization.py` - Docker tests
- `tests/database/test_isbot_integration.py` - isbot script tests

**Run Tests**:
```bash
pytest tests/database/test_startup_initialization.py -v
```

---

## Troubleshooting

### Tables Not Created

**Symptoms**: Errors like "no such table: users"

**Solutions**:
1. Check `init_db()` is called in `src/app.py`
2. Check database file permissions (SQLite)
3. Check DATABASE_URL is correct (PostgreSQL)
4. Check logs for initialization errors

**Debug**:
```python
from flask import Flask
from src.database import init_db, db
from sqlalchemy import inspect

app = Flask(__name__)
init_db(app)
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
```

---

### Docker Database Issues

**Check Database Container**:
```bash
docker-compose ps
docker-compose logs db
```

**Check App Can Connect**:
```bash
docker-compose exec app python -c "
import os
from flask import Flask
from src.database import init_db, db

app = Flask(__name__)
init_db(app)
with app.app_context():
    print('Database connected:', db.engine.url)
"
```

---

## Summary

✅ **Database Creation**: Automatic on app startup
✅ **Docker Support**: PostgreSQL container + automatic table creation
✅ **isbot Integration**: Updated for migration system
✅ **Multiple Fallbacks**: Robust error handling
✅ **Testing**: Comprehensive test coverage

**Status**: ✅ **Production Ready**
