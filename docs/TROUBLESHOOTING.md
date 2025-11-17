# Troubleshooting Guide

Common issues and solutions for Data Detective Academy.

## Table of Contents

- [Backend Issues](#backend-issues)
  - [Installation & Setup](#backend-installation--setup)
  - [Database](#database-issues)
  - [Authentication](#authentication-issues)
  - [API Errors](#api-errors)
- [Frontend Issues](#frontend-issues)
  - [Installation & Setup](#frontend-installation--setup)
  - [Build Errors](#build-errors)
  - [Runtime Errors](#runtime-errors)
  - [API Connection](#api-connection-issues)
- [Testing Issues](#testing-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Getting Help](#getting-help)

---

## Backend Issues

### Backend Installation & Setup

#### Issue: `uv: command not found`

**Problem:** uv package manager not installed or not in PATH.

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

---

#### Issue: `Python version mismatch`

**Problem:** Python 3.13+ required but different version installed.

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.13 (Ubuntu/Debian)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# Use pyenv for version management (recommended)
curl https://pyenv.run | bash
pyenv install 3.13
pyenv local 3.13
```

---

#### Issue: `uv sync` fails with dependency conflicts

**Problem:** Dependency resolution errors.

**Solution:**
```bash
# Clear uv cache
uv cache clean

# Remove lock file and retry
rm uv.lock
uv sync --all-extras

# If still failing, check pyproject.toml for conflicting versions
# Update dependencies to compatible versions
```

---

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Problem:** Python can't find the app module.

**Solution:**
```bash
# Ensure you're in the backend directory
cd backend

# Run from project root using module notation
uv run python -m app.main

# Or use uvicorn directly
uv run uvicorn app.main:app --reload

# Check pyproject.toml has:
# [tool.pytest.ini_options]
# pythonpath = ["."]
```

---

### Database Issues

#### Issue: `sqlite3.OperationalError: unable to open database file`

**Problem:** SQLite database file permissions or path issues.

**Solution:**
```bash
# Check current directory
pwd  # Should be in /backend

# Verify database path in .env
cat .env | grep DATABASE_URL
# Should be: DATABASE_URL=sqlite:///./data_detective_academy.db

# Create database manually if needed
uv run python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Check file permissions
ls -la data_detective_academy.db
# If permission issues:
chmod 644 data_detective_academy.db
```

---

#### Issue: `asyncpg.exceptions.InvalidCatalogNameError` (PostgreSQL)

**Problem:** Database doesn't exist.

**Solution:**
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE datadetective;
\q

# Update .env with correct DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost/datadetective

# Run migrations
uv run alembic upgrade head
# OR create tables directly
uv run python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

---

#### Issue: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked`

**Problem:** Multiple processes accessing SQLite simultaneously.

**Solution:**
```bash
# Stop all running instances
pkill -f uvicorn

# For development, use a single worker
uvicorn app.main:app --reload --workers 1

# For production, use PostgreSQL instead of SQLite
```

---

#### Issue: Database schema out of sync

**Problem:** Code expects different schema than database has.

**Solution:**
```bash
# Option 1: Delete database and recreate (DEVELOPMENT ONLY)
rm data_detective_academy.db
uv run python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Option 2: Use Alembic migrations
uv run alembic revision --autogenerate -m "Update schema"
uv run alembic upgrade head

# Option 3: Manually inspect differences
sqlite3 data_detective_academy.db .schema
```

---

### Authentication Issues

#### Issue: `401 Unauthorized` on protected endpoints

**Problem:** Invalid or missing JWT token.

**Solution:**
```bash
# Test authentication flow
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test123!"}'

# 2. Extract access_token from response
# 3. Use token in Authorization header
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Check token expiration (default: 30 minutes)
# If expired, use refresh token to get new access token
```

**Frontend:**
```javascript
// Check if token is stored
console.log(localStorage.getItem('access_token'));

// Check if token is being sent
// Open browser DevTools > Network > Request Headers
// Should see: Authorization: Bearer ...
```

---

#### Issue: `Could not validate credentials`

**Problem:** JWT secret key mismatch or token corruption.

**Solution:**
```bash
# Backend: Verify SECRET_KEY is set
grep SECRET_KEY backend/.env

# Generate new SECRET_KEY if needed
openssl rand -hex 32

# Update .env
SECRET_KEY=your-new-secret-key

# Restart backend
# Users will need to re-login
```

---

#### Issue: Password reset token doesn't work

**Problem:** Token expired, already used, or invalid.

**Solution:**
```bash
# Check token expiration (default: 1 hour)
# Token must be used within 1 hour of generation

# Verify token in database
sqlite3 data_detective_academy.db
SELECT * FROM password_reset_tokens WHERE token = 'your-token';

# Check if token is marked as used
# Check if expires_at is in the past

# Generate new reset token if needed
```

---

### API Errors

#### Issue: `422 Unprocessable Entity` on API requests

**Problem:** Request validation failed.

**Solution:**
```bash
# Check request body matches schema
# Example: POST /auth/register
{
  "email": "user@example.com",    # Must be valid email
  "name": "User Name",             # Required
  "password": "Password123!",      # Min 8 characters
  "role": "student"                # Must be "student" or "teacher"
}

# Check API docs for exact schema
# http://localhost:8000/docs

# Read error response for details
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

#### Issue: `500 Internal Server Error`

**Problem:** Unhandled exception in backend.

**Solution:**
```bash
# Check backend logs
uv run uvicorn app.main:app --reload

# Look for stack trace in terminal
# Common causes:
# - Database connection issues
# - Missing environment variables
# - Unhandled null/None values

# Enable debug mode for detailed errors (DEVELOPMENT ONLY)
# In .env:
DEBUG=True

# Check for recent code changes that might have introduced bugs
```

---

## Frontend Issues

### Frontend Installation & Setup

#### Issue: `pnpm: command not found`

**Problem:** pnpm not installed.

**Solution:**
```bash
# Install pnpm
npm install -g pnpm

# Verify installation
pnpm --version

# Alternative: Use corepack (Node.js 16.13+)
corepack enable
corepack prepare pnpm@latest --activate
```

---

#### Issue: `EACCES: permission denied` during `pnpm install`

**Problem:** npm global directory permission issues.

**Solution:**
```bash
# Option 1: Fix npm permissions (recommended)
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Option 2: Use sudo (not recommended)
sudo pnpm install

# Option 3: Change npm directory ownership
sudo chown -R $(whoami) ~/.npm
```

---

#### Issue: Module not found after `pnpm install`

**Problem:** Dependencies not properly installed or cached.

**Solution:**
```bash
# Clear pnpm cache and node_modules
rm -rf node_modules
pnpm store prune

# Reinstall dependencies
pnpm install

# If using path aliases, check tsconfig.json and vite.config.ts
# tsconfig.json should have:
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}

# vite.config.ts should have:
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src')
  }
}
```

---

### Build Errors

#### Issue: TypeScript errors during build

**Problem:** Type checking failures.

**Solution:**
```bash
# Run type check to see all errors
pnpm exec tsc --noEmit

# Common fixes:
# 1. Missing type definitions
pnpm add -D @types/package-name

# 2. Incorrect type usage
# Fix type errors in reported files

# 3. Skip lib check (temporary workaround)
# In tsconfig.json:
{
  "compilerOptions": {
    "skipLibCheck": true
  }
}
```

---

#### Issue: `ReferenceError: process is not defined`

**Problem:** Using Node.js globals in browser code.

**Solution:**
```typescript
// Don't use process.env directly in frontend
// Bad:
const apiUrl = process.env.VITE_API_URL;

// Good:
const apiUrl = import.meta.env.VITE_API_URL;

// For build scripts, ensure proper Vite environment
```

---

#### Issue: `Failed to resolve import` errors

**Problem:** Import path issues or missing dependencies.

**Solution:**
```bash
# Check if dependency is installed
pnpm list package-name

# Install if missing
pnpm add package-name

# For path alias issues, verify:
# 1. tsconfig.json paths
# 2. vite.config.ts resolve.alias
# 3. Import uses correct alias: import x from '@/...'

# Restart dev server after config changes
```

---

### Runtime Errors

#### Issue: `Uncaught TypeError: Cannot read property of undefined`

**Problem:** Accessing property on null/undefined value.

**Solution:**
```typescript
// Use optional chaining
const userName = user?.name;

// Use nullish coalescing
const points = user?.points ?? 0;

// Check before accessing
if (user && user.name) {
  console.log(user.name);
}

// Type guards
function isUser(value: unknown): value is User {
  return typeof value === 'object' && value !== null && 'id' in value;
}

if (isUser(data)) {
  console.log(data.name); // Safe
}
```

---

#### Issue: `Network Error` or `Failed to fetch`

**Problem:** API connection issues.

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify API URL in frontend .env
cat frontend/.env
# Should be: VITE_API_URL=http://localhost:8000

# Check CORS configuration in backend
# backend/app/main.py should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check browser console for CORS errors
# Open DevTools > Console
```

---

### API Connection Issues

#### Issue: API requests timeout

**Problem:** Backend not responding or network issues.

**Solution:**
```bash
# Test backend directly
curl -v http://localhost:8000/challenges

# Check backend logs for errors
# Terminal running uvicorn

# Increase timeout in frontend (ky config)
// src/services/api.ts
export const api = ky.create({
  timeout: 60000, // Increase to 60 seconds
});

# Check for slow database queries
# Enable SQL logging in backend
```

---

#### Issue: 401 errors despite valid login

**Problem:** Token not being sent or stored correctly.

**Solution:**
```javascript
// Check localStorage
console.log(localStorage.getItem('access_token'));

// Check if token is being sent in requests
// Browser DevTools > Network > Request > Headers
// Should see: Authorization: Bearer ...

// Verify ky hooks are configured
// src/services/api.ts
hooks: {
  beforeRequest: [
    (request) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        request.headers.set('Authorization', `Bearer ${token}`);
      }
    }
  ]
}

// Check token hasn't expired
// Tokens expire after 30 minutes by default
// Implement token refresh logic
```

---

## Testing Issues

### Backend Testing Issues

#### Issue: Tests fail with database errors

**Problem:** Test database not properly isolated.

**Solution:**
```python
# Ensure using StaticPool for in-memory SQLite
# tests/conftest.py
from sqlalchemy.pool import StaticPool

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # Critical for in-memory
    )
    SQLModel.metadata.create_all(engine)
    yield engine

# Clear data between tests
@pytest.fixture(autouse=True)
def clear_database(engine):
    yield
    for table in reversed(SQLModel.metadata.sorted_tables):
        engine.execute(table.delete())
```

---

#### Issue: Import errors in tests

**Problem:** Module path issues.

**Solution:**
```bash
# Ensure pyproject.toml has:
[tool.pytest.ini_options]
pythonpath = ["."]

# Run tests from backend directory
cd backend
uv run pytest tests/

# Not from parent directory
# cd data-detective && pytest backend/tests/  # ❌
```

---

### Frontend Testing Issues

#### Issue: `ReferenceError: localStorage is not defined`

**Problem:** localStorage not available in test environment.

**Solution:**
```typescript
// Mock localStorage in test setup
// src/test/setup.ts
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

global.localStorage = localStorageMock as any;

// Or use vitest environment
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts']
  }
});
```

---

#### Issue: E2E tests fail with timeout

**Problem:** Elements not loading in time.

**Solution:**
```typescript
// Increase timeout
// playwright.config.ts
export default defineConfig({
  timeout: 60000, // 60 seconds

  use: {
    actionTimeout: 10000,
  },
});

// Use waitFor helpers
await page.waitForSelector('text=Dashboard');
await page.waitForLoadState('networkidle');

// Check backend is running
// E2E tests require backend on http://localhost:8000
```

---

## Performance Issues

### Backend Performance

#### Issue: Slow API responses

**Problem:** Database queries not optimized.

**Solution:**
```python
# Add indexes to frequently queried columns
# In models.py
class User(SQLModel, table=True):
    email: str = Field(index=True)  # Add index

# Use select specific columns instead of SELECT *
statement = select(User.id, User.name).where(User.role == "student")

# Implement pagination
statement = select(User).offset(offset).limit(limit)

# Use caching for expensive queries
# See backend/app/routes/leaderboard.py for example

# Monitor slow queries
# Enable SQL logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

### Frontend Performance

#### Issue: Slow page load times

**Problem:** Large bundle size or unoptimized assets.

**Solution:**
```bash
# Analyze bundle size
pnpm build:analyze

# Lazy load routes
// App.tsx
const TeacherDashboard = lazy(() => import('./pages/teacher/Dashboard'));

# Optimize images
# - Compress images before adding to project
# - Use appropriate formats (WebP, AVIF)
# - Implement lazy loading for images

# Split code chunks
# vite.config.ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        router: ['react-router-dom'],
      }
    }
  }
}
```

---

## Deployment Issues

### Issue: Environment variables not working in production

**Problem:** .env file not loaded or wrong variables.

**Solution:**
```bash
# Backend: Ensure .env is in correct location
ls -la /home/datadetective/app/backend/.env

# Frontend: Ensure variables are prefixed with VITE_
# In .env.production:
VITE_API_URL=https://api.yourdomain.com  # ✓
API_URL=https://api.yourdomain.com       # ✗ Won't work

# Rebuild frontend after changing env vars
pnpm build

# For systemd service, use EnvironmentFile
[Service]
EnvironmentFile=/path/to/.env
```

---

### Issue: 502 Bad Gateway (Nginx)

**Problem:** Nginx can't connect to backend.

**Solution:**
```bash
# Check backend is running
sudo systemctl status datadetective-backend
curl http://localhost:8000/health

# Check Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Verify upstream configuration
upstream backend {
    server 127.0.0.1:8000;  # Correct port?
}

# Restart services
sudo systemctl restart datadetective-backend
sudo systemctl reload nginx
```

---

### Issue: Static files 404 in production

**Problem:** Frontend build files not found.

**Solution:**
```bash
# Verify build files exist
ls -la /var/www/datadetective/

# Check Nginx root directive
server {
    root /var/www/datadetective;  # Correct path?
    index index.html;
}

# Ensure SPA routing is configured
location / {
    try_files $uri $uri/ /index.html;
}

# Check file permissions
sudo chown -R www-data:www-data /var/www/datadetective
sudo chmod -R 755 /var/www/datadetective
```

---

## Getting Help

If you can't find a solution here:

1. **Search existing issues** on GitHub
2. **Check documentation:**
   - [Architecture Guide](ARCHITECTURE.md)
   - [API Reference](API.md)
   - [Deployment Guide](DEPLOYMENT.md)
3. **Enable debug logging:**
   ```bash
   # Backend
   DEBUG=True in .env

   # Frontend
   console.log() for debugging
   ```
4. **Create a GitHub issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages/stack traces
   - Environment details (OS, versions, etc.)
5. **Ask in GitHub Discussions** for general questions

### Useful Debugging Commands

**Backend:**
```bash
# Check Python version
python3 --version

# Check installed packages
uv pip list

# Run with verbose logging
uvicorn app.main:app --reload --log-level debug

# Test database connection
python3 -c "from app.database import engine; print(engine)"
```

**Frontend:**
```bash
# Check Node version
node --version

# Check pnpm version
pnpm --version

# Clear cache and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Build with verbose output
pnpm build --debug
```

**General:**
```bash
# Check ports in use
sudo lsof -i :3000
sudo lsof -i :8000

# Check disk space
df -h

# Check memory usage
free -h

# Check logs
sudo journalctl -u datadetective-backend -n 100
```

---

## Common Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `ECONNREFUSED` | Can't connect to backend | Start backend server |
| `CORS policy` | CORS not configured | Update backend CORS settings |
| `Module not found` | Missing dependency | Run `pnpm install` or `uv sync` |
| `401 Unauthorized` | Auth token missing/invalid | Re-login to get new token |
| `422 Unprocessable` | Validation failed | Check request body format |
| `500 Internal Error` | Backend exception | Check backend logs |
| `EADDRINUSE` | Port already in use | Kill process or use different port |
| `sqlite3.OperationalError` | Database locked/missing | Check database file permissions |

---

*Last updated: 2025-11-17*
