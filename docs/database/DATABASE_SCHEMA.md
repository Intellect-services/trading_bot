# Database Schema Documentation

## Overview

The trading bot uses a **multi-layer database architecture** with two ORM systems:
1. **Flask-SQLAlchemy** (`db.Model`) - For authentication and core user management
2. **BaseModel** (SQLAlchemy Declarative) - For business domain models (trading, strategies)

All database changes are managed through **Alembic migrations**, ensuring version-controlled, database-agnostic schema evolution.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Flask App, API Routes, Business Logic)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORM Layer                                 │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ Flask-SQLAlchemy   │  │  BaseModel (Declarative)     │  │
│  │  (db.Model)        │  │  (Infrastructure Layer)      │  │
│  └────────────────────┘  └──────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Migration Layer (Alembic)                       │
│  - Version Control                                          │
│  - Database-Agnostic Migrations                             │
│  - Rollback Support                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ SQLite   │  │PostgreSQL│  │  Other   │                  │
│  │ (Local)  │  │(Prod)    │  │          │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Layers

### Layer 1: Authentication & Core (Flask-SQLAlchemy)

**Purpose**: User management, authentication, session handling

```
┌─────────────┐
│    users    │
│─────────────│
│ id (PK)     │
│ email       │◄──────────────────┐
│ password    │                   │
│ name        │                   │
│ role        │                   │
│ verified    │                   │
└─────────────┘                   │
      │                           │
      │ 1:N                       │ 1:1
      ▼                           │
┌─────────────────┐      ┌──────────────────┐
│  email_tokens   │      │user_credentials  │
│─────────────────│      │──────────────────│
│ id (PK)         │      │ id (PK)          │
│ user_id (FK)    │      │ user_id (FK)     │◄───┐
│ token           │      │ api_key_enc      │    │
│ token_type      │      │ secret_enc       │    │
│ expires_at      │      │ trading_mode     │    │
└─────────────────┘      └──────────────────┘    │
                                                │
┌─────────────────┐                             │
│market_data_bars │                             │
│─────────────────│                             │
│ id (PK)         │                             │
│ symbol          │                             │
│ timestamp       │                             │
│ open/high/low   │                             │
│ close/volume    │                             │
└─────────────────┘                             │
                                                │
                                ┌───────────────┴───────────┐
                                │  Business Domain Models   │
                                │  (BaseModel Layer)        │
                                └───────────────┬───────────┘
```

---

### Layer 2: Business Domain Models (BaseModel)

**Purpose**: Trading operations, strategies, portfolio management

#### 2.1 Trading Domain

```
┌─────────────┐
│  portfolios │
│─────────────│
│ id (PK)     │◄──────────────────┐
│ user_id (FK)│                    │
│ name        │                    │
│ capital     │                    │
│ cash        │                    │
│ is_paper    │                    │
└─────────────┘                    │
      │                            │
      │ 1:N                        │
      ├────────────────────────────┤
      │                            │
      ├─────────────┐              │
      ▼             ▼              │
┌──────────┐  ┌──────────┐        │
│positions │  │  orders  │        │
│──────────│  │──────────│        │
│ id (PK)  │  │ id (PK)  │        │
│ port_id  │  │ port_id  │        │
│ symbol   │  │ symbol   │        │
│ qty      │  │ qty      │        │
│ price    │  │ status   │        │
│ side     │  │ type     │        │
└──────────┘  └────┬─────┘        │
                   │ 1:N          │
                   ▼              │
            ┌──────────┐          │
            │  trades  │          │
            │──────────│          │
            │ id (PK)  │          │
            │ order_id │          │
            │ port_id  │          │
            │ price    │          │
            │ pl       │          │
            └──────────┘          │
                                  │
┌─────────────────┐               │
│portfolio_snap   │               │
│─────────────────│               │
│ id (PK)         │               │
│ portfolio_id    │───────────────┘
│ total_value     │
│ snapshot_at     │
└─────────────────┘
```

#### 2.2 Strategy Domain

```
┌─────────────┐
│ strategies  │
│─────────────│
│ id (PK)     │◄──────────────┐
│ user_id (FK)│                │
│ name        │                │
│ type        │                │
│ parameters  │                │
│ is_active   │                │
└─────────────┘                │
      │                        │
      │ 1:N                    │ 1:N
      ▼                        │
┌──────────┐          ┌──────────────────┐
│ signals  │          │ backtest_results │
│──────────│          │──────────────────│
│ id (PK)  │          │ id (PK)          │
│ strat_id │          │ strategy_id (FK) │
│ symbol   │          │ start_date       │
│ type     │          │ end_date         │
│ strength │          │ performance      │
│ executed │          │ metrics          │
└──────────┘          └──────────────────┘
```

#### 2.3 Common Domain

```
┌─────────────┐
│ user_setting│
│─────────────│
│ id (PK)     │
│ user_id (FK)│
│ key         │
│ value (JSON)│
└─────────────┘

┌─────────────┐
│ audit_log   │
│─────────────│
│ id (PK)     │
│ user_id (FK)│
│ entity_type │
│ action      │
│ changes     │
└─────────────┘
```

---

## Complete Entity Relationship Diagram

```
                    ┌─────────────┐
                    │    users    │
                    │─────────────│
                    │ id          │
                    │ email       │
                    │ password    │
                    │ role        │
                    └───┬─────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        │ 1:N           │ 1:1           │ 1:N          │ 1:N
        ▼               ▼               ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐
│email_tokens  │ │user_cred    │ │strategies│ │portfolios │
└──────────────┘ └─────────────┘ └────┬─────┘ └─────┬─────┘
                                       │            │
                                       │ 1:N        │ 1:N
                    ┌──────────────────┴──┐         │
                    │                      │         │
                    ▼                      ▼         │
            ┌──────────────┐      ┌──────────┐      │
            │  signals     │      │backtest_ │      │
            └──────────────┘      │ results  │      │
                                  └──────────┘      │
                                                    │
                    ┌───────────────────────────────┘
                    │
        ┌───────────┼─────────────┬──────────────┐
        │           │             │              │
        │ 1:N       │ 1:N         │ 1:N          │
        ▼           ▼             ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐
│positions │ │  orders  │ │portfolio_│ │user_setting │
└──────────┘ └────┬─────┘ │ snapshots│ └─────────────┘
                  │       └──────────┘
                  │ 1:N
                  ▼
            ┌──────────┐
            │  trades  │
            └──────────┘
```

---

## Table Details

### Flask-SQLAlchemy Tables

#### `users`
**Purpose**: User accounts and authentication

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `email` | VARCHAR(120) | Unique email address |
| `password_hash` | VARCHAR(255) | Bcrypt hashed password |
| `name` | VARCHAR(100) | User's full name |
| `avatar` | VARCHAR(255) | Avatar URL |
| `email_verified` | BOOLEAN | Email verification status |
| `email_verification_token` | VARCHAR(255) | Verification token |
| `role` | VARCHAR(20) | User role: 'trader', 'admin', 'owner' |
| `created_at` | DATETIME | Account creation timestamp |
| `last_login` | DATETIME | Last login timestamp |

**Indexes**: `email`, `email_verification_token`

#### `user_credentials`
**Purpose**: Encrypted Alpaca API credentials per user

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` (unique) |
| `alpaca_api_key_encrypted` | TEXT | Encrypted API key |
| `alpaca_secret_key_encrypted` | TEXT | Encrypted secret key |
| `trading_mode` | VARCHAR(20) | 'paper' or 'live' |
| `is_active` | BOOLEAN | Whether credentials are active |
| `last_verified_at` | DATETIME | Last verification timestamp |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `user_id`

#### `email_tokens`
**Purpose**: Email verification and password reset tokens

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `token` | VARCHAR(255) | Unique token string |
| `token_type` | VARCHAR(50) | 'verification' or 'password_reset' |
| `expires_at` | DATETIME | Token expiration |
| `used_at` | DATETIME | When token was used (nullable) |
| `created_at` | DATETIME | Creation timestamp |

**Indexes**: `token`, `user_id`

#### `market_data_bars`
**Purpose**: Historical market data (OHLCV bars)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `symbol` | VARCHAR(10) | Stock symbol |
| `timestamp` | DATETIME | Bar timestamp |
| `open` | NUMERIC | Opening price |
| `high` | NUMERIC | High price |
| `low` | NUMERIC | Low price |
| `close` | NUMERIC | Closing price |
| `volume` | INTEGER | Trading volume |
| `created_at` | DATETIME | Record creation timestamp |

**Indexes**: `symbol`, `timestamp`

---

### BaseModel Tables (Trading Domain)

#### `portfolios`
**Purpose**: User trading portfolios (paper/live)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `name` | VARCHAR(100) | Portfolio name |
| `description` | TEXT | Portfolio description |
| `initial_capital` | NUMERIC(15,2) | Starting capital |
| `current_value` | NUMERIC(15,2) | Current portfolio value |
| `cash_balance` | NUMERIC(15,2) | Available cash |
| `buying_power` | NUMERIC(15,2) | Available buying power |
| `is_paper` | BOOLEAN | Paper trading flag |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `user_id`

#### `positions`
**Purpose**: Open trading positions

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `portfolio_id` | INTEGER | Foreign key to `portfolios.id` |
| `symbol` | VARCHAR(10) | Stock symbol |
| `quantity` | NUMERIC(15,4) | Position quantity |
| `avg_entry_price` | NUMERIC(15,4) | Average entry price |
| `current_price` | NUMERIC(15,4) | Current market price |
| `market_value` | NUMERIC(15,2) | Current market value |
| `unrealized_pl` | NUMERIC(15,2) | Unrealized P&L |
| `unrealized_pl_percent` | NUMERIC(10,4) | Unrealized P&L percentage |
| `side` | VARCHAR(10) | 'long' or 'short' |
| `opened_at` | DATETIME | Position open time |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(portfolio_id, symbol)`, `opened_at`

#### `orders`
**Purpose**: Trading orders (all types: market, limit, stop, etc.)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `portfolio_id` | INTEGER | Foreign key to `portfolios.id` |
| `alpaca_order_id` | VARCHAR(100) | External Alpaca order ID (unique) |
| `symbol` | VARCHAR(10) | Stock symbol |
| `quantity` | NUMERIC(15,4) | Order quantity |
| `filled_quantity` | NUMERIC(15,4) | Filled quantity |
| `side` | VARCHAR(10) | 'buy' or 'sell' |
| `type` | VARCHAR(20) | Order type: 'market', 'limit', 'stop', etc. |
| `time_in_force` | VARCHAR(10) | 'day', 'gtc', 'ioc', 'fok' |
| `status` | VARCHAR(20) | 'pending', 'filled', 'cancelled', etc. |
| `limit_price` | NUMERIC(15,4) | Limit price (if applicable) |
| `stop_price` | NUMERIC(15,4) | Stop price (if applicable) |
| `filled_avg_price` | NUMERIC(15,4) | Average fill price |
| `commission` | NUMERIC(10,4) | Commission paid |
| `filled_at` | DATETIME | Fill timestamp (nullable) |
| `cancelled_at` | DATETIME | Cancellation timestamp (nullable) |
| `created_at` | DATETIME | Order creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(portfolio_id, symbol)`, `status`, `created_at`

#### `trades`
**Purpose**: Executed trades (fills from orders)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `order_id` | INTEGER | Foreign key to `orders.id` |
| `portfolio_id` | INTEGER | Foreign key to `portfolios.id` |
| `symbol` | VARCHAR(10) | Stock symbol |
| `quantity` | NUMERIC(15,4) | Trade quantity |
| `price` | NUMERIC(15,4) | Execution price |
| `side` | VARCHAR(10) | 'buy' or 'sell' |
| `commission` | NUMERIC(10,4) | Commission paid |
| `realized_pl` | NUMERIC(15,2) | Realized P&L |
| `executed_at` | DATETIME | Execution timestamp |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(portfolio_id, symbol)`, `executed_at`

#### `portfolio_snapshots`
**Purpose**: Historical portfolio value snapshots for performance tracking

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `portfolio_id` | INTEGER | Foreign key to `portfolios.id` |
| `total_value` | NUMERIC(15,2) | Total portfolio value |
| `cash_balance` | NUMERIC(15,2) | Cash balance |
| `positions_value` | NUMERIC(15,2) | Total positions value |
| `total_pl` | NUMERIC(15,2) | Total P&L |
| `daily_pl` | NUMERIC(15,2) | Daily P&L |
| `snapshot_at` | DATETIME | Snapshot timestamp |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(portfolio_id, snapshot_at)`

---

### BaseModel Tables (Strategy Domain)

#### `strategies`
**Purpose**: Trading strategy configurations

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `name` | VARCHAR(100) | Strategy name |
| `description` | TEXT | Strategy description |
| `type` | VARCHAR(50) | Strategy type: 'rsi', 'macd', 'bollinger', 'ai', etc. |
| `parameters` | JSON | Strategy-specific parameters |
| `risk_parameters` | JSON | Risk management parameters |
| `is_active` | BOOLEAN | Whether strategy is active |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(user_id, type)`

#### `signals`
**Purpose**: Trading signals generated by strategies

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `strategy_id` | INTEGER | Foreign key to `strategies.id` |
| `symbol` | VARCHAR(10) | Stock symbol |
| `signal_type` | VARCHAR(10) | 'buy', 'sell', 'hold' |
| `strength` | NUMERIC(5,2) | Signal strength (0-100) |
| `price` | NUMERIC(15,4) | Price at signal generation |
| `indicators` | JSON | Technical indicator values |
| `generated_at` | DATETIME | Signal generation timestamp |
| `executed` | BOOLEAN | Whether signal was executed |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(strategy_id, symbol)`, `generated_at`

#### `backtest_results`
**Purpose**: Historical backtesting performance results

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `strategy_id` | INTEGER | Foreign key to `strategies.id` |
| `start_date` | DATE | Backtest start date |
| `end_date` | DATE | Backtest end date |
| `initial_capital` | NUMERIC(15,2) | Starting capital |
| `final_value` | NUMERIC(15,2) | Ending value |
| `total_return` | NUMERIC(10,4) | Total return percentage |
| `sharpe_ratio` | NUMERIC(10,4) | Sharpe ratio |
| `max_drawdown` | NUMERIC(10,4) | Maximum drawdown |
| `win_rate` | NUMERIC(10,4) | Win rate (0-1) |
| `total_trades` | INTEGER | Total number of trades |
| `metrics` | JSON | Additional performance metrics |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `(strategy_id, end_date)`

---

### BaseModel Tables (Common Domain)

#### `user_settings`
**Purpose**: User-specific settings and preferences

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `key` | VARCHAR(100) | Setting key |
| `value` | JSON | Setting value |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `key`, `(user_id, key)` (unique)

#### `audit_log`
**Purpose**: Audit trail for important actions

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to `users.id` (nullable) |
| `entity_type` | VARCHAR(50) | Entity type (e.g., 'order', 'strategy') |
| `entity_id` | INTEGER | Entity ID |
| `action` | VARCHAR(20) | Action performed |
| `changes` | JSON | Changes made |
| `ip_address` | VARCHAR(45) | User IP address |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**: `user_id`, `(user_id, entity_type)`, `created_at`

---

## Migration System

### Using Alembic Migrations

All database schema changes are managed through Alembic migrations:

```bash
# Run all pending migrations
python scripts/migrate.py upgrade head

# Rollback one migration
python scripts/migrate.py downgrade -1

# Check current migration state
python scripts/migrate.py current

# Create new migration
python scripts/migrate.py revision --autogenerate -m "Add new column"

# Show migration history
python scripts/migrate.py history
```

### Migration Files Location

Migrations are stored in: `alembic/versions/`

Each migration file contains:
- `upgrade()` - Applies the migration
- `downgrade()` - Rolls back the migration
- Revision ID and dependencies

---

## Database Configuration

### Local Development (SQLite)

Default location: `src/trading_bot.db`

```bash
# No DATABASE_URL needed - defaults to SQLite
python src/app.py
```

### Production/Staging (PostgreSQL)

Set `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgresql://user:pass@host:port/dbname
python src/app.py
```

### Docker Compose

PostgreSQL is configured in `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: intellecttrader
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

The app automatically uses PostgreSQL when `DATABASE_URL` is set.

---

## Best Practices

1. **Always use migrations** - Never manually modify the database schema
2. **Test migrations** - Test both upgrade and downgrade paths
3. **Backup first** - Always backup before running migrations in production
4. **Review migrations** - Review auto-generated migrations before committing
5. **One change per migration** - Keep migrations focused and atomic
6. **Database-agnostic code** - Avoid SQLite-specific features

---

## Troubleshooting

### Migration Errors

1. Check current migration state: `python scripts/migrate.py current`
2. Review migration history: `python scripts/migrate.py history`
3. Check for conflicts in migration dependencies

### Missing Tables

1. Ensure all models are imported in `alembic/env.py`
2. Run migrations: `python scripts/migrate.py upgrade head`
3. Check for errors in migration files

### Database Connection Issues

1. Verify `DATABASE_URL` is set correctly
2. Check PostgreSQL is running (if using PostgreSQL)
3. Verify network connectivity and credentials

---

## Related Documentation

- [Database Migration Guide](migration-guide.md)
- [Alembic Configuration](alembic-config.md)
- [Model Relationships](model-relationships.md)
