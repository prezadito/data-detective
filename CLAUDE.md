# CLAUDE.md

This file provides comprehensive guidance to AI assistants (especially Claude) when working with code in this repository.

## Project Overview

**Data Detective Academy** is a comprehensive SQL education platform designed for students in grades 4-8. It's a gamified learning system where students complete SQL challenges, earn points, track progress, and compete on leaderboards. Teachers can manage students, import rosters, view analytics, and track class performance.

**License**: GNU Affero General Public License v3.0 (AGPL-3.0)

**Architecture**: Full-stack monorepo with separate backend and frontend applications

### Key Features

- Interactive SQL challenge system (7 challenges across 3 units)
- JWT-based authentication with refresh tokens
- Progress tracking and completion statistics
- Leaderboard gamification
- Teacher analytics dashboard
- Bulk student import via CSV
- Password reset functionality
- Hint system for challenges

---

## Repository Structure

```
/home/user/data-detective/
├── backend/                        # FastAPI backend (Python 3.13+)
│   ├── app/
│   │   ├── routes/                # API route modules (10 routers)
│   │   ├── main.py               # Application entry point
│   │   ├── database.py           # Database config & session management
│   │   ├── models.py             # SQLModel database models (6 tables)
│   │   ├── schemas.py            # Pydantic request/response schemas (58 schemas)
│   │   ├── auth.py               # Auth utilities (JWT, password hashing)
│   │   └── challenges.py         # Hardcoded challenge definitions
│   ├── tests/                     # Pytest test suite (18 test files)
│   ├── pyproject.toml            # Python dependencies (uv package manager)
│   ├── .env.example              # Environment variables template
│   ├── README.md
│   └── CLAUDE.md                 # Backend-specific documentation
│
├── frontend/                      # React + Vite frontend (TypeScript)
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/               # Page components (Login, Register, Dashboard)
│   │   ├── contexts/            # React contexts (AuthContext)
│   │   ├── services/            # API service layer (ky HTTP client)
│   │   ├── types/               # TypeScript type definitions
│   │   ├── utils/               # Utility functions
│   │   ├── App.tsx              # Root component with routing
│   │   └── main.tsx             # Entry point
│   ├── package.json             # Dependencies (pnpm package manager)
│   ├── vite.config.ts           # Vite configuration (port 3000, API proxy)
│   ├── tsconfig.json            # TypeScript configuration
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   ├── .env.example             # Environment variables template
│   └── README.md
│
├── scripts/                       # Development helper scripts
│   ├── start-backend.sh          # Backend startup script
│   └── start-frontend.sh         # Frontend startup script
│
├── .gitignore
├── LICENSE
├── README.md
└── CLAUDE.md                      # This file
```

---

## Technology Stack

### Backend Stack

- **Language**: Python 3.13+
- **Web Framework**: FastAPI 0.120.4+
- **Database ORM**: SQLModel 0.0.27+ (combines SQLAlchemy + Pydantic)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Authentication**: JWT tokens (python-jose), bcrypt password hashing (passlib)
- **Server**: Uvicorn 0.38.0+
- **Package Manager**: `uv` (modern, fast Python package manager)
- **Database Migrations**: Alembic 1.17.1+
- **Testing**: pytest 8.4.2+, pytest-asyncio, httpx
- **Linting/Formatting**: ruff 0.14.3+

### Frontend Stack

- **Language**: TypeScript 5.9.3 (strict mode enabled)
- **Framework**: React 19.2.0
- **Build Tool**: Vite 7.2.2
- **Routing**: React Router DOM 7.9.6
- **Styling**: Tailwind CSS 4.1.17
- **HTTP Client**: Ky 1.14.0 (modern fetch wrapper)
- **Forms**: React Hook Form 7.66.0 with Zod 4.1.12 validation
- **Package Manager**: pnpm
- **Linting**: ESLint 9.39.1+ with TypeScript ESLint

---

## Development Setup

### Quick Start (Full Stack)

```bash
# Clone repository
git clone <repository-url>
cd data-detective

# Backend setup
cd backend
uv sync --all-extras              # Install dependencies
cp .env.example .env              # Create environment file
# Edit .env: set SECRET_KEY (openssl rand -hex 32)
cd ..

# Frontend setup
cd frontend
pnpm install                      # Install dependencies
cp .env.example .env              # Create environment file
cd ..

# Start both servers (in separate terminals)
# Terminal 1:
cd backend && uvicorn app.main:app --reload  # Port 8000

# Terminal 2:
cd frontend && pnpm dev                      # Port 3000
```

### Backend Development

**Location**: `/home/user/data-detective/backend/`

```bash
# Install dependencies
uv sync --all-extras              # Include dev dependencies
uv sync                           # Production only

# Environment setup
cp .env.example .env
# Generate SECRET_KEY: openssl rand -hex 32
# Edit .env and configure DATABASE_URL, SECRET_KEY, etc.

# Run development server
uvicorn app.main:app --reload     # http://localhost:8000
# API docs: http://localhost:8000/docs

# Run tests
uv run pytest tests/ -v           # All tests
uv run pytest tests/test_auth.py -v  # Specific file
uv run pytest tests/ --cov=app    # With coverage

# Code quality
uv run ruff check .               # Lint
uv run ruff check . --fix         # Auto-fix
uv run ruff format .              # Format

# Database tools
uv run sqlite_web data_detective_academy.db  # Database browser
```

**Important Files**:
- `backend/CLAUDE.md` - Detailed backend documentation
- `backend/.env.example` - Environment variables template
- `backend/pyproject.toml` - Python dependencies and config

### Frontend Development

**Location**: `/home/user/data-detective/frontend/`

```bash
# Install dependencies
pnpm install

# Environment setup
cp .env.example .env
# Configure VITE_API_URL (default: http://localhost:8000)

# Run development server
pnpm dev                          # http://localhost:3000

# Build for production
pnpm build                        # Output: dist/
pnpm preview                      # Preview production build

# Code quality
pnpm lint                         # ESLint
pnpm exec tsc --noEmit            # Type checking
```

**Important Files**:
- `frontend/README.md` - Frontend-specific documentation
- `frontend/.env.example` - Environment variables template
- `frontend/vite.config.ts` - Vite configuration (includes API proxy)

---

## Development Workflow

### Making Changes

1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Backend changes**:
   - Make changes to code in `backend/app/`
   - Write/update tests in `backend/tests/`
   - Run tests: `uv run pytest tests/ -v`
   - Run linter: `uv run ruff check . --fix`
3. **Frontend changes**:
   - Make changes to code in `frontend/src/`
   - Run type checking: `pnpm exec tsc --noEmit`
   - Run linter: `pnpm lint`
4. **Commit changes**: Use descriptive commit messages
5. **Push and create PR**: Follow the project's PR template

### Testing Strategy

**Backend Testing** (18 test files, comprehensive coverage):
- Location: `/home/user/data-detective/backend/tests/`
- Framework: pytest with async support
- In-memory SQLite databases (StaticPool pattern)
- Dependency injection for test database
- Run before committing: `uv run pytest tests/ -v`

**Frontend Testing**:
- No test files currently present (testing framework not yet configured)
- Future: Consider Vitest + React Testing Library

### Code Quality Requirements

**Backend**:
- Python 3.13+ compatible
- Type hints on all functions
- Docstrings on models, schemas, and endpoints
- Ruff linting passes (88-char line length)
- All tests pass

**Frontend**:
- TypeScript strict mode (no type errors)
- ESLint passes
- Functional components with hooks
- Named exports for components

---

## Architecture Patterns

### Backend Architecture

**Pattern**: Modular FastAPI with domain-driven route organization

**Key Patterns**:

1. **Dependency Injection**: FastAPI's `Depends()` for database sessions and auth
   ```python
   def submit_challenge(
       session: Session = Depends(get_session),
       current_user: User = Depends(get_current_user)
   )
   ```

2. **Separation of Models and Schemas**:
   - **Models** (`app/models.py`): Database tables (include sensitive fields)
   - **Schemas** (`app/schemas.py`): API contracts (exclude sensitive data)
   - **Critical**: Always use schemas for API responses, never expose models directly

3. **Router-based Organization**: 10 routers, each handling a domain
   - `auth.py`: Authentication (register, login, password reset)
   - `users.py`: User management
   - `challenges.py`: Challenge browsing
   - `progress.py`: Challenge submission & tracking
   - `leaderboard.py`: Gamification
   - `hints.py`: Hint access
   - `reports.py`: Weekly progress
   - `analytics.py`: Class-wide analytics (teachers)
   - `export.py`: Data export
   - `bulk_import.py`: CSV student import

4. **Lifespan Management**: Modern async context manager (not deprecated startup/shutdown)
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       create_db_and_tables()  # Startup
       yield
       # Cleanup
   ```

5. **Caching Strategy**: In-memory caching for expensive queries
   - Leaderboard: 5-minute TTL
   - Analytics: 1-hour TTL
   - Weekly reports: 1-hour TTL
   - Cache invalidation on data changes

6. **Role-based Access Control**:
   - `get_current_user()`: Authentication required
   - `require_student()`: Student-only endpoints
   - `require_teacher()`: Teacher-only endpoints

### Frontend Architecture

**Pattern**: Component-based React with centralized state management

**Key Patterns**:

1. **Context API for Auth**: Global authentication state
   - `AuthContext.tsx`: Manages login state, tokens, user info
   - LocalStorage for token persistence

2. **Service Layer Pattern**: API calls abstracted into service modules
   - `services/api.ts`: Configured ky HTTP client
   - `services/auth.ts`: Auth-specific API functions
   - Automatic token injection and error handling

3. **Component Organization**:
   - `pages/`: Route-level components
   - `components/ui/`: Reusable UI primitives
   - `components/auth/`: Auth-specific forms

4. **Path Aliases**: `@/*` maps to `./src/*` for clean imports

---

## Database Schema

**File**: `/home/user/data-detective/backend/app/models.py`

### 6 Database Tables

1. **User** (`users`):
   - Fields: id, email (unique), name, role ('student'|'teacher'), password_hash, created_at, last_login
   - Indexes: email

2. **RefreshToken** (`refresh_tokens`):
   - Fields: id, token (unique), user_id (FK), expires_at, revoked, created_at
   - Indexes: token

3. **PasswordResetToken** (`password_reset_tokens`):
   - Fields: id, token (unique), user_id (FK), expires_at, used, created_at
   - Indexes: token

4. **Progress** (`progress`):
   - Fields: id, user_id (FK), unit_id, challenge_id, points_earned, hints_used, query, completed_at
   - Unique constraint: (user_id, unit_id, challenge_id)

5. **Hint** (`hints`):
   - Fields: id, user_id (FK), unit_id, challenge_id, hint_level, accessed_at
   - Tracks every hint access (no unique constraint)

6. **Attempt** (`attempts`):
   - Fields: id, user_id (FK), unit_id, challenge_id, query, is_correct, attempted_at
   - Tracks every attempt (no unique constraint)

### Database Patterns

**SQLModel Dual Nature**:
- Models with `table=True` are both ORM models and validation schemas
- Use separate Pydantic schemas for API to exclude sensitive fields

**Session Management**:
```python
# Dependency injection pattern
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Usage in endpoints
@router.post("/endpoint")
def endpoint(session: Session = Depends(get_session)):
    # session automatically provided and cleaned up
```

**Query Pattern**:
```python
# Always use select(), not raw SQL
statement = select(User).where(User.email == email)
user = session.exec(statement).first()

# After commit, refresh to get DB-assigned values
session.add(user)
session.commit()
session.refresh(user)  # Critical for getting IDs
```

---

## API Endpoints

**Base URL**: `http://localhost:8000`
**Documentation**: `http://localhost:8000/docs` (auto-generated Swagger UI)

### Key Endpoint Groups

**Authentication** (`/auth`):
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Revoke refresh token
- `POST /auth/password-reset-request` - Request password reset
- `POST /auth/password-reset-confirm` - Confirm password reset

**Users** (`/users`):
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users` - List students (teachers only, paginated)
- `GET /users/{user_id}` - Get student details (teachers only)

**Challenges** (`/challenges`):
- `GET /challenges` - Browse all challenges with statistics

**Progress** (`/progress`):
- `POST /progress/submit` - Submit challenge solution (students)
- `GET /progress/me` - Get own progress (students)
- `GET /progress/user/{user_id}` - Get student progress (teachers)

**Leaderboard** (`/leaderboard`):
- `GET /leaderboard` - Top 100 students by points (public, cached)

**Analytics** (`/analytics`):
- `GET /analytics/class` - Class-wide analytics (teachers, cached)

**Export** (`/export`):
- `GET /export/students` - Export students as CSV (teachers)
- `GET /export/progress` - Export progress as CSV (teachers)

**Bulk Import** (`/import`):
- `POST /import/students` - Bulk import students from CSV (teachers)

---

## Important Conventions

### Security Conventions

1. **Password Security**:
   - Bcrypt hashing with passlib (file: `backend/app/auth.py`)
   - Minimum 8 characters required
   - Never return passwords or hashes in API responses
   - Password hashes start with `$2b$` (bcrypt format)

2. **JWT Authentication**:
   - Access tokens: 30 minutes (short-lived)
   - Refresh tokens: 7 days (long-lived, stored in DB)
   - Token payload: email (sub), user_id, role, exp, iat, jti
   - OAuth2PasswordBearer scheme for token extraction

3. **User Enumeration Prevention**:
   - Same error message for invalid email or password
   - Password reset always returns 200 OK regardless of email existence

4. **Role-Based Access Control**:
   - Dependency injection for role checks
   - 403 Forbidden for role violations

### Code Quality Conventions

**Backend**:
- Type hints on all functions
- Docstrings on all endpoints, models, and schemas
- 88-character line length (Ruff)
- Python 3.11+ target for ruff
- Use `select()` for queries, not raw SQL

**Frontend**:
- TypeScript strict mode enabled
- Functional components with hooks
- Named exports for components
- Props via TypeScript interfaces
- Path aliases (`@/`) for imports

### Testing Conventions

**Backend Testing Pattern**:
```python
# Fixture hierarchy: engine → session/client
@pytest.fixture(name="engine")
def engine_fixture():
    """In-memory SQLite with StaticPool"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # Critical for in-memory
    )
    SQLModel.metadata.create_all(engine)
    yield engine

@pytest.fixture(name="client")
def client_fixture(engine):
    """TestClient with dependency overrides"""
    with patch("app.database.create_db_and_tables"):
        from app.main import app
        app.dependency_overrides[get_session] = get_test_session
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
```

**Key Testing Patterns**:
- StaticPool for in-memory SQLite (ensures connection sharing)
- Dependency override pattern for test database
- Patch `create_db_and_tables()` during app import
- Direct database access via session fixture for test setup

### API Design Conventions

1. **Response Models**: Always specify `response_model` on endpoints
2. **HTTP Status Codes**:
   - 201: Resource created
   - 200: Success
   - 400: Client error (validation failure)
   - 401: Unauthorized (auth required)
   - 403: Forbidden (insufficient permissions)
   - 404: Not found
3. **Pagination**: Use `offset` and `limit` query parameters
4. **Error Handling**: HTTPException with detail message

---

## Working with Challenges

**File**: `/home/user/data-detective/backend/app/challenges.py`

Challenges are **hardcoded** in a dictionary (not in database):

```python
CHALLENGES: Dict[Tuple[int, int], Dict[str, Any]] = {
    (1, 1): {  # (unit_id, challenge_id)
        "title": "SELECT All Columns",
        "points": 100,
        "description": "...",
        "sample_solution": "SELECT * FROM users"
    },
    # ... 6 more challenges
}
```

**Challenge Units**:
- Unit 1: SELECT Basics (3 challenges)
- Unit 2: JOINs (2 challenges)
- Unit 3: Aggregations (2 challenges)

**Query Validation**:
- Normalizes queries (lowercase, collapse whitespace, remove comments)
- Exact string matching after normalization
- Function: `validate_query(student_query, expected_query)` in `backend/app/challenges.py:56`

**To add a new challenge**:
1. Add entry to `CHALLENGES` dictionary in `backend/app/challenges.py`
2. No database migration needed (challenges are hardcoded)
3. Update frontend to display new challenge

---

## Environment Variables

### Backend Environment Variables

**File**: `/home/user/data-detective/backend/.env`

```bash
# Security
SECRET_KEY=your-secret-key-here        # Generate: openssl rand -hex 32
ALGORITHM=HS256                        # JWT algorithm

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30         # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS=7            # Refresh token lifetime

# Database
DATABASE_URL=sqlite:///./data_detective_academy.db  # or PostgreSQL URL

# Environment
ENVIRONMENT=development
DEBUG=True
```

**IMPORTANT**: Never commit `.env` file to version control! Use `.env.example` as template.

### Frontend Environment Variables

**File**: `/home/user/data-detective/frontend/.env`

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Application
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=development
```

**Note**: Vite environment variables must be prefixed with `VITE_`

---

## Common Tasks

### Adding a New API Endpoint

1. **Create/update router** in `backend/app/routes/`
2. **Define schema** in `backend/app/schemas.py` (if needed)
3. **Implement endpoint** with dependency injection
4. **Register router** in `backend/app/main.py` (if new router)
5. **Write tests** in `backend/tests/`
6. **Update frontend types** in `frontend/src/types/index.ts`
7. **Create service function** in `frontend/src/services/`

### Adding a New Database Model

1. **Define model** in `backend/app/models.py` with `table=True`
2. **Create schemas** in `backend/app/schemas.py` for API
3. **Run migration** (or rely on SQLModel.metadata.create_all in dev)
4. **Write tests** for new model
5. **Update API endpoints** to use new model

### Debugging Database Issues

```bash
# View database in browser
cd backend
uv run sqlite_web data_detective_academy.db

# Delete database and recreate (dev only!)
rm data_detective_academy.db
uvicorn app.main:app --reload  # Will recreate on startup

# Check database schema
sqlite3 data_detective_academy.db ".schema"
```

### Running Both Servers

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
pnpm dev

# Or use helper scripts:
./scripts/start-backend.sh
./scripts/start-frontend.sh
```

### Viewing API Documentation

Start backend server, then visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Git Workflow

### Branch Naming

- Feature: `feature/description`
- Bug fix: `fix/description`
- Refactor: `refactor/description`

### Commit Messages

Use descriptive commit messages that explain the "why":

```bash
# Good
git commit -m "Add student bulk import endpoint with CSV validation"
git commit -m "Fix leaderboard cache invalidation on progress update"

# Bad
git commit -m "Update code"
git commit -m "Fix bug"
```

### Before Committing

**Backend checklist**:
```bash
cd backend
uv run pytest tests/ -v           # All tests pass
uv run ruff check .               # No linting errors
uv run ruff format .              # Code formatted
```

**Frontend checklist**:
```bash
cd frontend
pnpm exec tsc --noEmit            # No type errors
pnpm lint                         # No linting errors
```

---

## Troubleshooting

### Backend Issues

**"Module not found" errors**:
```bash
cd backend
uv sync --all-extras  # Reinstall dependencies
```

**Database errors**:
```bash
# Delete and recreate (dev only!)
rm data_detective_academy.db
uvicorn app.main:app --reload
```

**Import errors in tests**:
- Ensure `pythonpath = ["."]` in `pyproject.toml`
- Run tests from `backend/` directory

### Frontend Issues

**"Cannot find module" errors**:
```bash
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

**API proxy not working**:
- Check backend is running on port 8000
- Check `vite.config.ts` proxy configuration
- Restart Vite dev server

**Type errors**:
```bash
pnpm exec tsc --noEmit  # Check for type errors
```

---

## Performance Considerations

### Backend Caching

The backend uses in-memory caching for expensive queries:
- **Leaderboard**: 5-minute TTL (file: `backend/app/routes/leaderboard.py:12`)
- **Analytics**: 1-hour TTL (file: `backend/app/routes/analytics.py:16`)
- **Weekly Reports**: 1-hour TTL (file: `backend/app/routes/reports.py:14`)

**Cache Invalidation**: Caches are explicitly invalidated when:
- Progress is submitted (invalidates all 3 caches)
- Bulk import is performed (invalidates all 3 caches)

### Database Performance

**Indexes**:
- `User.email`: Unique index for fast lookups
- `RefreshToken.token`: Unique index for fast validation
- `PasswordResetToken.token`: Unique index for fast validation

**Query Optimization**:
- Use `select()` with specific columns when possible
- Avoid N+1 queries (use joins or batch queries)
- Leverage SQLModel's relationship features

---

## Resources

### Documentation

- **Backend Details**: See `backend/CLAUDE.md` for comprehensive backend documentation
- **Frontend Details**: See `frontend/README.md` for frontend-specific documentation
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLModel Docs**: https://sqlmodel.tiangolo.com/
- **React Docs**: https://react.dev/
- **Vite Docs**: https://vitejs.dev/

### Tools

- **API Testing**: Use Swagger UI at http://localhost:8000/docs
- **Database Browsing**: `uv run sqlite_web data_detective_academy.db`
- **Python Package Manager**: https://docs.astral.sh/uv/

---

## For AI Assistants

When working with this codebase:

1. **Always read backend/CLAUDE.md** for detailed backend patterns
2. **Use type hints** on all new Python functions
3. **Write tests** for new backend endpoints
4. **Use schemas, not models** for API responses
5. **Follow the service layer pattern** in frontend
6. **Use dependency injection** for database sessions and auth
7. **Invalidate caches** when modifying data
8. **Never commit .env files** or expose secrets
9. **Run tests before committing**: `uv run pytest tests/ -v`
10. **Check types before committing**: `pnpm exec tsc --noEmit`

### Common Gotchas

- **Testing**: Always use `StaticPool` for in-memory SQLite tests
- **Database**: Always call `session.refresh(obj)` after commit to get DB-assigned IDs
- **Security**: Never include `password_hash` in API response schemas
- **Caching**: Remember to invalidate caches when modifying relevant data
- **Frontend**: Environment variables must be prefixed with `VITE_`
- **Backend**: Use `select()` for queries, not raw SQL

### Example Code Patterns

**Adding a new endpoint**:
```python
# backend/app/routes/example.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.auth import get_current_user
from app.models import User
from app.schemas import ExampleResponse

router = APIRouter(prefix="/example", tags=["Example"])

@router.get("/", response_model=ExampleResponse)
def get_example(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get example data."""
    # Implementation here
    return ExampleResponse(data="example")
```

**Adding a new React component**:
```tsx
// frontend/src/components/ExampleComponent.tsx
import { useState } from 'react';

interface ExampleComponentProps {
  title: string;
  onAction?: () => void;
}

export function ExampleComponent({ title, onAction }: ExampleComponentProps) {
  const [state, setState] = useState<string>('');

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold">{title}</h2>
      {/* Component implementation */}
    </div>
  );
}
```

---

## Changelog

**Last Updated**: 2025-11-16

This document is maintained to reflect the current state of the codebase. When making significant architectural changes, please update this file accordingly.
