# Database Improvements Plan

## Summary

This document outlines improvements needed to align the database schema with industry best practices and standards. These improvements will be implemented in phases to minimize disruption.

---

## Critical Improvements (Immediate)

### ✅ 1. Schema Creation on Startup

**Status**: **FIXED**

**Issue**: `init_db()` didn't ensure BaseModel tables were created if migrations failed.

**Solution**: Updated `src/database.py` to:
- Create both Flask-SQLAlchemy and BaseModel tables in all fallback scenarios
- Add a final safety check to ensure all required tables exist
- Use `Base.metadata.create_all()` for BaseModel tables

**Files Modified**:
- `src/database.py` - Enhanced schema creation logic

---

## Future Improvements (Breaking Changes - Requires Migration)

### ⚠️ 2. Boolean Column Naming

**Status**: **PLANNED** - Requires migration

**Issue**: Some boolean columns don't follow `is_*` prefix convention.

**Changes Needed**:
- `users.email_verified` → `users.is_email_verified`
- `signals.executed` → `signals.is_executed`

**Impact**:
- **High**: Affects many code references
- **Files to Update**: ~30+ files
- **Migration Required**: Yes (column rename)

**Estimated Effort**: 2-3 hours

**Implementation Plan**:
1. Create Alembic migration to rename columns
2. Update all model definitions
3. Update all code references
4. Test thoroughly

---

### ⚠️ 3. Table Naming (Plural)

**Status**: **PLANNED** - Requires migration

**Issue**: `audit_log` table should be plural (`audit_logs`).

**Changes Needed**:
- Rename `audit_log` → `audit_logs`

**Impact**:
- **Medium**: Affects fewer code references (~5-10 files)
- **Migration Required**: Yes (table rename)

**Estimated Effort**: 1 hour

**Implementation Plan**:
1. Create Alembic migration to rename table
2. Update model definition (`__tablename__`)
3. Update all code references
4. Test thoroughly

---

## Low Priority Improvements (Non-Breaking)

### 📋 4. Index Naming Standardization

**Status**: **PLANNED** - Non-breaking

**Issue**: Mix of `ix_` and `idx_` prefixes.

**Standard**:
- `ix_` for single column indexes
- `idx_` for composite indexes

**Impact**: **Low** - Only affects internal naming

**Estimated Effort**: 30 minutes

---

### 📋 5. Foreign Key Constraint Naming

**Status**: **PLANNED** - Non-breaking

**Issue**: Most foreign keys use implicit SQLAlchemy naming.

**Standard**: Explicit names like `fk_{table}_{referenced_table}`

**Impact**: **Low** - Better error messages, easier debugging

**Estimated Effort**: 1 hour

---

## Recommended Implementation Order

1. ✅ **Schema Creation on Startup** (Completed)
2. ⚠️ **Boolean Column Naming** (Next - requires migration)
3. ⚠️ **Table Naming** (After boolean fixes)
4. 📋 **Index Naming** (Low priority)
5. 📋 **Foreign Key Naming** (Low priority)

---

## Migration Strategy for Breaking Changes

### Boolean Column Rename

```python
# Migration: rename_email_verified_to_is_email_verified.py

def upgrade():
    # For PostgreSQL
    op.alter_column('users', 'email_verified', new_column_name='is_email_verified')
    op.alter_column('signals', 'executed', new_column_name='is_executed')

    # For SQLite (requires table recreation)
    # 1. Create new columns
    # 2. Copy data
    # 3. Drop old columns
    # 4. Rename new columns

def downgrade():
    # Reverse the changes
    ...
```

### Table Rename

```python
# Migration: rename_audit_log_to_audit_logs.py

def upgrade():
    op.rename_table('audit_log', 'audit_logs')

def downgrade():
    op.rename_table('audit_logs', 'audit_log')
```

---

## Testing Checklist

For each breaking change:
- [ ] Create migration script
- [ ] Test migration on empty database
- [ ] Test migration on populated database
- [ ] Test rollback (downgrade)
- [ ] Update all code references
- [ ] Run full test suite
- [ ] Update API documentation
- [ ] Update database schema documentation

---

## Risk Assessment

| Change | Risk Level | Impact | Effort |
|--------|-----------|--------|--------|
| Schema Creation Fix | ✅ Low | High (fixes bugs) | Done |
| Boolean Naming | 🟡 Medium | High (many files) | 2-3 hours |
| Table Naming | 🟡 Medium | Medium (fewer files) | 1 hour |
| Index Naming | 🟢 Low | Low (internal) | 30 min |
| FK Naming | 🟢 Low | Low (internal) | 1 hour |

---

## Notes

- **Breaking changes** should be done during low-traffic periods
- **Always backup** database before running migrations
- **Test thoroughly** in staging environment first
- **Coordinate** with team if changes affect API contracts
- **Document** all changes in migration comments
