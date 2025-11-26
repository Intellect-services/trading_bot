# Database Documentation

## Overview

The IntellectScout trading bot uses a **production-ready database migration system** based on Alembic, supporting both SQLite (local development) and PostgreSQL (production/staging).

## Quick Links

- **[Database Schema](DATABASE_SCHEMA.md)** - Complete schema documentation with ER diagrams
- **[Migration Guide](MIGRATION_GUIDE.md)** - How to use migrations
- **[Naming Conventions](NAMING_CONVENTIONS.md)** - Table, column, and index naming standards
- **[Schema Naming Strategy](SCHEMA_NAMING_STRATEGY.md)** - Schema vs. prefix strategy (IMPORTANT)
- **[Database Migration Assessment](../DATABASE_MIGRATION_ASSESSMENT.md)** - Original assessment and planning

## Key Features

✅ **Database-Agnostic** - Works with SQLite and PostgreSQL
✅ **Version-Controlled** - All schema changes tracked in Git
✅ **Rollback Support** - Can undo migrations if needed
✅ **Production-Ready** - Proper migration system for all environments
✅ **Multi-Layer Architecture** - Flask-SQLAlchemy + BaseModel unified
✅ **Clean Naming** - No table prefixes, uses schemas (PostgreSQL)

## Quick Start

### Running Migrations

```bash
# Check current state
python scripts/migrate.py current

# Apply all pending migrations
python scripts/migrate.py upgrade head

# Create new migration
python scripts/migrate.py revision --autogenerate -m "Description"

# Rollback one migration
python scripts/migrate.py downgrade -1
```

### Resetting Database

```bash
# Reset database (drops all tables and recreates)
python scripts/reset_db.py
```

## Architecture

The database uses a **dual ORM system**:

1. **Flask-SQLAlchemy** (`db.Model`) - Authentication & core models
   - `users`, `user_credentials`, `email_tokens`, `market_data_bars`

2. **BaseModel** (SQLAlchemy Declarative) - Business domain models
   - Trading: `portfolios`, `positions`, `orders`, `trades`, `portfolio_snapshots`
   - Strategies: `strategies`, `signals`, `backtest_results`
   - Common: `user_settings`, `audit_log`

Both systems are unified through Alembic migrations.

## Naming Strategy

### ✅ Current: Clean Table Names (No Prefixes)

**Tables**: `users`, `portfolios`, `orders`, etc. (clean, no prefixes)

**Rationale**:
- Modern best practice
- Works seamlessly with ORMs
- Easy to read and maintain
- Can use database schemas for namespace separation (PostgreSQL)

**See**: `SCHEMA_NAMING_STRATEGY.md` for detailed explanation of why we don't use table prefixes like `IS_USERS`.

### Future: Database Schema Support (PostgreSQL)

When deploying to PostgreSQL production:
- **Schema name**: `intellect_scout`
- **Table names**: Same clean names (`users`, `portfolios`)
- **Full reference**: `intellect_scout.users` (in SQL)
- **Application code**: Still uses `users` (search_path handles it)

**Benefits**:
- Better organization
- Schema-level security
- Multiple applications in one database

## Environment Configuration

### Local Development (SQLite)
Default - no configuration needed:
```bash
python src/app.py
```

**Tables**: `users`, `portfolios`, `orders` (single namespace)

### Production/Staging (PostgreSQL)
Set `DATABASE_URL` environment variable:
```bash
export DATABASE_URL=postgresql://user:pass@host:port/dbname
python src/app.py
```

**Schema**: `intellect_scout` (optional, can be added later)
**Tables**: Same names as SQLite (easy migration)

### Docker Compose
PostgreSQL is automatically configured:
```bash
docker-compose up
```

## Database Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/migrate.py` | Migration CLI | ✅ Active |
| `scripts/reset_db.py` | Reset database | ✅ Active (uses migrations) |
| `scripts/create_strategy_tables.py` | ⚠️ Deprecated | Use migrations |
| `scripts/create_user_settings_table.py` | ⚠️ Deprecated | Use migrations |
| `scripts/migrate_db.py` | ⚠️ Deprecated | Use migrations |

## Migration Files

Migrations are stored in: `alembic/versions/`

Current migrations:
- `f9179e223e34` - Add trading domain models
- `add_user_auth_features` - Add user authentication features
- `eecf196c7107` - Initial schema with all tables (latest)

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Schema Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
