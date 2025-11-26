# Database Naming Conventions & Best Practices

## Overview

This document outlines the naming conventions and best practices used in the IntellectScout trading bot database schema. These conventions follow industry standards for clarity, maintainability, and consistency.

---

## Table Naming Convention

### Rule 1: Tables should be **plural nouns**

**Rationale**: Tables represent collections of entities, so plural naming is standard practice.

### Rule 2: **NO table prefixes** (use database schemas instead)

**Rationale**:
- Table prefixes (like `IS_USERS`) are **not recommended** in modern database design
- Use **database schemas** for namespace separation (PostgreSQL)
- For SQLite, clean table names are sufficient (single namespace)
- See `SCHEMA_NAMING_STRATEGY.md` for detailed strategy

**Current Status**: ✅ **Already correct** - All tables use clean names without prefixes

**Rationale**: Tables represent collections of entities, so plural naming is standard practice.

**Current Status**:
- ✅ `users` - Correct
- ✅ `portfolios` - Correct
- ✅ `positions` - Correct
- ✅ `orders` - Correct
- ✅ `trades` - Correct
- ✅ `strategies` - Correct
- ✅ `signals` - Correct
- ✅ `backtest_results` - Correct
- ✅ `email_tokens` - Correct
- ✅ `user_credentials` - Correct
- ✅ `market_data_bars` - Correct
- ✅ `user_settings` - Correct
- ✅ `portfolio_snapshots` - Correct
- ⚠️ `audit_log` → Should be `audit_logs` (to be fixed in future migration)

---

## Column Naming Convention

### Boolean Columns

**Rule**: Boolean columns should be prefixed with `is_`, `has_`, or `can_` for clarity.

**Rationale**: Makes boolean columns immediately identifiable and self-documenting.

**Current Status**:
- ✅ `is_active` (user_credentials, strategies) - Correct
- ✅ `is_paper` (portfolios) - Correct
- ⚠️ `email_verified` → Should be `is_email_verified` (to be fixed in future migration)
- ⚠️ `executed` → Should be `is_executed` (to be fixed in future migration)

**Examples**:
```python
is_active = Column(Boolean, default=False)  # ✅ Good
is_email_verified = Column(Boolean, default=False)  # ✅ Good
executed = Column(Boolean, default=False)  # ⚠️ Should be is_executed
email_verified = Column(Boolean, default=False)  # ⚠️ Should be is_email_verified
```

### Foreign Key Columns

**Rule**: Foreign key columns should be named `{referenced_table}_id`

**Rationale**: Clear and consistent naming makes relationships obvious.

**Current Status**:
- ✅ `user_id` - Correct (references `users.id`)
- ✅ `portfolio_id` - Correct (references `portfolios.id`)
- ✅ `strategy_id` - Correct (references `strategies.id`)
- ✅ `order_id` - Correct (references `orders.id`)

### Timestamp Columns

**Rule**: Use descriptive names with `_at` suffix for timestamps.

**Current Status**:
- ✅ `created_at` - Creation timestamp
- ✅ `updated_at` - Last update timestamp
- ✅ `executed_at` - Execution timestamp
- ✅ `generated_at` - Signal generation timestamp
- ✅ `last_login` - Could be `last_login_at` for consistency (low priority)

---

## Index Naming Convention

### Single Column Indexes

**Rule**: Use prefix `ix_{table_name}_{column_name}`

**Examples**:
- `ix_users_email`
- `ix_strategies_user_id`
- `ix_signals_generated_at`

### Composite Indexes

**Rule**: Use prefix `idx_{table_name}_{columns}` (abbreviated column names)

**Examples**:
- `idx_portfolio_symbol` (for `portfolio_id`, `symbol`)
- `idx_strategy_symbol` (for `strategy_id`, `symbol`)
- `idx_user_type` (for `user_id`, `type`)

**Current Status**: Mostly consistent, but some mixing of `ix_` and `idx_` exists.

---

## Foreign Key Constraint Naming

### Rule: Explicit naming for better debugging

**Format**: `fk_{table_name}_{referenced_table}`

**Current Status**:
- ⚠️ Most foreign keys use implicit SQLAlchemy naming
- **Recommendation**: Add explicit names in future migrations for better error messages

**Example**:
```python
user_id = Column(
    Integer,
    ForeignKey("users.id", ondelete="CASCADE", name="fk_portfolios_users"),
    nullable=False,
    index=True
)
```

---

## Primary Key Convention

### Rule: Always use `id` as primary key column name

**Current Status**: ✅ All tables use `id` consistently.

---

## Naming Anti-Patterns to Avoid

1. ❌ **Singular table names** - Use plural (`users`, not `user`)
2. ❌ **Unprefixed boolean columns** - Use `is_*` prefix (`is_active`, not `active`)
3. ❌ **Abbreviated column names** - Use full words (`quantity`, not `qty`)
4. ❌ **Mixed case** - Use snake_case consistently
5. ❌ **Reserved keywords** - Avoid SQL keywords (`order` → use `orders`, `type` → acceptable but consider `strategy_type`)

---

## Future Improvements

### Phase 1: Boolean Column Renaming (Breaking Change)
- [ ] Rename `email_verified` → `is_email_verified` in `users` table
- [ ] Rename `executed` → `is_executed` in `signals` table
- [ ] Update all code references
- [ ] Create migration with data preservation

### Phase 2: Table Renaming (Breaking Change)
- [ ] Rename `audit_log` → `audit_logs` table
- [ ] Update all code references
- [ ] Create migration

### Phase 3: Index Naming Standardization (Non-Breaking)
- [ ] Review all indexes
- [ ] Standardize to `ix_` for single, `idx_` for composite
- [ ] Create migration to rename indexes

### Phase 4: Foreign Key Naming (Non-Breaking)
- [ ] Add explicit names to all foreign key constraints
- [ ] Update models
- [ ] Create migration

---

## References

- [SQLAlchemy Naming Conventions](https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData)
- [PostgreSQL Naming Conventions](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS)
- [Database Design Best Practices](https://www.postgresql.org/docs/current/ddl-best-practices.html)
