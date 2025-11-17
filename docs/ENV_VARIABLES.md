# Environment Variables Reference

Complete reference for all environment variables used in Data Detective Academy.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Backend Environment Variables](#backend-environment-variables)
  - [Required Variables](#required-backend-variables)
  - [Security Variables](#security-variables)
  - [Database Variables](#database-variables)
  - [Analytics Variables](#analytics-variables)
  - [Optional Variables](#optional-backend-variables)
- [Frontend Environment Variables](#frontend-environment-variables)
  - [Required Variables](#required-frontend-variables)
  - [Optional Variables](#optional-frontend-variables)
- [Environment-Specific Examples](#environment-specific-examples)
- [Security Best Practices](#security-best-practices)
- [How to Generate Secure Values](#how-to-generate-secure-values)
- [Troubleshooting](#troubleshooting)
- [Migration Guide](#migration-guide)

---

## Overview

Data Detective Academy uses environment variables for configuration to:
- Keep secrets out of source code
- Enable different configurations for development, staging, and production
- Follow the [Twelve-Factor App](https://12factor.net/config) methodology

**Important Files:**
- `backend/.env.example` - Development template (committed)
- `backend/.env.production.example` - Production template (committed)
- `backend/.env` - Your actual development config (gitignored, create locally)
- `backend/.env.production` - Your actual production config (gitignored, NEVER commit)
- `frontend/.env.example` - Frontend development template (committed)
- `frontend/.env.production.example` - Frontend production template (committed)

---

## Quick Start

### Development Setup

```bash
# Backend
cd backend
cp .env.example .env
# Generate a secure SECRET_KEY
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
# Edit other values as needed
nano .env

# Frontend
cd frontend
cp .env.example .env
# Edit if needed (defaults are fine for local development)
nano .env
```

### Production Setup

```bash
# Backend
cd backend
cp .env.production.example .env.production
# Generate secure values
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.production
# Edit all required variables
nano .env.production

# Frontend
cd frontend
cp .env.production.example .env.production
# Edit all required variables
nano .env.production
```

---

## Backend Environment Variables

### Required Backend Variables

These variables **MUST** be set in production:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (32+ bytes) | `a1b2c3d4e5f6...` (64 chars) |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host/db` |
| `ENVIRONMENT` | Environment name | `production` |
| `DEBUG` | Debug mode (MUST be False in prod) | `False` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `https://example.com,https://www.example.com` |
| `FRONTEND_URL` | Frontend URL for emails/redirects | `https://example.com` |

**Example:**
```bash
SECRET_KEY=f4e3d2c1b0a9876543210abcdef1234567890abcdef1234567890abcdef12345
DATABASE_URL=postgresql://datadetective:secure_password@db.example.com:5432/datadetective_prod
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://datadetective.academy,https://www.datadetective.academy
FRONTEND_URL=https://datadetective.academy
```

### Security Variables

JWT token configuration:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | None | JWT signing key - **MUST be unique and secret** |
| `ALGORITHM` | No | `HS256` | JWT algorithm (HS256 recommended) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime (30 min recommended) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime (7 days recommended) |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | No | `1` | Password reset token lifetime |

**Security Notes:**
- `SECRET_KEY` should be at least 32 bytes (64 hex characters)
- Never reuse SECRET_KEY across environments
- Rotate SECRET_KEY periodically (invalidates all existing tokens)
- Use HS256 algorithm unless you have specific requirements for RS256

### Database Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | `sqlite:///./data_detective_academy.db` | Database connection string |
| `DB_ECHO` | No | `false` | Log all SQL queries (set to `false` in production) |
| `DB_POOL_SIZE` | No | `5` | PostgreSQL connection pool size |
| `DB_MAX_OVERFLOW` | No | `10` | PostgreSQL max overflow connections |

**Database URL Formats:**

**SQLite (Development Only):**
```bash
DATABASE_URL=sqlite:///./data_detective_academy.db
```

**PostgreSQL (Production):**
```bash
# Basic format
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# With SSL (recommended for production)
DATABASE_URL=postgresql://username:password@hostname:port/database_name?sslmode=require

# AWS RDS example
DATABASE_URL=postgresql://admin:SecurePass123@myinstance.abc123.us-east-1.rds.amazonaws.com:5432/datadetective

# Digital Ocean example
DATABASE_URL=postgresql://doadmin:SecurePass123@db-postgresql-nyc1-12345.ondigitalocean.com:25060/datadetective?sslmode=require

# Supabase example
DATABASE_URL=postgresql://postgres:SecurePass123@db.abcdefghijk.supabase.co:5432/postgres

# Heroku (auto-provided)
DATABASE_URL=postgres://user:pass@ec2-x-x-x-x.compute-1.amazonaws.com:5432/dbname
```

**Connection Pool Settings:**
- `DB_POOL_SIZE=5`: Good for small apps (< 100 concurrent users)
- `DB_POOL_SIZE=10`: Medium apps (100-500 concurrent users)
- `DB_POOL_SIZE=20`: Large apps (500+ concurrent users)
- Adjust based on your database server's `max_connections` setting

### Analytics Variables

Optional analytics configuration (Plausible or Google Analytics):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANALYTICS_ENABLED` | No | `false` | Enable analytics tracking |
| `ANALYTICS_PROVIDER` | No | `plausible` | Analytics provider: `plausible` or `google` |
| `ANALYTICS_DOMAIN` | No | None | Your domain name |
| `ANALYTICS_SCRIPT_URL` | No | `https://plausible.io/js/script.js` | Plausible script URL |
| `ANALYTICS_ID` | No | None | Google Analytics Measurement ID (G-XXXXXXXXXX) |

**Plausible Analytics (Privacy-Friendly, Recommended):**
```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=datadetective.academy
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js
```

**Google Analytics:**
```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=google
ANALYTICS_DOMAIN=datadetective.academy
ANALYTICS_ID=G-XXXXXXXXXX
```

### Optional Backend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `SENTRY_DSN` | No | None | Sentry error tracking DSN |

**Example:**
```bash
LOG_LEVEL=WARNING
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/123456
```

---

## Frontend Environment Variables

All Vite environment variables must be prefixed with `VITE_` to be exposed to the browser.

### Required Frontend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.datadetective.academy` |
| `VITE_ENV` | Environment name | `production` |

**Example:**
```bash
VITE_API_URL=https://api.datadetective.academy
VITE_ENV=production
```

### Optional Frontend Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_APP_NAME` | `Data Detective` | Application name |
| `VITE_APP_VERSION` | `1.0.0` | Application version |
| `VITE_SENTRY_DSN` | None | Sentry error tracking DSN |
| `VITE_ANALYTICS_ENABLED` | `false` | Enable analytics tracking |
| `VITE_ANALYTICS_PROVIDER` | `plausible` | Analytics provider |
| `VITE_ANALYTICS_DOMAIN` | None | Analytics domain |

**Example:**
```bash
VITE_APP_NAME=Data Detective Academy
VITE_APP_VERSION=1.0.0
VITE_SENTRY_DSN=https://def456@o123456.ingest.sentry.io/654321
VITE_ANALYTICS_ENABLED=true
VITE_ANALYTICS_PROVIDER=plausible
VITE_ANALYTICS_DOMAIN=datadetective.academy
```

---

## Environment-Specific Examples

### Development Environment

**Backend (`backend/.env`):**
```bash
# Development uses SQLite and relaxed security
SECRET_KEY=dev-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# SQLite for local development
DATABASE_URL=sqlite:///./data_detective_academy.db

# Development settings
ENVIRONMENT=development
DEBUG=True
DB_ECHO=True

# Local CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
FRONTEND_URL=http://localhost:3000

# Analytics disabled in dev
ANALYTICS_ENABLED=false
```

**Frontend (`frontend/.env`):**
```bash
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=development
```

### Staging Environment

**Backend (`backend/.env.staging`):**
```bash
# Staging uses PostgreSQL and production-like settings
SECRET_KEY=staging-secret-key-different-from-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL staging database
DATABASE_URL=postgresql://datadetective_staging:staging_password@db-staging.example.com:5432/datadetective_staging?sslmode=require

# Staging settings
ENVIRONMENT=staging
DEBUG=False
DB_ECHO=False
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Staging CORS
ALLOWED_ORIGINS=https://staging.datadetective.academy
FRONTEND_URL=https://staging.datadetective.academy

# Analytics enabled with test domain
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=staging.datadetective.academy
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js

# Logging
LOG_LEVEL=INFO
```

**Frontend (`frontend/.env.staging`):**
```bash
VITE_API_URL=https://api-staging.datadetective.academy
VITE_APP_NAME=Data Detective [STAGING]
VITE_APP_VERSION=1.0.0
VITE_ENV=staging
```

### Production Environment

**Backend (`backend/.env.production`):**
```bash
# PRODUCTION - KEEP THIS FILE SECURE AND NEVER COMMIT

# Strong unique secret key (generate with: openssl rand -hex 32)
SECRET_KEY=your-production-secret-key-64-characters-long-hex-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL production database
DATABASE_URL=postgresql://datadetective_prod:super_secure_password@db-prod.example.com:5432/datadetective_prod?sslmode=require

# Production settings
ENVIRONMENT=production
DEBUG=False
DB_ECHO=False
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Production CORS - only allow your domains
ALLOWED_ORIGINS=https://datadetective.academy,https://www.datadetective.academy
FRONTEND_URL=https://datadetective.academy

# Analytics
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=datadetective.academy
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js

# Monitoring
LOG_LEVEL=WARNING
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**Frontend (`frontend/.env.production`):**
```bash
VITE_API_URL=https://api.datadetective.academy
VITE_APP_NAME=Data Detective Academy
VITE_APP_VERSION=1.0.0
VITE_ENV=production
VITE_ANALYTICS_ENABLED=true
VITE_ANALYTICS_PROVIDER=plausible
VITE_ANALYTICS_DOMAIN=datadetective.academy
VITE_SENTRY_DSN=https://your-frontend-sentry-dsn@sentry.io/frontend-project-id
```

---

## Security Best Practices

### 1. Secret Key Management

**DO:**
- ✅ Generate unique `SECRET_KEY` for each environment
- ✅ Use cryptographically secure random generation
- ✅ Store in environment variables or secure secret managers
- ✅ Rotate keys periodically (every 90 days recommended)
- ✅ Use minimum 32 bytes (64 hex characters)

**DON'T:**
- ❌ Never commit `.env` files with real secrets
- ❌ Don't reuse SECRET_KEY across environments
- ❌ Don't use simple or guessable values
- ❌ Don't share SECRET_KEY in chat, email, or documentation

### 2. Database Security

**DO:**
- ✅ Use PostgreSQL in production (not SQLite)
- ✅ Enable SSL/TLS for database connections (`?sslmode=require`)
- ✅ Use strong database passwords (16+ characters)
- ✅ Restrict database access by IP address
- ✅ Use separate database users for different environments
- ✅ Enable database backups

**DON'T:**
- ❌ Don't use default passwords
- ❌ Don't expose database ports to public internet
- ❌ Don't use SQLite in production (not suitable for concurrent access)
- ❌ Don't disable SSL in production

### 3. CORS Configuration

**DO:**
- ✅ Specify exact production domains in `ALLOWED_ORIGINS`
- ✅ Include both www and non-www variants if needed
- ✅ Use HTTPS URLs only in production
- ✅ Test CORS configuration before deploying

**DON'T:**
- ❌ Never use `*` (wildcard) in production
- ❌ Don't include development URLs in production CORS
- ❌ Don't allow HTTP origins in production

### 4. Debug Mode

**DO:**
- ✅ Set `DEBUG=False` in production
- ✅ Set `DB_ECHO=False` in production (prevent SQL logging)
- ✅ Use appropriate `LOG_LEVEL` (WARNING or ERROR in production)

**DON'T:**
- ❌ Never set `DEBUG=True` in production (exposes stack traces)
- ❌ Don't log sensitive data (passwords, tokens)

### 5. File Permissions

On production servers, protect your `.env.production` file:

```bash
# Set restrictive permissions (only owner can read)
chmod 600 /path/to/.env.production

# Ensure correct ownership
chown appuser:appuser /path/to/.env.production
```

---

## How to Generate Secure Values

### SECRET_KEY Generation

**Method 1: OpenSSL (Recommended)**
```bash
openssl rand -hex 32
```
Output: `a1b2c3d4e5f6...` (64 characters)

**Method 2: Python**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Method 3: Node.js**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Database Password Generation

**Method 1: OpenSSL**
```bash
openssl rand -base64 24
```
Output: 32-character random string

**Method 2: Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Verification

**Check SECRET_KEY length:**
```bash
echo -n "your-secret-key" | wc -c
# Should be 64 or more
```

---

## Troubleshooting

### Backend Issues

**Problem: "SECRET_KEY not set" error**
- **Solution**: Ensure `.env` file exists and contains `SECRET_KEY=...`
- **Check**: Run `cat backend/.env | grep SECRET_KEY` to verify

**Problem: "Could not connect to database"**
- **Solution**: Verify `DATABASE_URL` is correct
- **Check**: Test PostgreSQL connection: `psql "$DATABASE_URL"`
- **Common Issue**: Firewall blocking port 5432

**Problem: CORS errors in browser**
- **Solution**: Add your frontend domain to `ALLOWED_ORIGINS`
- **Check**: `ALLOWED_ORIGINS=https://yourdomain.com` (no trailing slash)
- **Debug**: Check browser console for exact origin being blocked

**Problem: Database connection pool exhausted**
- **Solution**: Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
- **Check**: Monitor active database connections
- **Alternative**: Scale horizontally (add more backend instances)

**Problem: SQL queries logged in production**
- **Solution**: Set `DB_ECHO=False` in `.env.production`

### Frontend Issues

**Problem: "Cannot connect to API" error**
- **Solution**: Verify `VITE_API_URL` matches your backend URL
- **Check**: Open `https://your-api-url/health` in browser
- **Common Issue**: Missing HTTPS or wrong port

**Problem: Environment variables not working**
- **Solution**: Ensure variables are prefixed with `VITE_`
- **Rebuild**: Run `pnpm build` after changing `.env` files
- **Note**: Vite only reads `.env` at build time, not runtime

**Problem: Analytics not tracking**
- **Solution**: Verify `VITE_ANALYTICS_ENABLED=true`
- **Check**: Browser console for analytics script loading
- **Common Issue**: Ad blockers blocking analytics scripts

### Environment Variable Not Loading

**Check file location:**
```bash
# Backend
ls -la backend/.env
cat backend/.env

# Frontend
ls -la frontend/.env
cat frontend/.env
```

**Check variable names:**
- Backend: No prefix required
- Frontend: MUST have `VITE_` prefix

**Check for typos:**
```bash
# Common typos
DATABASE_URL (correct)
DATABSE_URL (wrong)
DATABASE_URl (wrong)

VITE_API_URL (correct)
API_URL (wrong - missing VITE_)
```

---

## Migration Guide

### From Development to Production

**Step 1: Create Production Environment Files**
```bash
# Backend
cd backend
cp .env.production.example .env.production

# Frontend
cd frontend
cp .env.production.example .env.production
```

**Step 2: Generate Secure Secrets**
```bash
# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY"

# Generate database password
DB_PASS=$(openssl rand -base64 24)
echo "Database Password: $DB_PASS"
```

**Step 3: Configure Database**
- Create PostgreSQL database and user
- Note connection details (host, port, database name)
- Build `DATABASE_URL` string

**Step 4: Update Backend `.env.production`**
```bash
# Edit file
nano backend/.env.production

# Required changes:
# 1. SECRET_KEY - paste generated value
# 2. DATABASE_URL - paste PostgreSQL connection string
# 3. ENVIRONMENT=production
# 4. DEBUG=False
# 5. ALLOWED_ORIGINS - add your production domains
# 6. FRONTEND_URL - add your frontend domain
```

**Step 5: Update Frontend `.env.production`**
```bash
# Edit file
nano frontend/.env.production

# Required changes:
# 1. VITE_API_URL - your backend API URL
# 2. VITE_ENV=production
```

**Step 6: Test Locally**
```bash
# Backend - test with production config
cd backend
cp .env.production .env
uvicorn app.main:app --reload
# Verify: http://localhost:8000/health
# Verify: http://localhost:8000/api/info shows "production"

# Frontend - build and preview
cd frontend
pnpm build
pnpm preview
# Verify: http://localhost:4173
```

**Step 7: Deploy**
- Upload files to server or push to hosting platform
- Set environment variables (via platform dashboard or `.env.production`)
- Run database migrations if needed
- Start application
- Monitor logs for errors

### From SQLite to PostgreSQL

**Step 1: Export SQLite Data**
```bash
# Dump SQLite to SQL
sqlite3 data_detective_academy.db .dump > backup.sql
```

**Step 2: Create PostgreSQL Database**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE datadetective_prod;
CREATE USER datadetective_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE datadetective_prod TO datadetective_user;
\q
```

**Step 3: Update DATABASE_URL**
```bash
# In .env.production
DATABASE_URL=postgresql://datadetective_user:secure_password@localhost:5432/datadetective_prod
```

**Step 4: Initialize Schema**
```bash
# Run backend (creates tables automatically via SQLModel)
cd backend
uvicorn app.main:app --reload
```

**Step 5: Import Data (if needed)**
```bash
# Manual import or use migration tool
# Note: SQLite dump may need conversion for PostgreSQL
```

---

## Additional Resources

- [Twelve-Factor App Config](https://12factor.net/config)
- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [OWASP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## Changelog

**Version 1.0.0** - 2025-11-17
- Initial comprehensive environment variables documentation
- Backend and frontend variable reference
- Security best practices
- Migration guide
- Troubleshooting section
