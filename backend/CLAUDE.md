# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Detective Academy - A FastAPI-based backend for an SQL learning platform. The application uses SQLModel (which combines SQLAlchemy + Pydantic) for database operations and data validation, with SQLite (dev) and PostgreSQL (production) as the database.

## Development Commands

### Setup and Installation
```bash
# Install dependencies (including dev dependencies)
uv sync --all-extras

# Install only production dependencies
uv sync

# Create .env file from template
cp .env.example .env
# Generate a secure SECRET_KEY: openssl rand -hex 32
# Edit .env and update SECRET_KEY and other variables as needed
```

### Environment Variables

Configuration is managed via `.env` file (never commit this file!):

- **SECRET_KEY**: JWT signing key - generate with `openssl rand -hex 32`
- **ALGORITHM**: JWT algorithm (default: HS256)
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Token expiration in minutes (default: 30)
- **DATABASE_URL**: Database connection string
  - Development: `sqlite:///./data_detective_academy.db`
  - Production: `postgresql://user:password@host/dbname`

The `.env.example` file provides a template. Environment variables are loaded using `python-dotenv` in `app/auth.py` and `app/database.py`.

### Running the Application
```bash
# Run development server with auto-reload
uvicorn app.main:app --reload

# Alternative: using uv
uv run uvicorn app.main:app --reload
```

### Testing
```bash
# Run all tests with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run specific test function
uv run pytest tests/test_auth.py::test_register_new_user -v

# Run tests with coverage
uv run pytest tests/ --cov=app
```

### Code Quality
```bash
# Run linter (Ruff)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### Database Tools
```bash
# View database in browser (sqlite-web)
uv run sqlite_web data_detective_academy.db
```

## Architecture

### Application Structure

The application follows a modular FastAPI architecture:

- **app/main.py**: Application entry point, includes router registration and lifespan management
- **app/database.py**: Database configuration, engine creation, and session management
- **app/models.py**: SQLModel database models (table definitions)
- **app/schemas.py**: Pydantic schemas for request/response validation (separate from DB models)
- **app/auth.py**: Authentication utilities (password hashing with bcrypt)
- **app/routes/**: API route modules organized by domain (e.g., auth.py)

### Database Architecture

**SQLModel Pattern**: This project uses SQLModel which combines SQLAlchemy (ORM) with Pydantic (validation):
- **Models** (app/models.py): Define database tables with `table=True`, include all DB fields including sensitive data
- **Schemas** (app/schemas.py): Define API request/response shapes, exclude sensitive fields like password_hash

**Key Pattern**: Always use schemas for API endpoints, never expose models directly. Example:
```python
# app/models.py - Database model
class User(SQLModel, table=True):
    password_hash: str  # Stored in DB

# app/schemas.py - API schema
class UserResponse(BaseModel):
    # password_hash NOT included - never expose in API
```

### Database Session Management

Uses dependency injection pattern via FastAPI's `Depends()`:
```python
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

@router.post("/endpoint")
def endpoint(session: Session = Depends(get_session)):
    # session automatically provided and cleaned up
```

### Lifespan Management

The app uses FastAPI's lifespan context manager pattern (not deprecated startup/shutdown events):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # Startup
    yield
    # Cleanup code here if needed
```

### Testing Architecture

Tests use in-memory SQLite databases with the following key patterns:

1. **StaticPool**: Required for in-memory SQLite to ensure all connections share the same database
2. **Fixture hierarchy**: `engine_fixture` → `session_fixture` / `client_fixture`
3. **Dependency override**: Tests override `get_session()` to use test database instead of production DB
4. **Patching create_db_and_tables**: Mock this during app import to prevent creation of production DB tables

Example test fixture pattern:
```python
@pytest.fixture(name="client")
def client_fixture(engine):
    with patch("app.database.create_db_and_tables"):
        from app.main import app
        from app.database import get_session

        def get_test_session():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
```

## Important Patterns and Conventions

### Security
- Passwords are hashed using bcrypt via passlib before storage
- Never include password or password_hash in API responses (use UserResponse schema)
- All password hashes start with `$2b$` prefix (bcrypt format)

### Database Operations
- Always use SQLModel's `select()` for queries, not raw SQL
- Use `session.exec(statement).first()` to get single results
- Always call `session.refresh(obj)` after commit to get DB-assigned values (like IDs)

### API Endpoints
- Use FastAPI's `APIRouter` with prefix and tags for organization
- Always specify `response_model` to ensure proper data serialization
- Use appropriate HTTP status codes (201 for creation, 400 for client errors)
- Validation is automatic via Pydantic schemas

### File Organization
- Routes go in `app/routes/` directory
- Each route module should export a `router` variable
- Register routers in `app/main.py` using `app.include_router()`

## Python Version

This project requires Python 3.13+ (specified in pyproject.toml)
