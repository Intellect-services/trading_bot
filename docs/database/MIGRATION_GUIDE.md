# Database Migration Guide

## Quick Start

### Initial Setup

1. **Generate initial migration** (first time only):
   ```bash
   python scripts/migrate.py revision --autogenerate -m "Initial schema"
   ```

2. **Review the generated migration** in `alembic/versions/` before applying

3. **Apply migrations**:
   ```bash
   python scripts/migrate.py upgrade head
   ```

### Daily Workflow

```bash
# Check current migration state
python scripts/migrate.py current

# Apply pending migrations
python scripts/migrate.py upgrade head

# Create new migration after model changes
python scripts/migrate.py revision --autogenerate -m "Add new field"
python scripts/migrate.py upgrade head
```

---

## Migration Workflow

### Creating Migrations

1. **Make model changes** in your model files
2. **Generate migration**:
   ```bash
   python scripts/migrate.py revision --autogenerate -m "Description of changes"
   ```
3. **Review generated migration** - Alembic may not detect all changes
4. **Edit migration file** if needed (in `alembic/versions/`)
5. **Test migration**:
   ```bash
   python scripts/migrate.py upgrade head
   python scripts/migrate.py downgrade -1  # Test rollback
   python scripts/migrate.py upgrade head  # Apply again
   ```

### Rolling Back

```bash
# Rollback one migration
python scripts/migrate.py downgrade -1

# Rollback to specific revision
python scripts/migrate.py downgrade <revision_id>

# Rollback all migrations (use with caution!)
python scripts/migrate.py downgrade base
```

---

## Environment-Specific Migrations

### Local Development

```bash
# Uses SQLite by default
python scripts/migrate.py upgrade head
```

### Staging/Production

```bash
# Set DATABASE_URL first
export DATABASE_URL=postgresql://user:pass@host:port/dbname

# Run migrations
python scripts/migrate.py upgrade head
```

---

## Troubleshooting

### Migration Conflicts

If you get migration conflicts:

1. **Check migration history**:
   ```bash
   python scripts/migrate.py history
   ```

2. **Check current revision**:
   ```bash
   python scripts/migrate.py current
   ```

3. **Stamp database** to specific revision (if needed):
   ```bash
   python scripts/migrate.py stamp <revision_id>
   ```

### Missing Tables

If tables are missing after migration:

1. Ensure all models are imported in `alembic/env.py`
2. Regenerate migration:
   ```bash
   python scripts/migrate.py revision --autogenerate -m "Add missing tables"
   ```
3. Review and apply migration

### Database State Mismatch

If migration thinks database is at wrong state:

1. Check actual database state manually
2. Stamp database to correct revision:
   ```bash
   python scripts/migrate.py stamp <correct_revision>
   ```

---

## Best Practices

1. **Always review auto-generated migrations** - Alembic may miss some changes
2. **Test rollback** before deploying to production
3. **Backup database** before migrations
4. **One logical change per migration** - easier to review and rollback
5. **Use descriptive migration messages**
6. **Commit migration files** with model changes

---

## See Also

- [Database Schema Documentation](DATABASE_SCHEMA.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
