## Backend Development Setup

```bash
cd backend

# Install dependencies
uv sync --all-extras

# Create .env file from template
cp .env.example .env
# Edit .env and set your SECRET_KEY (generate with: openssl rand -hex 32)

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