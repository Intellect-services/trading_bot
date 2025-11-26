# Database Schema Audit & Improvements

## Issues Found

### 1. Boolean Column Naming Convention ⚠️
**Industry Standard**: Boolean columns should be prefixed with `is_`, `has_`, or `can_` for clarity.

**Issues**:
- `email_verified` → Should be `is_email_verified`
- `executed` → Should be `is_executed`

**Already Correct**:
- ✅ `is_active` (user_credentials, strategies)
- ✅ `is_paper` (portfolios)

### 2. Table Naming Convention ⚠️
**Industry Standard**: Table names should be plural nouns.

**Issues**:
- `audit_log` → Should be `audit_logs`

**Already Correct**:
- ✅ `users`, `portfolios`, `positions`, `orders`, `trades`, `strategies`, `signals`, `backtest_results`, `email_tokens`, `user_credentials`, `market_data_bars`, `user_settings`, `portfolio_snapshots`

### 3. Schema Creation on Startup ⚠️
**Current Issue**: `init_db()` has fallback to `db.create_all()`, but it doesn't ensure BaseModel tables are created if migrations fail.

**Fix Needed**: Ensure all tables (Flask-SQLAlchemy + BaseModel) are created even if migrations fail.

### 4. Database Instance Naming
**Current**: Uses `db` which is standard for Flask-SQLAlchemy ✅

### 5. Index Naming Convention
**Current**: Mix of `ix_`, `idx_` prefixes
**Best Practice**: Consistent prefix - `ix_` for single column, `idx_` for composite

### 6. Foreign Key Naming
**Current**: Implicit naming by SQLAlchemy
**Best Practice**: Explicit foreign key constraint names for better debugging

---

## Recommended Fixes

1. **Rename boolean columns** to follow `is_*` convention
2. **Rename `audit_log` table** to `audit_logs`
3. **Improve schema creation** on startup to be more robust
4. **Standardize index naming** conventions
5. **Add explicit foreign key names** where missing

---

## Migration Strategy

Since we're changing column names and table names, we need migrations that:
1. Rename columns (for boolean fixes)
2. Rename table (`audit_log` → `audit_logs`)
3. Update all foreign key references
4. Update all code references

**Risk Level**: 🟡 Medium (requires data migration for existing databases)
