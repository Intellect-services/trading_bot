# Database Schema Naming Strategy

## Executive Summary

**Recommendation**: Use **database schemas** (not table prefixes) for namespace separation. This follows modern industry best practices and provides better organization and flexibility.

---

## Table Prefixes vs. Database Schemas

### ❌ Table Prefixes (NOT Recommended)

**Example**: `IS_USERS`, `IS_PORTFOLIOS`, `IS_ORDERS`

**Problems**:
- ❌ Makes queries verbose: `SELECT * FROM IS_USERS WHERE...`
- ❌ Redundant - database already provides namespace
- ❌ Harder to maintain - prefix must be consistent everywhere
- ❌ Breaks ORM conventions (SQLAlchemy expects clean names)
- ❌ Doesn't scale well with multiple schemas/modules
- ❌ Violates modern best practices

**When Prefixes ARE Acceptable**:
- Multi-tenant systems (where tenant isolation is required)
- Legacy systems (migration from old systems)
- External integrations (third-party tables)

---

### ✅ Database Schemas (RECOMMENDED)

**Example**: Schema `intellect_scout` containing `users`, `portfolios`, `orders`

**Benefits**:
- ✅ Clean, readable table names: `SELECT * FROM intellect_scout.users`
- ✅ Logical organization by application/module
- ✅ Supports multiple schemas in one database
- ✅ Better security isolation (schema-level permissions)
- ✅ Industry standard approach
- ✅ Works seamlessly with ORMs
- ✅ Easier maintenance and refactoring

---

## Recommended Schema Structure

### For PostgreSQL (Production)

Use **database schemas** for logical grouping:

```sql
-- Main application schema
CREATE SCHEMA IF NOT EXISTS intellect_scout;

-- Optional: Separate schemas for different modules
CREATE SCHEMA IF NOT EXISTS intellect_scout_auth;      -- Authentication
CREATE SCHEMA IF NOT EXISTS intellect_scout_trading;   -- Trading operations
CREATE SCHEMA IF NOT EXISTS intellect_scout_strategies; -- Strategy management
```

**Or simpler single schema approach**:
```sql
-- Single schema for all IntellectScout tables
CREATE SCHEMA IF NOT EXISTS intellect_scout;
```

**Table names within schema**:
- `intellect_scout.users`
- `intellect_scout.portfolios`
- `intellect_scout.orders`
- etc.

---

### For SQLite (Local Development)

**Note**: SQLite doesn't support schemas - it has a single namespace.

**Solution**: Use clean table names without prefixes (since it's single-application):
- ✅ `users`
- ✅ `portfolios`
- ✅ `orders`

**Rationale**:
- SQLite is typically used for single-application databases
- No namespace conflicts expected
- Simpler setup for local development
- When migrating to PostgreSQL, tables can be moved into a schema

---

## Implementation Strategy

### Phase 1: Current State (No Changes Needed)

**Current Tables**: Already use clean names without prefixes ✅
- `users`, `portfolios`, `orders`, etc.

**Action**: ✅ **No immediate changes required**

---

### Phase 2: Add PostgreSQL Schema Support (Future)

**When migrating to PostgreSQL** (or setting up production):

1. **Create schema**:
```sql
CREATE SCHEMA IF NOT EXISTS intellect_scout;
```

2. **Set default schema in SQLAlchemy**:
```python
# In src/database.py or alembic/env.py
engine = create_engine(
    "postgresql://...",
    connect_args={"options": "-csearch_path=intellect_scout,public"}
)
```

3. **Update Alembic to use schema**:
```python
# In alembic/env.py
from sqlalchemy import event

@event.listens_for(Engine, "connect", insert=True)
def set_search_path(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET search_path TO intellect_scout, public")
    cursor.close()
```

4. **Update table definitions** (optional, for explicit schema):
```python
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "intellect_scout"}  # Optional
```

---

## Schema Naming Conventions

### Schema Name Format

**Recommended**: `{application_name}` or `{application_name}_{module}`

**Examples for IntellectScout**:
- ✅ `intellect_scout` - Single schema (simplest)
- ✅ `intellect_scout_auth` - Authentication module
- ✅ `intellect_scout_trading` - Trading module
- ✅ `is_auth` - Shorter version (if preferred)

**Naming Rules**:
- Use `snake_case` (lowercase with underscores)
- Be descriptive and clear
- Keep it concise but meaningful
- Avoid abbreviations unless widely understood

---

## Comparison Table

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **Table Prefixes** | `IS_USERS` | Simple, works in SQLite | Verbose, not scalable, breaks ORM conventions |
| **Single Schema** | `intellect_scout.users` | Clean names, logical grouping | Requires schema setup |
| **Multiple Schemas** | `intellect_scout_auth.users` | Best organization | More complex setup |

---

## Recommendation for IntellectScout

### ✅ RECOMMENDED: Single Schema Approach

**PostgreSQL**:
- Schema name: `intellect_scout`
- Table names: Clean, no prefixes (`users`, `portfolios`, etc.)
- Full reference: `intellect_scout.users`

**SQLite**:
- No schema support
- Table names: Clean, no prefixes (`users`, `portfolios`, etc.)
- Same names as PostgreSQL (easy migration)

**Benefits**:
- ✅ Clean table names throughout
- ✅ Easy migration between SQLite and PostgreSQL
- ✅ Logical grouping with schema
- ✅ Industry standard approach
- ✅ Minimal code changes needed

---

## Implementation Plan

### Current State ✅
- Tables already use clean names (no prefixes)
- Works with both SQLite and PostgreSQL
- **Action**: None required

### Future: Add Schema Support (PostgreSQL)

1. **Create migration** to create schema:
```python
def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS intellect_scout")
```

2. **Update database configuration** to use schema

3. **Update Alembic** to work with schema

4. **Test** migration path from SQLite to PostgreSQL

---

## Code Examples

### SQLAlchemy Model (Current - Works Everywhere)

```python
class User(db.Model):
    __tablename__ = "users"  # ✅ Clean name, no prefix

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
```

### SQLAlchemy Model (With Schema - PostgreSQL)

```python
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "intellect_scout"}  # Optional - can set in engine

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
```

### SQL Queries

**Without schema** (current):
```sql
SELECT * FROM users;
```

**With schema** (PostgreSQL):
```sql
SELECT * FROM intellect_scout.users;
-- Or, with search_path set:
SELECT * FROM users;  -- Resolves to intellect_scout.users
```

---

## Migration Considerations

### SQLite → PostgreSQL

**Current tables** (SQLite):
- `users`, `portfolios`, `orders`, etc.

**PostgreSQL with schema**:
- `intellect_scout.users`
- `intellect_scout.portfolios`
- `intellect_scout.orders`

**Migration**: Tables keep same names, just add to schema. No table renaming needed!

---

## Security Considerations

### Schema-Level Permissions (PostgreSQL)

```sql
-- Grant access to schema
GRANT USAGE ON SCHEMA intellect_scout TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA intellect_scout TO app_user;

-- Revoke access from public schema (if needed)
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

**Benefits**:
- ✅ Better security isolation
- ✅ Can have multiple applications in one database
- ✅ Easier permission management

---

## Conclusion

### ✅ Final Recommendation

1. **Keep current table names** (no prefixes) - ✅ Already correct!
2. **Use database schemas** for PostgreSQL production
3. **Schema name**: `intellect_scout` (single schema)
4. **No changes needed** for SQLite (local dev)

**Current Status**: ✅ **No immediate changes required**

**Future Enhancement**: Add schema support when migrating to PostgreSQL production environment.

---

## References

- [PostgreSQL Schema Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [SQLAlchemy Schema Support](https://docs.sqlalchemy.org/en/20/core/metadata.html#specifying-the-schema-name)
- [Database Design Best Practices](https://www.postgresql.org/docs/current/ddl-best-practices.html)
