# Render.com Deployment - Quick Start Guide

This guide provides step-by-step instructions for deploying the Data Detective Academy backend to Render.com.

## Why Render.com?

✅ **Free Tier Benefits:**
- PostgreSQL database (1GB, free for 90 days)
- Web service hosting (512MB RAM, free with limitations)
- Automatic SSL certificates
- Zero-downtime deploys
- Auto-deploy from GitHub
- No credit card required

## Prerequisites

- GitHub account with this repository
- Render.com account (sign up at https://render.com/)

## Quick Start (5 minutes)

### Option 1: One-Click Blueprint Deploy (Easiest)

1. **Connect Repository to Render:**
   - Go to https://dashboard.render.com/
   - Sign in with GitHub
   - Authorize Render to access this repository

2. **Deploy with Blueprint:**
   - Click **"New +"** → **"Blueprint"**
   - Select this repository
   - Click **"Apply"**

3. **Wait for Deployment:**
   - Render automatically creates:
     - PostgreSQL database
     - Backend web service
     - Environment variables
   - First deploy takes 5-10 minutes

4. **Verify Deployment:**
   ```bash
   # Replace with your actual URL
   curl https://data-detective-api.onrender.com/health
   # Should return: {"status":"healthy"}
   ```

5. **Access API Documentation:**
   - Visit: `https://YOUR_SERVICE_NAME.onrender.com/docs`

### Option 2: Manual Setup

If you prefer more control or need to customize settings:

#### Step 1: Create PostgreSQL Database

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `data-detective-db`
   - **Database**: `data_detective_academy`
   - **User**: `data_detective_user`
   - **Region**: `Oregon` (or closest to your users)
   - **PostgreSQL Version**: `16`
   - **Plan**: **Free**
4. Click **"Create Database"**
5. **Save the Internal Database URL** (you'll need it for the web service)

#### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect to your GitHub repository
3. Configure service:

| Setting | Value |
|---------|-------|
| **Name** | `data-detective-api` |
| **Region** | `Oregon` (same as database) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install uv && uv sync --no-dev` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | **Free** |

#### Step 3: Configure Environment Variables

In the **"Environment"** tab, add these variables:

```bash
# Database - Paste the Internal Database URL from Step 1
DATABASE_URL=postgresql://data_detective_user:PASSWORD@HOST/data_detective_academy

# JWT Settings
SECRET_KEY=<click "Generate" to create secure random value>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
ENVIRONMENT=production
DEBUG=false

# CORS - Add your frontend URL after deploying it
ALLOWED_ORIGINS=https://data-detective.onrender.com,http://localhost:3000
FRONTEND_URL=https://data-detective.onrender.com

# Analytics (Optional)
ANALYTICS_ENABLED=false
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=datadetective.academy
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js
```

**Important:** For `SECRET_KEY`, click the **"Generate"** button to create a cryptographically secure random value.

#### Step 4: Configure Health Check

1. Scroll to **"Health Check Path"**
2. Enter: `/health`

This allows Render to monitor your service and restart it if it becomes unhealthy.

#### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Run the build command
   - Install dependencies with `uv`
   - Start the service
3. Monitor the **"Logs"** tab for deployment progress
4. First deployment takes 5-10 minutes

## Database Setup

### Automatic Migration

When your service starts for the first time, SQLModel automatically creates all necessary database tables via the `lifespan` function in `backend/app/main.py`.

**Tables created:**
- `users`
- `refresh_tokens`
- `password_reset_tokens`
- `progress`
- `hints`
- `attempts`
- `datasets`
- `custom_challenges`

### Verify Database Tables

1. Go to Render Dashboard → PostgreSQL database
2. Click **"Connect"** → **"External Connection"**
3. Copy the connection string
4. Use `psql` or any PostgreSQL client:

```bash
psql "postgresql://data_detective_user:PASSWORD@HOST/data_detective_academy"

# List all tables
\dt

# Describe a table
\d users

# Count records (should be 0 initially)
SELECT COUNT(*) FROM users;

# Exit
\q
```

### Manual Migration (if needed)

If you need to run Alembic migrations:

```bash
# From your local machine with DATABASE_URL set to Render's external URL
export DATABASE_URL="postgresql://..."
cd backend
uv run alembic upgrade head
```

## Post-Deployment Configuration

### 1. Enable Auto-Deploys

1. Go to your web service → **"Settings"** → **"Build & Deploy"**
2. Set **"Auto-Deploy"** to **Yes**
3. Now every push to `main` branch automatically deploys

### 2. Update Frontend Configuration

Update your frontend to point to the new backend:

```bash
# frontend/.env.production
VITE_API_URL=https://YOUR_SERVICE_NAME.onrender.com
```

### 3. Update CORS Settings

Once your frontend is deployed, update the backend environment variable:

```bash
ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

## Testing Your Deployment

### Health Check
```bash
curl https://YOUR_SERVICE_NAME.onrender.com/health
# Expected: {"status":"healthy"}
```

### API Info
```bash
curl https://YOUR_SERVICE_NAME.onrender.com/api/info
# Expected: {"app":"Data Detective Academy","environment":"production"}
```

### API Documentation
Visit: `https://YOUR_SERVICE_NAME.onrender.com/docs`

### Create Test User
```bash
curl -X POST https://YOUR_SERVICE_NAME.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123",
    "role": "student"
  }'
```

### Login
```bash
curl -X POST https://YOUR_SERVICE_NAME.onrender.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

## Free Tier Limitations & Solutions

### Sleep Mode (15-minute inactivity)

**Problem:** Free tier services "sleep" after 15 minutes of inactivity. First request after sleep takes 30-60 seconds.

**Solutions:**

1. **Upgrade to Paid Plan** ($7/month for always-on)
2. **Use Uptime Monitor** (free):
   - Sign up at https://uptimerobot.com/
   - Create monitor for: `https://YOUR_SERVICE_NAME.onrender.com/health`
   - Interval: Every 5 minutes
   - This keeps your service awake

3. **Use Cron Job Service** (free):
   - Sign up at https://cron-job.org/
   - Add job: `https://YOUR_SERVICE_NAME.onrender.com/health`
   - Schedule: Every 10 minutes

### PostgreSQL 90-Day Limit

**Problem:** Free PostgreSQL expires after 90 days.

**Solutions:**

1. **Upgrade to Paid Plan** ($7/month, 25GB storage)
2. **Migrate to Alternative**:
   - Supabase (free tier, 500MB)
   - ElephantSQL (free tier, 20MB)
   - Neon (free tier, 3GB)
3. **Export and Re-create**:
   ```bash
   # Export data
   pg_dump "postgresql://..." > backup.sql

   # Create new free database on Render
   # Import data
   psql "postgresql://NEW_URL" < backup.sql

   # Update DATABASE_URL environment variable
   ```

## Monitoring

### View Logs
1. Dashboard → Web Service → **"Logs"**
2. Real-time streaming
3. Search and filter

### Metrics
1. Dashboard → Web Service → **"Metrics"**
2. Monitor:
   - Request rate
   - Response times
   - Memory usage
   - CPU usage

### Alerts
1. Dashboard → Web Service → **"Settings"** → **"Alerts"**
2. Get email notifications for:
   - Deploy failures
   - Health check failures
   - High memory usage

## Troubleshooting

### Build Fails

**Error: Python version not compatible**
```bash
# Solution: Check pyproject.toml
# Render uses Python 3.11 by default
requires-python = ">=3.11"
```

**Error: uv not found**
```bash
# Solution: Ensure build command installs uv first
pip install uv && uv sync --no-dev
```

### Service Won't Start

**Error: Port binding**
```bash
# Problem: Not using $PORT environment variable
# Solution: Start command must use $PORT
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Error: Database connection**
```bash
# Problem: DATABASE_URL not set or incorrect
# Solution: Use Internal Database URL from Render dashboard
# Format: postgresql://user:pass@internal-host/dbname
```

**Error: SECRET_KEY missing**
```bash
# Problem: SECRET_KEY environment variable not set
# Solution: Add to environment variables and click "Generate" for secure value
```

### Service is Slow

**First request takes 30+ seconds**
- This is normal for free tier (cold start after sleep)
- Use uptime monitor to keep service awake (see above)

**All requests are slow**
- Check Metrics tab for memory/CPU usage
- Free tier has limited resources (512MB RAM)
- Consider upgrading to paid plan

### Database Errors

**Error: relation "users" does not exist**
```bash
# Problem: Tables not created
# Solution: Tables are auto-created on first start
# Check logs for startup errors
# If needed, manually run table creation:
# (This happens automatically in app/main.py lifespan function)
```

**Error: connection refused**
```bash
# Problem: Using External Database URL instead of Internal
# Solution: In Render dashboard, use "Internal Database URL" for better performance
```

## Custom Domain Setup

### Add Custom Domain

1. Go to web service → **"Settings"** → **"Custom Domain"**
2. Click **"Add Custom Domain"**
3. Enter: `api.yourdomain.com`
4. Render shows DNS records to add

### Configure DNS

Add CNAME record at your DNS provider:

```
Type: CNAME
Name: api
Value: YOUR_SERVICE_NAME.onrender.com
TTL: 3600
```

### SSL Certificate

- Render automatically provisions SSL certificate
- Can take up to 24 hours for DNS propagation
- Check status in **"Custom Domain"** section

### Update Environment Variables

After domain is active, update CORS:

```bash
ALLOWED_ORIGINS=https://api.yourdomain.com,https://yourdomain.com
```

## Backup & Recovery

### Backup Database

```bash
# Get external database URL from Render dashboard
pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql

# Or with compression
pg_dump "postgresql://..." | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Database

```bash
# Restore from backup
psql "postgresql://..." < backup.sql

# Or from compressed
gunzip -c backup.sql.gz | psql "postgresql://..."
```

### Automated Backups

Render provides automatic daily backups (7-day retention) for PostgreSQL databases.

**Access backups:**
1. Dashboard → PostgreSQL database
2. **"Backups"** tab
3. Download or restore as needed

## Cost Breakdown

### Free Tier (First 90 days)
```
PostgreSQL: $0 (1GB)
Web Service: $0 (512MB RAM, with sleep)
Total: $0/month
```

### After 90 Days - Option 1
```
PostgreSQL Starter: $7/month (25GB)
Web Service Free: $0 (with sleep)
Total: $7/month
```

### After 90 Days - Option 2
```
PostgreSQL Starter: $7/month (25GB)
Web Service Starter: $7/month (512MB, always-on)
Total: $14/month
```

### Cost Optimization Tips

1. **Keep Free Tier Longer**: Use uptime monitor to prevent sleep
2. **Database Alternatives**: Consider Supabase (free 500MB)
3. **Multiple Apps**: Share one PostgreSQL instance across services
4. **Seasonal**: Delete and recreate services during low-usage periods

## Next Steps

1. ✅ **Deploy Frontend**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for frontend deployment options
2. ✅ **Set Up Monitoring**: Configure uptime monitoring to prevent sleep
3. ✅ **Custom Domain**: Add your own domain (optional)
4. ✅ **Backup Strategy**: Set up automated backups
5. ✅ **Performance Testing**: Load test your deployment
6. ✅ **Security Review**: Review environment variables and CORS settings

## Support & Resources

- **Render Documentation**: https://render.com/docs
- **Render Community**: https://community.render.com/
- **Project Documentation**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Frequently Asked Questions

**Q: Can I use Render's free tier for production?**
A: Yes, but be aware of limitations (sleep mode, 90-day database limit). For production, consider paid tier ($7/month).

**Q: How do I prevent my service from sleeping?**
A: Use an uptime monitor service (UptimeRobot, cron-job.org) to ping `/health` every 5-10 minutes.

**Q: What happens after 90 days?**
A: PostgreSQL database must be upgraded ($7/month) or migrated to another provider.

**Q: Can I use a different database provider?**
A: Yes! You can use Supabase, Neon, ElephantSQL, etc. Just update the `DATABASE_URL` environment variable.

**Q: How do I update my deployment?**
A: Just push to the `main` branch (if auto-deploy is enabled) or manually trigger deploy in dashboard.

**Q: Can I SSH into my Render service?**
A: SSH access is only available on paid plans ($7/month and up).

---

**Last Updated:** 2025-11-17

**Need Help?** Open an issue on GitHub or check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
