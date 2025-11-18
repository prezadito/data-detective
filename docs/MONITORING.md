# Monitoring and Logging Guide

Complete guide for monitoring, logging, and error tracking in Data Detective Academy.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Sentry Setup](#sentry-setup)
- [Logging Guide](#logging-guide)
- [Uptime Monitoring](#uptime-monitoring)
- [Performance Monitoring](#performance-monitoring)
- [Alert Configuration](#alert-configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

Data Detective Academy uses a comprehensive monitoring stack to catch errors before users report them, understand system behavior, and maintain high availability.

### Monitoring Components

```
┌─────────────────────────────────────────────────────────────┐
│                     MONITORING STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Backend (FastAPI)          Frontend (React)                │
│  • Sentry SDK               • Sentry SDK                    │
│  • Python Logging           • Error Boundary                │
│  • Request Logging          • API Breadcrumbs               │
│  • Global Exception         • Session Replay                │
│    Handler                  • Performance                   │
│                               Tracking                       │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │           Sentry.io (Cloud)              │              │
│  │  • Error Tracking                        │              │
│  │  • Performance Monitoring (APM)          │              │
│  │  • Session Replay                        │              │
│  │  • Alert Rules                           │              │
│  └──────────────────────────────────────────┘              │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │        UptimeRobot (Free Tier)           │              │
│  │  • Health Endpoint Monitoring            │              │
│  │  • 5-minute Interval Checks              │              │
│  │  • Email Alerts                          │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### What We Track

**Backend:**
- ✅ All HTTP requests with timing and status codes
- ✅ User authentication events (login, logout, registration)
- ✅ Challenge submissions (successful and failed)
- ✅ Database errors
- ✅ Unhandled exceptions

**Frontend:**
- ✅ JavaScript errors and React component errors
- ✅ API call failures with full context
- ✅ User session replays (on errors)
- ✅ Page load performance
- ✅ Route change performance

**Infrastructure:**
- ✅ Application uptime (99.9% target)
- ✅ Health endpoint response time
- ✅ Database connectivity

---

## Quick Start

### 1. Install Dependencies

**Backend:**
```bash
cd backend
uv sync  # Installs sentry-sdk[fastapi]>=2.0.0
```

**Frontend:**
```bash
cd frontend
pnpm install  # Installs @sentry/react@^8.0.0
```

### 2. Get Sentry DSN Keys

1. Create free account at [https://sentry.io](https://sentry.io)
2. Create **TWO projects**:
   - **Backend** project (platform: Python/FastAPI)
   - **Frontend** project (platform: JavaScript/React)
3. Copy the DSN from each project settings

### 3. Configure Environment Variables

**Backend** (`backend/.env`):
```bash
# Copy from .env.example
cp .env.example .env

# Edit .env and add:
SENTRY_DSN=https://YOUR_BACKEND_KEY@o123456.ingest.sentry.io/7654321
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
LOG_LEVEL=INFO
LOG_FORMAT=text
```

**Frontend** (`frontend/.env`):
```bash
# Copy from .env.example
cp .env.example .env

# Edit .env and add:
VITE_SENTRY_DSN=https://YOUR_FRONTEND_KEY@o123456.ingest.sentry.io/7654322
VITE_SENTRY_ENVIRONMENT=development
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 4. Test Integration

**Backend Test:**
```bash
cd backend
uvicorn app.main:app --reload

# In another terminal, trigger a test error:
curl http://localhost:8000/api/info
# Check logs for "Sentry initialized" message
```

**Frontend Test:**
```bash
cd frontend
pnpm dev

# Open browser console, should see:
# "Sentry initialized for environment: development"
```

### 5. Verify in Sentry Dashboard

1. Go to https://sentry.io/organizations/your-org/issues/
2. You should see events appearing
3. Check that both backend and frontend projects are receiving data

---

## Sentry Setup

### Creating Sentry Account (Free Tier)

1. **Sign Up:**
   - Visit [https://sentry.io/signup/](https://sentry.io/signup/)
   - Sign up with email or GitHub
   - Free tier includes:
     - 5,000 errors/month
     - 10,000 performance units/month
     - 50 session replays/month

2. **Create Organization:**
   - Organization name: your-company-name
   - Choose free "Developer" plan

3. **Create Projects:**
   - Click "Create Project"
   - **Backend Project:**
     - Platform: Python
     - Project name: `data-detective-backend`
     - Alert frequency: "On every new issue"
   - **Frontend Project:**
     - Platform: JavaScript (React)
     - Project name: `data-detective-frontend`
     - Alert frequency: "On every new issue"

### Getting DSN Keys

1. Go to project Settings → Client Keys (DSN)
2. Copy the DSN URL (looks like: `https://abc123@o456.ingest.sentry.io/789`)
3. **Important:** Use different DSNs for backend and frontend!

### Sentry Configuration by Environment

#### Development
```bash
# Backend
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% sampling for testing
LOG_LEVEL=DEBUG
LOG_FORMAT=text  # Human-readable logs

# Frontend
VITE_SENTRY_ENVIRONMENT=development
VITE_SENTRY_TRACES_SAMPLE_RATE=1.0
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=1.0  # Record all sessions
```

#### Production
```bash
# Backend
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% sampling to save quota
LOG_LEVEL=INFO
LOG_FORMAT=json  # Machine-readable logs

# Frontend
VITE_SENTRY_ENVIRONMENT=production
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.1  # 10% of sessions
VITE_SENTRY_REPLAYS_ERROR_SAMPLE_RATE=1.0   # Always on errors
```

### What Gets Sent to Sentry

#### Backend
- ✅ All unhandled exceptions with stack traces
- ✅ HTTP errors (4xx, 5xx) with request context
- ✅ Database errors
- ✅ Performance data (slow endpoints)
- ❌ Passwords, tokens (filtered by `_filter_sensitive_data()`)
- ❌ Authorization headers (filtered)

#### Frontend
- ✅ JavaScript errors and React component errors
- ✅ API call failures (except 401)
- ✅ Performance metrics (page loads, route changes)
- ✅ User session replays (when errors occur)
- ✅ Breadcrumbs (user actions leading to error)
- ❌ Passwords, tokens (filtered by `beforeSend()`)
- ❌ 401 errors (expected behavior, not sent)

---

## Logging Guide

### Log Levels

The backend uses Python's standard logging module with the following levels:

| Level    | When to Use                           | Examples                                    |
|----------|---------------------------------------|---------------------------------------------|
| DEBUG    | Detailed diagnostic information       | Variable values, control flow              |
| INFO     | General informational messages        | User login, challenge completion           |
| WARNING  | Something unexpected but handled      | Failed login attempt, invalid input        |
| ERROR    | Serious problem, operation failed     | Database error, unhandled exception        |
| CRITICAL | System-level failure                  | Database unavailable, disk full            |

### Using Logging in Code

**Backend Example (`backend/app/routes/your_route.py`):**

```python
from app.logging_config import get_logger

logger = get_logger(__name__)

@router.post("/example")
def example_endpoint(current_user: User = Depends(get_current_user)):
    # INFO: Normal operations
    logger.info(
        f"User performed action: {current_user.email}",
        extra={"user_id": current_user.id, "action": "example"},
    )

    try:
        # Your code here
        result = perform_operation()

    except ValueError as exc:
        # WARNING: Expected errors that are handled
        logger.warning(
            f"Invalid input: {exc}",
            extra={"user_id": current_user.id},
        )
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        # ERROR: Unexpected errors
        logger.error(
            f"Operation failed: {exc}",
            extra={"user_id": current_user.id},
            exc_info=True,  # Include stack trace
        )
        raise

    return result
```

### Log Output Formats

#### Text Format (Development)
```
2025-11-18 10:23:45 INFO     [app.routes.auth] User logged in: student@example.com (user_id=123)
2025-11-18 10:24:12 WARNING  [app.routes.progress] Incorrect challenge submission: unit=1, challenge=2 (user_id=123)
2025-11-18 10:25:33 ERROR    [app.main] Unhandled exception: ValueError: Invalid input
```

#### JSON Format (Production)
```json
{"timestamp": "2025-11-18T10:23:45Z", "level": "INFO", "logger": "app.routes.auth", "message": "User logged in: student@example.com", "user_id": 123, "email": "student@example.com"}
{"timestamp": "2025-11-18T10:24:12Z", "level": "WARNING", "logger": "app.routes.progress", "message": "Incorrect challenge submission: unit=1, challenge=2", "user_id": 123, "unit_id": 1, "challenge_id": 2}
```

### Viewing Logs

**Development (Console):**
```bash
cd backend
uvicorn app.main:app --reload
# Logs appear in terminal with colors
```

**Production (Sentry):**
1. Go to Sentry dashboard
2. Navigate to "Issues"
3. Click on an issue to see logs and context
4. Use "Breadcrumbs" tab to see log trail

### Searching Logs in Sentry

**By User:**
```
user.id:123
user.email:student@example.com
```

**By Endpoint:**
```
http.url:"*/auth/login*"
```

**By Error Type:**
```
error.type:ValueError
```

**By Time Range:**
- Use date picker in top right
- Or: `timestamp:>2025-11-18T00:00:00`

---

## Uptime Monitoring

### Setting Up UptimeRobot

1. **Create Account:**
   - Visit [https://uptimerobot.com/signUp](https://uptimerobot.com/signUp)
   - Sign up with email (free tier)
   - Free plan includes:
     - 50 monitors
     - 5-minute check intervals
     - Email alerts

2. **Create Monitor:**
   - Click "Add New Monitor"
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Data Detective - Production`
   - URL: `https://your-domain.com/health`
   - Monitoring Interval: **5 minutes**
   - Alert Contacts: Add your email

3. **Configure Health Check:**
   - Monitor Timeout: 30 seconds
   - HTTP Method: GET
   - Expected Status Code: 200
   - Keyword Check (optional): `"healthy"`

4. **Test Monitor:**
   - Click "Test" to verify it works
   - Should show "Up" status

### Health Endpoint

The `/health` endpoint provides comprehensive health information:

**Request:**
```bash
curl https://your-domain.com/health
```

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "ok"
  }
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2025-11-18T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "error"
  }
}
```

### Alert Configuration

**UptimeRobot Alert Settings:**
- **Alert When:** Down
- **Alert After:** 2 consecutive failures (10 minutes)
- **Alert To:** Your email
- **Alert Message Template:**
  ```
  🚨 ALERT: Data Detective is DOWN
  URL: {{monitorURL}}
  Time: {{monitorAlertTime}}
  Reason: {{monitorAlertDetails}}
  ```

**Recovery Alert:**
- **Alert When:** Up (after being down)
- **Alert Message Template:**
  ```
  ✅ RECOVERED: Data Detective is back UP
  Downtime: {{monitorDowntimeDuration}}
  ```

---

## Performance Monitoring

### What We Track

#### Backend Performance
- **Endpoint Response Times:**
  - Average (p50): < 200ms target
  - 95th percentile (p95): < 500ms target
  - 99th percentile (p99): < 1s target

- **Database Query Times:**
  - Slow query threshold: > 100ms
  - Tracked automatically by Sentry

- **Request Duration:**
  - Logged for every request
  - Visible in logs and Sentry

#### Frontend Performance
- **Page Load Time:**
  - First Contentful Paint (FCP): < 1.8s
  - Largest Contentful Paint (LCP): < 2.5s
  - Time to Interactive (TTI): < 3.8s

- **Route Change Time:**
  - Client-side navigation: < 200ms

- **API Call Duration:**
  - Tracked with breadcrumbs
  - Slow requests flagged in Sentry

### Viewing Performance in Sentry

1. **Navigate to Performance Tab:**
   - Go to your project in Sentry
   - Click "Performance" in left sidebar

2. **View Slow Transactions:**
   - Sort by "p95 Duration"
   - Look for red/yellow indicators
   - Click transaction to see details

3. **Analyze Slow Endpoint:**
   - View flame graph
   - See database query times
   - Check external API calls

4. **Frontend Performance:**
   - View "Web Vitals" tab
   - See LCP, FID, CLS metrics
   - Identify slow pages

### Optimizing Performance

**Backend:**
- Add database indexes for slow queries
- Implement caching (already in place for leaderboard, analytics)
- Use pagination for large result sets
- Profile slow endpoints with Sentry profiling

**Frontend:**
- Code splitting for large components
- Lazy loading for routes
- Optimize bundle size
- Use React.memo for expensive components

---

## Alert Configuration

### Sentry Alert Rules

#### Critical Error Alert (Immediate)

1. Go to Sentry → Alerts → Create Alert Rule
2. Configure:
   - **Name:** Critical Errors
   - **Conditions:**
     - When: An event is seen
     - Where: level equals error OR critical
   - **Frequency:** Immediately
   - **Actions:**
     - Send email to: your-email@example.com
     - Include: Stack trace, breadcrumbs, user context

#### High Error Rate Alert (Warning)

1. Create Alert Rule:
   - **Name:** High Error Rate
   - **Conditions:**
     - When: An event is seen
     - Where: error rate exceeds 5% in 15 minutes
   - **Frequency:** Once per issue
   - **Actions:**
     - Send email digest

#### Performance Degradation Alert

1. Create Alert Rule:
   - **Name:** Slow Endpoints
   - **Conditions:**
     - When: p95 response time
     - Where: > 2000ms (2 seconds)
   - **Frequency:** Daily digest
   - **Actions:**
     - Send email summary

### Email Alert Setup

**Sentry Email Notifications:**
1. Go to Settings → Notifications
2. Enable:
   - ✅ Deploy notifications
   - ✅ Issue alerts
   - ✅ Quota notifications
   - ❌ Weekly reports (optional)

**UptimeRobot Email Alerts:**
1. Go to My Settings → Alert Contacts
2. Add email address
3. Verify email
4. Assign to monitors

### Slack Integration (Optional)

1. **Connect Slack to Sentry:**
   - Go to Settings → Integrations
   - Click "Slack"
   - Click "Add Workspace"
   - Authorize Slack

2. **Configure Slack Alerts:**
   - Create alert rule (as above)
   - Action: "Send Slack notification"
   - Channel: #engineering-alerts

---

## Troubleshooting

### Sentry Not Receiving Events

**Check DSN Configuration:**
```bash
# Backend
cd backend
grep SENTRY_DSN .env
# Should show: SENTRY_DSN=https://...

# Frontend
cd frontend
grep VITE_SENTRY_DSN .env
# Should show: VITE_SENTRY_DSN=https://...
```

**Check Initialization:**
```bash
# Backend - should see log message
uvicorn app.main:app --reload
# Look for: "Sentry initialized for environment: development"

# Frontend - check browser console
pnpm dev
# Open http://localhost:3000
# Console should show: "Sentry initialized for environment: development"
```

**Test with Error:**
```python
# Backend - create test endpoint
@app.get("/test/error")
def test_error():
    raise ValueError("Test error for Sentry")

# Visit: http://localhost:8000/test/error
# Check Sentry dashboard for error
```

```javascript
// Frontend - create test button
<button onClick={() => { throw new Error("Test error"); }}>
  Test Error
</button>
// Click button, check Sentry dashboard
```

### Logs Not Appearing

**Check Log Level:**
```bash
# .env
LOG_LEVEL=DEBUG  # Set to DEBUG for testing
```

**Check Log Format:**
```python
# backend/app/main.py
# Should see logging initialization:
setup_logging()
logger = get_logger(__name__)
```

**Restart Server:**
```bash
# Changes to logging config require restart
cd backend
uvicorn app.main:app --reload
```

### Health Check Failing

**Test Locally:**
```bash
curl http://localhost:8000/health
# Should return 200 with JSON
```

**Check Database:**
```bash
# Backend logs should show:
# "Database health check failed" if database is down
```

**Check Firewall:**
```bash
# Ensure port is open for UptimeRobot IPs
# UptimeRobot IP ranges: https://uptimerobot.com/inc/files/ips/IPv4.txt
```

### Performance Issues

**High Response Times:**
1. Check Sentry Performance tab
2. Identify slow endpoint
3. Look for slow database queries
4. Add logging to measure sections:
   ```python
   import time
   start = time.time()
   # Your code
   duration = time.time() - start
   logger.info(f"Operation took {duration:.2f}s")
   ```

**High Memory Usage:**
1. Check for memory leaks in Sentry
2. Enable profiling:
   ```bash
   SENTRY_PROFILES_SAMPLE_RATE=1.0
   ```
3. View profiles in Sentry

---

## Best Practices

### What to Log

**✅ DO Log:**
- User authentication events (login, logout)
- Important state changes (challenge completion)
- Errors and exceptions
- Performance metrics (slow queries)
- Security events (failed login attempts)

**❌ DON'T Log:**
- Passwords or password hashes
- API keys or tokens
- Credit card numbers
- Personally identifiable information (PII) without need
- Every single request in production (use sampling)

### Security Considerations

**Sensitive Data Filtering:**
- Backend filters applied in `_filter_sensitive_data()`
- Frontend filters applied in `beforeSend()`
- Never log passwords, even hashed
- Redact tokens from logs

**PII Handling:**
- Be mindful of GDPR requirements
- Don't send unnecessary user data to Sentry
- Configure data scrubbing in Sentry settings
- Set data retention limits

### Cost Management

**Sentry Free Tier Limits:**
- 5,000 errors/month
- 10,000 performance units/month
- 50 session replays/month

**Staying Within Limits:**
- Use sample rates (0.1 = 10%)
- Don't send 401 errors (expected)
- Group similar errors in Sentry
- Increase sample rates only in dev
- Monitor quota in Sentry dashboard

**If You Exceed Free Tier:**
- Sentry Team plan: $26/month (100k errors)
- Or reduce sample rates:
  ```bash
  SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
  ```

### Monitoring Checklist

**Before Production:**
- [ ] Sentry DSN configured for both backend and frontend
- [ ] Environment variables set correctly
- [ ] Log level set to INFO (not DEBUG)
- [ ] Log format set to JSON
- [ ] Sample rates configured (0.1 recommended)
- [ ] UptimeRobot monitor created and tested
- [ ] Alert email addresses configured
- [ ] Test error sent to Sentry
- [ ] Health endpoint returns 200
- [ ] Performance baselines established

**Weekly Monitoring:**
- [ ] Review error trends in Sentry
- [ ] Check uptime percentage (target: 99.9%)
- [ ] Review slow endpoints
- [ ] Check Sentry quota usage
- [ ] Review and resolve open issues

---

## Additional Resources

- **Sentry Documentation:** [https://docs.sentry.io/](https://docs.sentry.io/)
- **UptimeRobot Documentation:** [https://uptimerobot.com/api/](https://uptimerobot.com/api/)
- **Python Logging:** [https://docs.python.org/3/library/logging.html](https://docs.python.org/3/library/logging.html)
- **FastAPI Logging:** [https://fastapi.tiangolo.com/tutorial/logging/](https://fastapi.tiangolo.com/tutorial/logging/)

---

## Support

If you encounter issues with monitoring setup:

1. Check this guide first
2. Review Sentry documentation
3. Check application logs for errors
4. Create an issue in the repository

**Common Support Links:**
- Sentry Support: [https://sentry.io/support/](https://sentry.io/support/)
- UptimeRobot Support: [https://uptimerobot.com/contact/](https://uptimerobot.com/contact/)

---

**Last Updated:** 2025-11-18
