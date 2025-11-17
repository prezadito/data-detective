## Backend Development Setup

```bash
cd backend

# Install dependencies
uv sync --all-extras

# Create .env file from template
cp .env.example .env
# Edit .env and set your SECRET_KEY (generate with: openssl rand -hex 32)

# Set up database
uv run alembic upgrade head      # Apply migrations
uv run python scripts/seed.py    # Seed with sample data (optional)

# Run tests
uv run pytest tests/ -v

# Run server
uvicorn app.main:app --reload
```

## Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30)
- `DATABASE_URL` - Database connection string (default: SQLite)

**IMPORTANT:** Never commit the `.env` file to version control!

## Database Management

### Migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create new migration after model changes
uv run alembic revision --autogenerate -m "Description"

# Rollback last migration
uv run alembic downgrade -1

# Check migration status
uv run alembic current
```

### Seed Data

```bash
# Seed database with sample data
uv run python scripts/seed.py

# Minimal seed (1 teacher, 2 students)
uv run python scripts/seed.py --minimal

# Clear and reseed (⚠️ DESTRUCTIVE!)
uv run python scripts/seed.py --clear
```

### Backup and Restore

```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backups/backup_20250117_143022.db.gz
```

**For comprehensive database management documentation, see [DATABASE.md](DATABASE.md)**