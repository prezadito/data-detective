# Deployment Guide

Complete guide for deploying Data Detective Academy to production.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Backend Deployment](#backend-deployment)
  - [Docker Deployment](#docker-deployment-backend)
  - [Traditional Server](#traditional-server-backend)
  - [Cloud Platforms](#cloud-platforms-backend)
- [Frontend Deployment](#frontend-deployment)
  - [Static Hosting](#static-hosting-frontend)
  - [Netlify](#netlify-deployment)
  - [Vercel](#vercel-deployment)
  - [Traditional Server](#traditional-server-frontend)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Security Checklist](#security-checklist)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting-deployment)

---

## Overview

Data Detective Academy consists of two separate applications:
- **Backend**: FastAPI Python application (Port 8000)
- **Frontend**: React SPA built with Vite (served as static files)

### Deployment Architecture

```
┌──────────────────┐
│   Users          │
│   (Browser)      │
└────────┬─────────┘
         │
         │ HTTPS
         ▼
┌────────────────────────────────────────┐
│         CDN / Load Balancer            │
│         (Optional)                     │
└────────┬───────────────────────────────┘
         │
         ├───────────────┬────────────────┐
         │               │                │
         ▼               ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│   Frontend     │ │   Backend    │ │   Backend    │
│   (Static)     │ │   (API)      │ │   (API)      │
│   Nginx/CDN    │ │   Gunicorn   │ │   Gunicorn   │
└────────────────┘ └──────┬───────┘ └──────┬───────┘
                          │                │
                          └────────┬───────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │   PostgreSQL   │
                          │   (Database)   │
                          └────────────────┘
```

---

## Prerequisites

### Backend Prerequisites
- Python 3.13+ installed
- uv package manager (`pip install uv`)
- PostgreSQL 14+ (production)
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)

### Frontend Prerequisites
- Node.js 18+ installed
- pnpm package manager (`npm install -g pnpm`)
- Web server (Nginx, Apache) or static hosting account

### Infrastructure
- Server with at least 2GB RAM (4GB recommended)
- 20GB storage minimum
- Ubuntu 22.04 LTS or similar Linux distribution

---

## Environment Setup

### 1. Server Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential git curl wget nginx postgresql postgresql-contrib

# Install Python 3.13 (if not available)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install pnpm
npm install -g pnpm
```

### 2. Create Application User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash datadetective
sudo usermod -aG sudo datadetective

# Switch to application user
sudo su - datadetective
```

### 3. Clone Repository

```bash
# Clone repository
git clone <repository-url> /home/datadetective/app
cd /home/datadetective/app
```

---

## Backend Deployment

### Docker Deployment (Backend)

**Recommended for production**

#### 1. Create Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY app/ app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uv", "run", "gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

#### 2. Create docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://datadetective:${DB_PASSWORD}@db:5432/datadetective
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=False
    depends_on:
      - db
    restart: unless-stopped
    networks:
      - app-network

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=datadetective
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=datadetective
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

#### 3. Deploy with Docker Compose

```bash
# Create .env file
cat > .env << EOF
DB_PASSWORD=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

---

### Traditional Server (Backend)

#### 1. Install Dependencies

```bash
cd /home/datadetective/app/backend

# Install dependencies
uv sync --frozen

# Install Gunicorn
uv pip install gunicorn
```

#### 2. Configure Environment

```bash
# Create production .env
cat > .env << EOF
# Database
DATABASE_URL=postgresql://datadetective:YOUR_PASSWORD@localhost/datadetective

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production
DEBUG=False

# CORS (update with your frontend domain)
ALLOWED_ORIGINS=https://yourdomain.com
EOF
```

#### 3. Create Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/datadetective-backend.service << EOF
[Unit]
Description=Data Detective Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=datadetective
Group=datadetective
WorkingDirectory=/home/datadetective/app/backend
Environment="PATH=/home/datadetective/.local/bin:/usr/local/bin:/usr/bin:/bin"

# Load environment variables
EnvironmentFile=/home/datadetective/app/backend/.env

# Run Gunicorn with Uvicorn workers
ExecStart=/home/datadetective/.local/bin/uv run gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/datadetective/access.log \
    --error-logfile /var/log/datadetective/error.log \
    --log-level info

# Restart policy
Restart=always
RestartSec=5

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/datadetective/app

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/datadetective
sudo chown datadetective:datadetective /var/log/datadetective

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable datadetective-backend
sudo systemctl start datadetective-backend

# Check status
sudo systemctl status datadetective-backend
```

#### 4. Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/datadetective << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

# Backend upstream
upstream backend {
    server 127.0.0.1:8000;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to backend
    location / {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limit authentication endpoints
    location /auth/ {
        limit_req zone=auth_limit burst=3 nodelay;
        proxy_pass http://backend;
        # ... (same proxy settings as above)
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/datadetective /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

### Cloud Platforms (Backend)

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
cd backend
eb init -p python-3.13 data-detective-api

# Create environment
eb create production-env

# Set environment variables
eb setenv SECRET_KEY="your-secret-key" \
          DATABASE_URL="postgresql://..." \
          ENVIRONMENT="production"

# Deploy
eb deploy
```

#### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/datadetective-backend

# Deploy
gcloud run deploy datadetective-backend \
    --image gcr.io/PROJECT_ID/datadetective-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "SECRET_KEY=...,DATABASE_URL=..."
```

#### Heroku

```bash
# Create app
heroku create datadetective-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"

# Deploy
git push heroku main
```

#### Render.com (Recommended for Free Tier)

**Why Render.com?**
- Free tier includes PostgreSQL (1GB) + Web Service
- Zero-downtime deploys
- Automatic SSL certificates
- Built-in health checks
- Deploy from Git (auto-deploys on push)
- No credit card required for free tier

##### Step 1: Prepare Repository

The repository already includes `render.yaml` for automated deployment.

##### Step 2: Create Render Account

1. Go to https://render.com/
2. Sign up with GitHub/GitLab
3. Authorize Render to access your repository

##### Step 3: Deploy Using render.yaml (Recommended)

**Option A: Blueprint Deployment (Easiest)**

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub/GitLab repository
4. Select the repository containing `render.yaml`
5. Click **"Apply"**
6. Render will automatically:
   - Create PostgreSQL database (1GB free)
   - Create web service for backend
   - Configure environment variables
   - Set up auto-deploys from main branch

**Option B: Manual Dashboard Setup**

If you prefer manual setup or need to customize:

**1. Create PostgreSQL Database:**
   - Dashboard → **"New +"** → **"PostgreSQL"**
   - Name: `data-detective-db`
   - Database: `data_detective_academy`
   - User: `data_detective_user`
   - Region: `Oregon` (or closest to users)
   - Plan: **Free** (1GB, expires after 90 days)
   - Click **"Create Database"**
   - Copy the **Internal Database URL** (starts with `postgresql://`)

**2. Create Web Service:**
   - Dashboard → **"New +"** → **"Web Service"**
   - Connect repository → Select your repo
   - Configure:
     - **Name**: `data-detective-api`
     - **Region**: `Oregon` (same as database)
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: `Python 3`
     - **Build Command**:
       ```bash
       pip install uv && uv sync --no-dev
       ```
     - **Start Command**:
       ```bash
       uvicorn app.main:app --host 0.0.0.0 --port $PORT
       ```
     - **Plan**: **Free**

**3. Configure Environment Variables:**

Click **"Environment"** tab and add:

```bash
# Database (use Internal Database URL from step 1)
DATABASE_URL=postgresql://data_detective_user:PASSWORD@HOST/data_detective_academy

# JWT Settings
SECRET_KEY=<click "Generate" button for secure random value>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
DEBUG=false

# CORS - Update after deploying frontend
ALLOWED_ORIGINS=https://data-detective.onrender.com,http://localhost:3000
FRONTEND_URL=https://data-detective.onrender.com

# Analytics (Optional)
ANALYTICS_ENABLED=false
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=datadetective.academy
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js
```

**4. Configure Health Check:**
   - **Health Check Path**: `/health`
   - Render will automatically ping this endpoint
   - Service is marked unhealthy if it fails 3 consecutive checks

**5. Deploy:**
   - Click **"Create Web Service"**
   - Render will build and deploy automatically
   - Monitor logs in the dashboard
   - First deploy takes 5-10 minutes

##### Step 4: Verify Deployment

```bash
# Check health endpoint
curl https://data-detective-api.onrender.com/health

# Expected response:
# {"status":"healthy"}

# Check API info
curl https://data-detective-api.onrender.com/api/info

# Test API docs
# Visit: https://data-detective-api.onrender.com/docs
```

##### Step 5: Database Migration

After first deployment, database tables are automatically created via the `lifespan` function in `app/main.py`.

To verify tables were created:

1. Go to Render Dashboard → PostgreSQL database
2. Click **"Connect"** → Copy external connection string
3. Use a PostgreSQL client or command line:
   ```bash
   psql "postgresql://data_detective_user:PASSWORD@HOST/data_detective_academy"

   # List tables
   \dt

   # Expected tables:
   # users, refresh_tokens, password_reset_tokens, progress, hints, attempts
   ```

If using Alembic migrations:

```bash
# SSH into Render shell (if available on paid plan)
alembic upgrade head
```

##### Step 6: Set Up Auto-Deploys

1. Go to web service **"Settings"** → **"Build & Deploy"**
2. Enable **"Auto-Deploy"**: `Yes`
3. Every push to `main` branch will trigger automatic deployment
4. Zero-downtime deploys (new version rolled out gradually)

##### Step 7: Custom Domain (Optional)

1. Go to web service **"Settings"** → **"Custom Domain"**
2. Add your domain: `api.yourdomain.com`
3. Add CNAME record in your DNS provider:
   ```
   CNAME  api  data-detective-api.onrender.com
   ```
4. Render automatically provisions SSL certificate
5. Update `ALLOWED_ORIGINS` environment variable with new domain

##### Step 8: Update Frontend Configuration

After backend is deployed, update frontend environment variables:

```bash
# Frontend .env
VITE_API_URL=https://data-detective-api.onrender.com
```

Rebuild and redeploy frontend.

##### Render.com Free Tier Limitations

**PostgreSQL:**
- 1GB storage
- Expires after 90 days (must upgrade or migrate)
- Automatic daily backups (7-day retention)

**Web Service:**
- 512MB RAM
- Shared CPU
- Spins down after 15 minutes of inactivity
- Cold start takes 30-60 seconds
- 750 hours/month free (enough for 1 service running 24/7)

**Performance Tips:**
- Free tier services "sleep" after inactivity - first request may be slow
- Consider using a cron job to ping `/health` every 10 minutes
- Use Render's paid Starter plan ($7/month) for always-on service

##### Monitoring and Logs

**View Logs:**
1. Dashboard → Web Service → **"Logs"** tab
2. Real-time streaming logs
3. Search and filter capabilities

**Metrics:**
1. Dashboard → Web Service → **"Metrics"** tab
2. CPU, Memory, Request rate
3. Response times

**Alerts:**
1. Dashboard → Web Service → **"Settings"** → **"Alerts"**
2. Configure email alerts for:
   - Deploy failures
   - Health check failures
   - High memory usage

##### Troubleshooting Render Deployment

**Build fails:**
```bash
# Check Python version compatibility
# Render uses Python 3.11 by default
# Update pyproject.toml if needed:
requires-python = ">=3.11"

# Ensure uv is installed in build command
pip install uv && uv sync --no-dev
```

**Service won't start:**
```bash
# Check logs for errors
# Common issues:
# - DATABASE_URL not set correctly
# - SECRET_KEY missing
# - Port binding (must use $PORT environment variable)

# Verify start command uses $PORT:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Database connection errors:**
```bash
# Use Internal Database URL (not external) for better performance
# Format: postgresql://user:pass@internal-host/dbname

# Check database is running
# Dashboard → PostgreSQL → Status should be "Available"
```

**Slow cold starts:**
```bash
# Free tier spins down after 15 minutes inactivity
# Solutions:
# 1. Upgrade to paid plan ($7/month for always-on)
# 2. Use cron job to ping /health every 10 minutes
# 3. Set up UptimeRobot (free) to ping your service

# Example: Use cron-job.org (free service)
# Add job: https://data-detective-api.onrender.com/health
# Interval: Every 10 minutes
```

**SSL certificate issues:**
```bash
# Render automatically provisions SSL
# If custom domain SSL fails:
# 1. Verify CNAME record is correct
# 2. Wait up to 24 hours for DNS propagation
# 3. Check Dashboard → Custom Domain → Status
```

##### Cost Optimization

**Free tier usage:**
```
PostgreSQL: $0 (first 90 days, then $7/month)
Web Service: $0 (750 hours/month)
Total: $0 for first 90 days
```

**After 90 days:**
```
PostgreSQL Starter: $7/month (25GB)
Web Service Free: $0 (with sleep mode)
OR
Web Service Starter: $7/month (always-on)
Total: $7-14/month
```

**Alternatives after free tier expires:**
- Migrate to Supabase (free PostgreSQL)
- Use Railway.com (free $5/month credit)
- Use Heroku hobby tier ($7/month)

---

## Frontend Deployment

### Static Hosting (Frontend)

#### 1. Build for Production

```bash
cd frontend

# Install dependencies
pnpm install

# Set production environment variables
cat > .env.production << EOF
VITE_API_URL=https://api.yourdomain.com
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production
EOF

# Build
pnpm build

# Output will be in dist/
```

#### 2. Deploy to Nginx

```bash
# Copy build to web server
sudo cp -r dist/* /var/www/datadetective/

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/datadetective-frontend << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Root directory
    root /var/www/datadetective;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Disable caching for index.html
    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/datadetective-frontend /etc/nginx/sites-enabled/

# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx
```

---

### Netlify Deployment

#### Option 1: Git Integration (Recommended)

1. Push code to GitHub/GitLab
2. Go to https://app.netlify.com/
3. Click "New site from Git"
4. Select repository
5. Configure build settings:
   - Base directory: `frontend`
   - Build command: `pnpm build`
   - Publish directory: `frontend/dist`
6. Add environment variables in Netlify UI
7. Deploy

#### Option 2: Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd frontend
netlify deploy --prod --dir=dist

# Configure environment variables
netlify env:set VITE_API_URL https://api.yourdomain.com
```

**netlify.toml:**
```toml
[build]
  base = "frontend"
  command = "pnpm build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

---

### Vercel Deployment

**Recommended for Frontend Hosting**

Vercel is the ideal platform for deploying the Data Detective Academy frontend. It offers:
- Automatic Vite framework detection
- Zero-configuration deployments
- Built-in CDN and edge network
- Automatic HTTPS/SSL certificates
- Preview deployments for every pull request
- Generous free tier (100GB bandwidth/month)

#### Prerequisites

Before deploying to Vercel, ensure you have:
- Backend API deployed and accessible (e.g., Render.com)
- Backend API URL (e.g., `https://data-detective-api.onrender.com`)
- GitHub/GitLab account with repository access
- Vercel account (free tier available)

---

#### Option 1: Git Integration (Recommended)

**Step 1: Prepare Repository**

The repository already includes `frontend/vercel.json` with optimized configuration for:
- SPA routing (React Router support)
- Security headers (XSS, CSRF protection)
- Asset caching (1-year cache for static assets)
- API proxy configuration

**Step 2: Create Vercel Account**

1. Go to https://vercel.com/
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"** (or GitLab/Bitbucket)
4. Authorize Vercel to access your repositories

**Step 3: Import Project**

1. From Vercel Dashboard, click **"Add New..."** → **"Project"**
2. Find your repository in the list (or use search)
3. Click **"Import"** next to `data-detective` repository

**Step 4: Configure Project Settings**

Vercel will auto-detect the Vite framework. Configure these settings:

```
Framework Preset: Vite (auto-detected)
Root Directory: frontend
Build Command: pnpm build (auto-detected)
Output Directory: dist (auto-detected)
Install Command: pnpm install (auto-detected)
Node.js Version: 20.x (default)
```

**Important**: Set **Root Directory** to `frontend` since this is a monorepo.

**Step 5: Configure Environment Variables**

Click **"Environment Variables"** and add:

| Name | Value | Environment |
|------|-------|-------------|
| `VITE_API_URL` | `https://your-backend-api.onrender.com` | Production, Preview, Development |
| `VITE_APP_NAME` | `Data Detective` | Production, Preview, Development |
| `VITE_APP_VERSION` | `1.0.0` | Production, Preview, Development |
| `VITE_ENV` | `production` | Production |
| `VITE_ENV` | `preview` | Preview |

**Example Configuration:**

```env
# Production Environment Variables
VITE_API_URL=https://data-detective-api.onrender.com
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production
```

**Step 6: Deploy**

1. Click **"Deploy"**
2. Vercel will:
   - Clone your repository
   - Install dependencies with `pnpm install`
   - Build the frontend with `pnpm build`
   - Deploy to global CDN
   - Provision SSL certificate
3. First deployment takes 2-5 minutes
4. Monitor build logs in real-time

**Step 7: Verify Deployment**

After deployment completes:

```bash
# Your site will be available at:
https://data-detective.vercel.app

# Or custom domain:
https://yourdomain.com

# Check the deployment
curl -I https://data-detective.vercel.app

# Expected response:
HTTP/2 200
content-type: text/html
x-vercel-id: ...
```

**Step 8: Update Backend CORS**

Update your backend's `ALLOWED_ORIGINS` environment variable to include your Vercel domain:

```bash
# Backend .env
ALLOWED_ORIGINS=https://data-detective.vercel.app,https://yourdomain.com
FRONTEND_URL=https://data-detective.vercel.app
```

Redeploy backend after updating CORS settings.

---

#### Option 2: Vercel CLI Deployment

For advanced users or CI/CD pipelines:

**Step 1: Install Vercel CLI**

```bash
# Install globally
npm install -g vercel

# Or use with npx
npx vercel --version
```

**Step 2: Login to Vercel**

```bash
vercel login
# Follow prompts to authenticate
```

**Step 3: Configure Project**

```bash
cd frontend

# Initialize Vercel project (first time only)
vercel link

# Select options:
# - Link to existing project? N (if first time)
# - Project name: data-detective
# - Directory: ./ (current directory is frontend)
```

**Step 4: Set Environment Variables**

```bash
# Production environment
vercel env add VITE_API_URL production
# Enter value: https://data-detective-api.onrender.com

vercel env add VITE_APP_NAME production
# Enter value: Data Detective

vercel env add VITE_APP_VERSION production
# Enter value: 1.0.0

vercel env add VITE_ENV production
# Enter value: production

# Preview environment (optional)
vercel env add VITE_API_URL preview
vercel env add VITE_ENV preview
# Enter value: preview
```

**Step 5: Deploy**

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Deploy with specific name
vercel --prod --name data-detective-academy
```

---

#### Custom Domain Configuration

**Step 1: Add Domain in Vercel**

1. Go to project **"Settings"** → **"Domains"**
2. Click **"Add"**
3. Enter your domain: `datadetective.academy` or `app.yourdomain.com`
4. Click **"Add"**

**Step 2: Configure DNS**

Vercel provides DNS records to add to your domain provider:

**Option A: Use Vercel as DNS (Recommended)**
```
Nameservers:
ns1.vercel-dns.com
ns2.vercel-dns.com
```

**Option B: Use CNAME Record**
```
Type: CNAME
Name: www (or subdomain)
Value: cname.vercel-dns.com
TTL: 3600
```

**Option C: Use A Record (Apex domain)**
```
Type: A
Name: @
Value: 76.76.21.21
TTL: 3600
```

**Step 3: Wait for DNS Propagation**

- DNS propagation takes 5 minutes to 48 hours
- Vercel automatically provisions SSL certificate once DNS resolves
- Check status in Vercel Dashboard → Domains

**Step 4: Verify SSL**

```bash
# Check SSL certificate
curl -I https://yourdomain.com

# Expected headers:
HTTP/2 200
content-type: text/html
strict-transport-security: max-age=31536000
```

---

#### Preview Deployments

Vercel automatically creates preview deployments for every pull request:

**How It Works:**

1. Create feature branch:
   ```bash
   git checkout -b feature/new-challenge
   ```

2. Make changes and push:
   ```bash
   git add .
   git commit -m "Add new challenge UI"
   git push origin feature/new-challenge
   ```

3. Create pull request on GitHub

4. Vercel automatically:
   - Builds the branch
   - Creates unique preview URL: `https://data-detective-git-feature-new-challenge.vercel.app`
   - Adds comment to PR with preview link
   - Updates preview on every new commit

**Benefits:**

- Test changes before merging to main
- Share previews with team/stakeholders
- Automatic cleanup when PR is closed
- Same environment as production

**Access Preview Deployments:**

- From GitHub PR comments (Vercel bot posts link)
- From Vercel Dashboard → Deployments
- Each commit gets unique preview URL

---

#### Production Deployment Workflow

**Automatic Deployments:**

```bash
# Merge to main branch triggers production deployment
git checkout main
git merge feature/new-challenge
git push origin main

# Vercel automatically:
# 1. Detects push to main
# 2. Builds frontend (pnpm build)
# 3. Deploys to production
# 4. Updates https://data-detective.vercel.app
```

**Manual Deployments:**

```bash
# From Vercel Dashboard
# Deployments → Select deployment → "Promote to Production"

# Or rollback to previous deployment
# Deployments → Select old deployment → "Promote to Production"
```

---

#### Vercel Configuration Reference

**frontend/vercel.json:**

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-url.com/:path*"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        }
      ]
    }
  ],
  "routes": [
    {
      "src": "/[^.]+",
      "dest": "/",
      "status": 200
    }
  ]
}
```

**Configuration Explanations:**

- **rewrites**: Proxy `/api/*` requests to backend (optional, use environment variables instead)
- **headers.assets**: Cache static assets for 1 year (immutable)
- **headers.security**: Security headers (XSS, clickjacking protection)
- **routes**: SPA routing - serve `index.html` for all non-file routes

---

#### Performance Optimization

**1. Enable Edge Caching**

Vercel's CDN automatically caches static assets. Verify caching:

```bash
curl -I https://data-detective.vercel.app/assets/index-abc123.js

# Expected header:
cache-control: public, max-age=31536000, immutable
x-vercel-cache: HIT
```

**2. Analyze Bundle Size**

```bash
cd frontend

# Build and analyze
pnpm build:analyze

# Opens bundle visualization
# dist/stats.html shows chunk sizes
```

**3. Environment-Specific Builds**

Vite automatically optimizes for production:
- Minification (esbuild)
- Tree shaking (removes unused code)
- Code splitting (manual chunks configured)
- Asset optimization (images, fonts)

**4. Monitor Performance**

- Vercel Dashboard → Analytics → Web Vitals
- Tracks: LCP, FID, CLS, TTFB
- Free tier includes basic analytics

---

#### Troubleshooting Vercel Deployments

**Build Fails:**

```bash
# Common issues:
# 1. TypeScript errors
pnpm exec tsc --noEmit  # Run locally to check

# 2. Missing dependencies
pnpm install  # Ensure package.json is up-to-date

# 3. Environment variables not set
# Check Vercel Dashboard → Settings → Environment Variables

# View build logs:
# Vercel Dashboard → Deployments → Select deployment → View logs
```

**404 on Routes:**

If you get 404 errors on routes like `/dashboard`:

```json
// Verify vercel.json has SPA routing:
{
  "routes": [
    {
      "src": "/[^.]+",
      "dest": "/",
      "status": 200
    }
  ]
}
```

**API Connection Issues:**

```bash
# Check VITE_API_URL is set correctly
# Vercel Dashboard → Settings → Environment Variables

# Verify backend CORS allows Vercel domain:
# Backend .env:
ALLOWED_ORIGINS=https://data-detective.vercel.app

# Check browser console for CORS errors
# Open DevTools → Console → Network tab
```

**Slow Cold Starts:**

```bash
# Vercel free tier doesn't have cold starts (unlike serverless functions)
# Frontend is always available (served from CDN)

# If API is slow (Render.com free tier):
# - Backend on Render free tier spins down after 15 minutes
# - First API request may take 30-60 seconds
# - Consider upgrading backend to paid tier ($7/month)
```

**Environment Variables Not Working:**

```bash
# Ensure variables are prefixed with VITE_
VITE_API_URL=...  # ✓ Correct
API_URL=...       # ✗ Won't work

# Redeploy after adding environment variables:
# Vercel Dashboard → Deployments → "Redeploy"
```

**Build Command Fails:**

```bash
# If custom build command fails, verify in vercel.json:
"buildCommand": "pnpm build"  # Not "cd frontend && pnpm build"

# Root Directory should be set to "frontend" in project settings
```

---

#### Vercel Free Tier Limits

**Included in Free Tier:**

- 100GB bandwidth/month
- Unlimited deployments
- Unlimited preview deployments
- Automatic HTTPS/SSL
- Global CDN (edge network)
- 6,000 build minutes/month
- 100 GB-hours serverless function execution
- Web Analytics (basic)

**Limits:**

- Maximum 100 deployments per day
- 3 team members maximum
- Community support only

**When to Upgrade ($20/month Pro):**

- More than 100GB bandwidth needed
- Advanced analytics required
- Password protection for previews
- Custom deployment protection
- Priority support

---

#### Post-Deployment Checklist

After successful Vercel deployment:

- [ ] Frontend accessible at Vercel URL
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active (HTTPS working)
- [ ] Environment variables set correctly
- [ ] Backend CORS updated with Vercel domain
- [ ] API connections working (test login/register)
- [ ] Preview deployments enabled for PRs
- [ ] Build notifications configured (optional)
- [ ] Analytics enabled (optional)
- [ ] Team members invited (if applicable)

---

#### Continuous Deployment Workflow

**Complete CI/CD Pipeline:**

```bash
# 1. Developer creates feature branch
git checkout -b feature/leaderboard-ui

# 2. Make changes, commit, push
git add .
git commit -m "Add leaderboard sorting options"
git push origin feature/leaderboard-ui

# 3. Create pull request on GitHub
# → Vercel automatically creates preview deployment
# → Preview URL posted in PR comments

# 4. Review preview, make changes if needed
# → Every new commit updates the preview

# 5. Merge PR to main
# → Vercel automatically deploys to production
# → https://data-detective.vercel.app updated

# 6. Monitor deployment
# → Vercel Dashboard shows real-time status
# → Rollback available if issues detected
```

---

#### Alternative: Vercel CLI in CI/CD

**GitHub Actions Example:**

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend to Vercel

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        working-directory: frontend
        run: pnpm install

      - name: Build
        working-directory: frontend
        run: pnpm build
        env:
          VITE_API_URL: ${{ secrets.VITE_API_URL }}
          VITE_APP_NAME: Data Detective
          VITE_APP_VERSION: 1.0.0
          VITE_ENV: production

      - name: Deploy to Vercel
        working-directory: frontend
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

---

#### Monitoring and Maintenance

**View Deployment Logs:**

```bash
# Via Dashboard
# Vercel Dashboard → Deployments → Select deployment → Logs

# Via CLI
vercel logs data-detective.vercel.app

# View build logs
vercel logs data-detective.vercel.app --build
```

**Monitor Performance:**

```bash
# Access Web Analytics
# Vercel Dashboard → Analytics

# Key metrics:
# - Visitors (unique, total)
# - Page views
# - Top pages
# - Referrers
# - Devices
```

**Deployment Notifications:**

```bash
# Configure in Vercel Dashboard:
# Settings → Notifications

# Options:
# - Email notifications
# - Slack integration
# - Discord webhook
# - Custom webhooks

# Notification triggers:
# - Deployment started
# - Deployment ready
# - Deployment failed
# - Deployment promoted
```

---

#### Cost Estimation

**Free Tier (Hobby):**
```
100GB bandwidth: $0/month
Unlimited builds: $0/month
Total: $0/month

Good for:
- Personal projects
- Small applications
- Development/testing
- Low to medium traffic
```

**Pro Tier ($20/month):**
```
1TB bandwidth: $20/month
Advanced analytics: Included
Team features: Included
Total: $20/month

Good for:
- Production applications
- Team collaboration
- High traffic sites
- Commercial projects
```

**Expected Usage for Data Detective:**
```
Estimated monthly bandwidth: 10-50GB (within free tier)
- Average page size: 500KB
- Estimated monthly users: 100-1000
- Pages per session: 10
- Bandwidth: 100 users × 10 pages × 500KB = 0.5GB
```

---

## Database Setup

### PostgreSQL Production Setup

```bash
# Create database and user
sudo -u postgres psql

CREATE USER datadetective WITH PASSWORD 'your-secure-password';
CREATE DATABASE datadetective OWNER datadetective;
GRANT ALL PRIVILEGES ON DATABASE datadetective TO datadetective;
\q

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf

# Recommended settings:
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 64MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 2621kB
# min_wal_size = 1GB
# max_wal_size = 4GB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Database Migration

```bash
# Run migrations (if using Alembic)
cd backend
uv run alembic upgrade head

# Or create tables directly
uv run python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

### Database Backups

```bash
# Create backup script
sudo tee /usr/local/bin/backup-datadetective.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/datadetective/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U datadetective datadetective | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

sudo chmod +x /usr/local/bin/backup-datadetective.sh

# Schedule daily backups
sudo crontab -e
# Add line:
0 2 * * * /usr/local/bin/backup-datadetective.sh
```

---

## Environment Variables

### Backend Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key-here              # Generate: openssl rand -hex 32
DATABASE_URL=postgresql://user:pass@host/db  # PostgreSQL connection string

# JWT Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production
DEBUG=False

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional
SENTRY_DSN=your-sentry-dsn                   # Error tracking
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=https://api.yourdomain.com

# Application
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production

# Optional
VITE_SENTRY_DSN=your-sentry-dsn
```

---

## Security Checklist

### Pre-Deployment Security

- [ ] Generate strong `SECRET_KEY` (minimum 32 bytes)
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Enable HTTPS/SSL (Let's Encrypt)
- [ ] Set `DEBUG=False` in production
- [ ] Configure CORS with specific origins
- [ ] Use environment variables (never commit secrets)
- [ ] Set up firewall (UFW or security groups)
- [ ] Configure rate limiting
- [ ] Enable security headers
- [ ] Use strong database passwords
- [ ] Disable PostgreSQL remote access (if not needed)
- [ ] Set up automated backups
- [ ] Configure logging and monitoring
- [ ] Update all dependencies
- [ ] Run security audit: `uv pip audit`

### SSL/TLS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal (already configured by certbot)
sudo systemctl status certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

### Firewall Configuration

```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (only from app server)
sudo ufw allow from APP_SERVER_IP to any port 5432

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Monitoring

### Application Monitoring

#### Sentry (Error Tracking)

```bash
# Backend
uv pip install sentry-sdk[fastapi]
```

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT"),
)
```

```typescript
// Frontend
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.VITE_ENV,
  tracesSampleRate: 0.1,
});
```

#### Health Check Endpoint

```python
# backend/app/main.py
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

#### Uptime Monitoring

Use services like:
- UptimeRobot (free tier available)
- Pingdom
- StatusCake

### Server Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop netdata

# Start Netdata (web dashboard on port 19999)
sudo systemctl start netdata
sudo systemctl enable netdata
```

---

## Backup & Recovery

### Automated Backups

```bash
# Full backup script
sudo tee /usr/local/bin/full-backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/datadetective/backups/$DATE"
mkdir -p $BACKUP_DIR

# Database
pg_dump -U datadetective datadetective | gzip > $BACKUP_DIR/database.sql.gz

# Application files
tar -czf $BACKUP_DIR/app_files.tar.gz /home/datadetective/app

# Environment files
cp /home/datadetective/app/backend/.env $BACKUP_DIR/backend.env
cp /home/datadetective/app/frontend/.env $BACKUP_DIR/frontend.env

# Upload to S3 (optional)
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/$DATE/

echo "Backup completed: $BACKUP_DIR"
EOF

sudo chmod +x /usr/local/bin/full-backup.sh
```

### Recovery Procedure

```bash
# Restore database
gunzip -c backup.sql.gz | psql -U datadetective datadetective

# Restore application
tar -xzf app_files.tar.gz -C /

# Restart services
sudo systemctl restart datadetective-backend
sudo systemctl reload nginx
```

---

## Troubleshooting Deployment

### Backend Won't Start

```bash
# Check service status
sudo systemctl status datadetective-backend

# View logs
sudo journalctl -u datadetective-backend -n 50 --no-pager

# Test manually
cd /home/datadetective/app/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U datadetective -d datadetective -h localhost

# Check PostgreSQL is running
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 502 Bad Gateway (Nginx)

```bash
# Check backend is running
curl http://localhost:8000/health

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx configuration
sudo nginx -t
```

### High Memory Usage

```bash
# Check memory usage
free -h

# Find memory-intensive processes
ps aux --sort=-%mem | head -10

# Reduce Gunicorn workers if needed
# Edit systemd service: --workers 2
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System architecture
- [API Reference](API.md) - API documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

*Last updated: 2025-11-17*
