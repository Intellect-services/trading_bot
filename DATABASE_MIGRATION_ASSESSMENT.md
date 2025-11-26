# Database Migration & Cleanup Assessment

## Current State Analysis

### Database Setup
- **Local Development**: SQLite (`sqlite:///src/trading_bot.db`)
- **Production/Staging**: PostgreSQL (via `DATABASE_URL` env var)
- **Docker**: PostgreSQL 15 via docker-compose (already configured!)

### Current Issues

1. **Manual Table Creation**
   - Raw SQL DDL in `src/database.py` (~550 lines)
   - SQLite-specific code (`sqlite_master`, `AUTOINCREMENT`, pragmas)
   - Multiple ad-hoc scripts: `create_strategy_tables.py`, `create_user_settings_table.py`
   - No proper migration system

2. **Mixed ORM Systems**
   - Flask-SQLAlchemy models (users, email_tokens, user_credentials, market_data_bars)
   - BaseModel (infrastructure) models (strategies, portfolios, positions, etc.)
   - Two separate metadata systems causing FK resolution issues

3. **SQLite-Specific Code**
   - `sqlite_master` queries (9 files)
   - `INTEGER PRIMARY KEY AUTOINCREMENT` (should be `SERIAL` for PostgreSQL)
   - SQLite pragmas (`journal_mode`, `synchronous`, `foreign_keys`, `locking_mode`)
   - File permission handling for SQLite

4. **Alembic Partially Configured**
   - Alembic exists but only tracks BaseModel metadata
   - Doesn't track Flask-SQLAlchemy models
   - Only 2 migration files exist
   - `env.py` only imports BaseModel, missing Flask-SQLAlchemy models

5. **No Migration Workflow**
   - No script to run migrations
   - No rollback mechanism
   - No environment-specific migration handling

## Migration to PostgreSQL - All Environments

### Recommendation: ✅ **YES, migrate to PostgreSQL everywhere**

**Benefits:**
- ✅ Consistent database across all environments
- ✅ Better concurrent access (no SQLite locking issues)
- ✅ Production-ready features (transactions, constraints, better performance)
- ✅ Easier deployment (already have docker-compose setup)
- ✅ Better tooling and monitoring options
- ✅ Supports complex queries and aggregations better

**PostgreSQL is already in place:**
- Docker Compose has PostgreSQL configured
- `psycopg2-binary` is in requirements.txt
- `init_db()` already supports PostgreSQL via `DATABASE_URL`

### Effort Estimation

#### Phase 1: Database Cleanup & Migration Setup (4-6 hours)
**Risk Level: 🟡 Medium**

1. **Set up Alembic properly** (2 hours)
   - Configure `alembic/env.py` to track both Flask-SQLAlchemy and BaseModel
   - Create initial migration from existing schema
   - Test migration generation

2. **Convert SQL to SQLAlchemy Models** (2-3 hours)
   - Review all Flask-SQLAlchemy models (users, user_credentials, etc.)
   - Create proper BaseModel classes for BaseModel tables
   - Ensure all relationships are defined
   - Test model definitions

3. **Remove Manual SQL Creation** (1 hour)
   - Remove `_create_base_model_tables()` function
   - Remove `_create_user_settings_table()` function
   - Update `init_db()` to use Alembic migrations instead
   - Clean up ad-hoc scripts

**Deliverables:**
- ✅ Proper Alembic configuration
- ✅ All models defined in SQLAlchemy
- ✅ Initial migration script
- ✅ Migration CLI script

#### Phase 2: PostgreSQL Migration & Compatibility (3-4 hours)
**Risk Level: 🟢 Low-Medium**

1. **Database-agnostic Code** (2 hours)
   - Remove `sqlite_master` queries (9 files)
   - Replace `AUTOINCREMENT` with SQLAlchemy `autoincrement=True`
   - Use SQLAlchemy's table inspection instead of raw SQL
   - Remove SQLite-specific pragmas
   - Update `reset_db.py` to use Alembic

2. **PostgreSQL-specific Optimizations** (1 hour)
   - Update connection pooling settings
   - Remove SQLite file permission handling
   - Add PostgreSQL-specific indexes if needed
   - Test with local PostgreSQL (docker-compose)

3. **Environment Configuration** (1 hour)
   - Update `.env.example` with PostgreSQL defaults
   - Update documentation for local PostgreSQL setup
   - Ensure docker-compose works out of the box

**Deliverables:**
- ✅ Database-agnostic codebase
- ✅ Local PostgreSQL via docker-compose
- ✅ Updated documentation

#### Phase 3: Migration Testing & Rollout (2-3 hours)
**Risk Level: 🟡 Medium**

1. **Test Migrations** (1-2 hours)
   - Test fresh database creation
   - Test migrations from existing SQLite database
   - Test rollback functionality
   - Test in docker-compose environment

2. **Data Migration Script** (1 hour)
   - Create script to migrate existing SQLite data to PostgreSQL (if needed)
   - Test data integrity after migration
   - Document migration process

**Deliverables:**
- ✅ Migration scripts tested
- ✅ Data migration script (if needed)
- ✅ Rollback tested

---

## Total Effort Estimate

| Phase | Hours | Risk Level |
|-------|-------|------------|
| Phase 1: Cleanup & Setup | 4-6h | 🟡 Medium |
| Phase 2: PostgreSQL Migration | 3-4h | 🟢 Low-Medium |
| Phase 3: Testing & Rollout | 2-3h | 🟡 Medium |
| **Total** | **9-13 hours** | **🟡 Medium** |

---

## Risk Assessment

### 🟢 Low Risk
- Docker Compose PostgreSQL already configured
- Code already supports PostgreSQL via `DATABASE_URL`
- `psycopg2-binary` already in dependencies

### 🟡 Medium Risk
- Mixed ORM systems (Flask-SQLAlchemy + BaseModel) - need careful coordination
- Existing data migration (if users have data in SQLite)
- Alembic configuration complexity for dual metadata
- Breaking changes during migration (need testing)

### 🔴 Mitigation Strategies
1. **Backup First**: Always backup existing SQLite database before migration
2. **Dual Support**: Keep SQLite support during transition, remove later
3. **Gradual Rollout**: Test in dev → staging → production
4. **Migration Scripts**: Automated migration scripts with rollback capability
5. **Documentation**: Clear migration guide for each environment

---

## Implementation Plan

### Step 1: Preparation (1 hour)
- [ ] Backup existing SQLite database
- [ ] Document current schema (generate ER diagram)
- [ ] Review all database queries in codebase
- [ ] Set up local PostgreSQL via docker-compose

### Step 2: Alembic Setup (2 hours)
- [ ] Configure Alembic to track both metadata systems
- [ ] Create unified migration system
- [ ] Generate initial migration
- [ ] Test migration up/down

### Step 3: Code Cleanup (3-4 hours)
- [ ] Convert manual SQL to SQLAlchemy models
- [ ] Remove SQLite-specific code
- [ ] Update database initialization
- [ ] Update reset_db.py script

### Step 4: PostgreSQL Testing (2 hours)
- [ ] Test with docker-compose PostgreSQL
- [ ] Test migrations in all environments
- [ ] Test data migration (if needed)
- [ ] Update documentation

### Step 5: Rollout (1 hour)
- [ ] Update .env files for all environments
- [ ] Deploy to staging first
- [ ] Verify functionality
- [ ] Deploy to production

---

## Files to Modify

### High Priority
1. `src/database.py` - Remove manual SQL, use Alembic
2. `alembic/env.py` - Add Flask-SQLAlchemy models
3. `scripts/reset_db.py` - Use Alembic instead of raw SQL
4. `scripts/create_strategy_tables.py` - Remove (use migrations)
5. `scripts/create_user_settings_table.py` - Remove (use migrations)

### Medium Priority
6. All files with `sqlite_master` queries (9 files)
7. Model files - Ensure proper BaseModel definitions
8. `.env.example` - Add PostgreSQL defaults
9. Documentation files - Update setup instructions

### Low Priority
10. Test files - Update for PostgreSQL
11. Docker files - Already good, minor tweaks

---

## Recommended Approach

### Option A: Full PostgreSQL Migration (Recommended) ✅
**Timeline**: 9-13 hours
**Risk**: 🟡 Medium
**Benefit**: Clean, consistent, production-ready

### Option B: Keep SQLite for Local, PostgreSQL for Production
**Timeline**: 5-7 hours
**Risk**: 🟢 Low
**Benefit**: Faster, less risky, but inconsistent environments

**Recommendation**: **Option A** - The codebase already supports PostgreSQL, docker-compose is set up, and the inconsistency issues justify the extra effort.

---

## Next Steps

1. **Review this assessment** - Confirm approach and priorities
2. **Create implementation plan** - Break down into tasks
3. **Start with Phase 1** - Set up Alembic properly
4. **Incremental testing** - Test each phase before moving forward

Would you like me to proceed with the implementation? I can start with Phase 1 (Alembic setup) first.
