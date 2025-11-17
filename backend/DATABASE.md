# Database Management Guide

This guide covers database migrations, backups, and management for Data Detective Academy.

## Table of Contents

- [Overview](#overview)
- [Database Migrations with Alembic](#database-migrations-with-alembic)
- [Seed Data](#seed-data)
- [Backup and Restore](#backup-and-restore)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## Overview

**Database Stack:**
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Migrations:** Alembic 1.17.1+
- **Development:** SQLite
- **Production:** PostgreSQL (recommended)

**Key Files:**
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup
- `alembic/versions/` - Migration files
- `scripts/seed.py` - Seed data script
- `scripts/backup.sh` - Database backup script
- `scripts/restore.sh` - Database restore script

---

## Database Migrations with Alembic

### What are Migrations?

Migrations are version-controlled database schema changes. They allow you to:
- Track schema changes over time
- Apply changes consistently across environments
- Roll back changes if needed
- Collaborate with team members safely

### Initial Setup

Alembic is already configured for this project. The configuration:
- Reads `DATABASE_URL` from environment variables
- Auto-imports all SQLModel models
- Generates migrations based on model changes

### Creating Migrations

#### Auto-generate from Model Changes

When you modify models in `app/models.py`:

```bash
# 1. Make changes to models in app/models.py
# 2. Generate migration
uv run alembic revision --autogenerate -m "Description of changes"

# 3. Review the generated migration in alembic/versions/
# 4. Edit if needed (Alembic doesn't catch everything!)
```

**Example:**
```bash
# Add a new field to User model
uv run alembic revision --autogenerate -m "Add phone_number to users"
```

#### Manual Migration (Advanced)

For complex changes that autogenerate can't detect:

```bash
uv run alembic revision -m "Description of manual changes"
```

Then edit the generated file in `alembic/versions/` to add your custom SQL.

### Applying Migrations

#### Upgrade to Latest

```bash
# Apply all pending migrations
uv run alembic upgrade head
```

#### Upgrade to Specific Version

```bash
# Upgrade to a specific revision
uv run alembic upgrade <revision_id>

# Upgrade one version forward
uv run alembic upgrade +1
```

#### Downgrade (Rollback)

```bash
# Rollback all migrations
uv run alembic downgrade base

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Rollback one version
uv run alembic downgrade -1
```

### Migration Best Practices

1. **Always Review Auto-generated Migrations**
   - Alembic can't detect all changes (e.g., renames, data migrations)
   - Review and test before committing

2. **Test Migrations Both Ways**
   ```bash
   # Test upgrade
   uv run alembic upgrade head

   # Test downgrade
   uv run alembic downgrade -1

   # Re-upgrade to verify
   uv run alembic upgrade head
   ```

3. **Backup Before Production Migrations**
   ```bash
   # Always backup before applying migrations in production
   ./scripts/backup.sh
   uv run alembic upgrade head
   ```

4. **One Migration Per Feature**
   - Keep migrations focused and atomic
   - Easier to review and rollback

5. **Never Edit Applied Migrations**
   - Once a migration is committed and shared, don't edit it
   - Create a new migration to fix issues

### Common Migration Patterns

#### Adding a Column

```python
# In app/models.py
class User(SQLModel, table=True):
    # ... existing fields ...
    phone_number: Optional[str] = Field(default=None, max_length=20)
```

```bash
uv run alembic revision --autogenerate -m "Add phone_number to users"
uv run alembic upgrade head
```

#### Renaming a Column

Alembic can't auto-detect renames. Manual migration needed:

```bash
uv run alembic revision -m "Rename user email to email_address"
```

Edit the generated migration:
```python
def upgrade():
    op.alter_column('users', 'email', new_column_name='email_address')

def downgrade():
    op.alter_column('users', 'email_address', new_column_name='email')
```

#### Data Migration

For migrating data alongside schema changes:

```python
def upgrade():
    # Schema change
    op.add_column('users', sa.Column('status', sa.String(20)))

    # Data migration
    op.execute("UPDATE users SET status = 'active' WHERE last_login IS NOT NULL")
    op.execute("UPDATE users SET status = 'inactive' WHERE last_login IS NULL")

def downgrade():
    op.drop_column('users', 'status')
```

---

## Seed Data

### Overview

The seed script (`scripts/seed.py`) populates the database with sample data for development and testing.

### Usage

#### Full Seed (Recommended for Development)

```bash
uv run python scripts/seed.py
```

Creates:
- 1 teacher account
- 5 student accounts
- Sample progress data

#### Minimal Seed

```bash
uv run python scripts/seed.py --minimal
```

Creates:
- 1 teacher account
- 2 student accounts
- No progress data

#### Clear and Reseed

```bash
uv run python scripts/seed.py --clear
```

**⚠️ WARNING:** This deletes ALL existing data!

### Default Accounts

After seeding, you can log in with:

**Teacher Account:**
- Email: `teacher@example.com`
- Password: `teacher123`

**Student Accounts:**
- Email: `alice@example.com` / Password: `student123`
- Email: `bob@example.com` / Password: `student123`
- Email: `charlie@example.com` / Password: `student123`
- Email: `diana@example.com` / Password: `student123`
- Email: `eve@example.com` / Password: `student123`

### Customizing Seed Data

Edit `scripts/seed.py` to modify:
- Sample accounts
- Sample progress data
- Initial datasets

---

## Backup and Restore

### Backup Database

The backup script supports both SQLite and PostgreSQL:

```bash
# Backup to default location (./backups/)
./scripts/backup.sh

# Backup to custom location
./scripts/backup.sh /path/to/backup/directory
```

**Features:**
- Automatic compression (gzip)
- Timestamped filenames
- Keeps last 10 backups automatically
- Supports both SQLite and PostgreSQL

**Output:**
```
backups/
  backup_20250117_143022.db.gz
  backup_20250116_101500.db.gz
  ...
```

### Restore Database

```bash
# Restore from backup
./scripts/restore.sh backups/backup_20250117_143022.db.gz
```

**⚠️ WARNING:** This replaces the current database!

The script will:
1. Ask for confirmation
2. Backup current database (SQLite only)
3. Restore from backup file
4. Handle decompression automatically

### Automated Backups (Production)

Set up automated backups with cron:

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * cd /path/to/backend && ./scripts/backup.sh /path/to/backups
```

---

## Common Tasks

### Fresh Database Setup

```bash
# 1. Create database tables
uv run alembic upgrade head

# 2. Seed with sample data
uv run python scripts/seed.py
```

### Reset Database (Development)

```bash
# Method 1: Delete and recreate (SQLite)
rm data_detective_academy.db
uv run alembic upgrade head
uv run python scripts/seed.py

# Method 2: Use seed script with --clear
uv run python scripts/seed.py --clear
```

### Update Database Schema

```bash
# 1. Modify models in app/models.py
# 2. Create migration
uv run alembic revision --autogenerate -m "Your change description"

# 3. Review migration in alembic/versions/
# 4. Apply migration
uv run alembic upgrade head
```

### Check Migration Status

```bash
# Show current revision
uv run alembic current

# Show migration history
uv run alembic history

# Show pending migrations
uv run alembic heads
```

### Inspect Database

#### SQLite (Development)

```bash
# Web-based browser
uv run sqlite_web data_detective_academy.db

# Command line
sqlite3 data_detective_academy.db
sqlite> .tables
sqlite> .schema users
sqlite> SELECT * FROM users;
```

#### PostgreSQL (Production)

```bash
# Command line
psql -h localhost -U username -d data_detective_academy

# List tables
\dt

# Describe table
\d users

# Query
SELECT * FROM users;
```

---

## Troubleshooting

### Migration Conflicts

**Problem:** Multiple developers created migrations simultaneously

```bash
# Check for multiple heads
uv run alembic heads

# Merge migrations
uv run alembic merge -m "Merge migrations" <rev1> <rev2>
```

### "Target database is not up to date"

**Problem:** Database schema doesn't match models

```bash
# Check current version
uv run alembic current

# Check pending migrations
uv run alembic history

# Apply missing migrations
uv run alembic upgrade head
```

### Alembic Can't Detect Changes

**Problem:** Model changes not detected by autogenerate

**Common causes:**
- Column renames (requires manual migration)
- Data type changes in some cases
- Index changes
- Constraint changes

**Solution:** Create manual migration

```bash
uv run alembic revision -m "Manual migration description"
# Edit the generated file
```

### Migration Fails Halfway

**Problem:** Migration error leaves database in inconsistent state

**Solution:**

```bash
# 1. Check current version
uv run alembic current

# 2. Restore from backup
./scripts/restore.sh backups/latest_backup.db.gz

# 3. Fix migration file
# Edit alembic/versions/<migration_file>.py

# 4. Try again
uv run alembic upgrade head
```

### "Import Error" in Migrations

**Problem:** Can't import models in migration

**Solution:** Ensure `alembic/env.py` imports all models:

```python
from app.models import (
    User,
    RefreshToken,
    # ... all models
)
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Backup current database
- [ ] Test migrations on staging environment
- [ ] Review all migration files
- [ ] Verify rollback procedures
- [ ] Plan maintenance window if needed

### Deployment Process

```bash
# 1. Backup production database
./scripts/backup.sh /secure/backup/location

# 2. Pull latest code
git pull origin main

# 3. Apply migrations
uv run alembic upgrade head

# 4. Restart application
# (Process depends on hosting platform)

# 5. Verify application health
# Check logs, test critical endpoints
```

### Rollback Procedure

If deployment fails:

```bash
# 1. Rollback migrations
uv run alembic downgrade -1

# 2. Restart application
# (Revert to previous code version)

# 3. Or restore from backup
./scripts/restore.sh /secure/backup/location/backup_YYYYMMDD_HHMMSS.db.gz
```

### Zero-Downtime Migrations

For large production databases:

1. **Backward-compatible migrations only**
   - Add columns as nullable first
   - Populate data in separate deployment
   - Make non-nullable in third deployment

2. **Use migration transactions**
   - Most migrations run in transactions automatically
   - Test rollback procedure

3. **Monitor during migration**
   - Watch database performance
   - Monitor application logs
   - Have rollback plan ready

### PostgreSQL Production Best Practices

1. **Connection Pooling**
   - Already configured in `app/database.py`
   - Default: 5 connections, 10 max overflow

2. **Indexes**
   - All important foreign keys are indexed
   - Email lookups are indexed
   - Token lookups are indexed

3. **Backups**
   - Set up automated daily backups
   - Test restore procedure regularly
   - Keep backups for 30 days minimum

4. **Monitoring**
   - Monitor query performance
   - Watch for slow queries
   - Set up alerts for database errors

---

## Environment Variables

Required environment variables for database management:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost/dbname

# Database configuration (optional)
DB_ECHO=false                # Log SQL queries
DB_POOL_SIZE=5              # Connection pool size
DB_MAX_OVERFLOW=10          # Max additional connections
```

---

## Additional Resources

- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **SQLModel Documentation:** https://sqlmodel.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/

---

## Quick Reference

```bash
# Migrations
uv run alembic upgrade head              # Apply all pending
uv run alembic downgrade -1              # Rollback one version
uv run alembic current                   # Show current version
uv run alembic history                   # Show history
uv run alembic revision --autogenerate -m "msg"  # Create migration

# Seed Data
uv run python scripts/seed.py            # Full seed
uv run python scripts/seed.py --minimal  # Minimal seed
uv run python scripts/seed.py --clear    # Clear and reseed

# Backup/Restore
./scripts/backup.sh                      # Create backup
./scripts/restore.sh <backup_file>       # Restore from backup

# Database Inspection
uv run sqlite_web data_detective_academy.db  # SQLite browser
sqlite3 data_detective_academy.db            # SQLite CLI
psql -d data_detective_academy               # PostgreSQL CLI
```

---

**Last Updated:** 2025-11-17
