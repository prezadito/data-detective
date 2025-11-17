# Vercel Deployment Guide - Quick Start

Complete step-by-step guide for deploying Data Detective Academy frontend to Vercel.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deployment (5 Minutes)](#quick-deployment-5-minutes)
- [Detailed Setup](#detailed-setup)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Backend API deployed** (e.g., Render.com, Heroku, AWS)
- ✅ **Backend API URL** (example: `https://data-detective-api.onrender.com`)
- ✅ **GitHub/GitLab account** with repository access
- ✅ **Vercel account** (sign up at https://vercel.com/ - free tier available)

---

## Quick Deployment (5 Minutes)

### Step 1: Create Vercel Account

1. Go to **https://vercel.com/**
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel

### Step 2: Import Project

1. Click **"Add New..."** → **"Project"**
2. Find `data-detective` repository
3. Click **"Import"**

### Step 3: Configure Settings

```
Framework Preset: Vite (auto-detected)
Root Directory: frontend
Build Command: pnpm build
Output Directory: dist
Install Command: pnpm install
```

**IMPORTANT**: Set **Root Directory** to `frontend`

### Step 4: Add Environment Variables

Add these environment variables:

| Variable | Value | Required |
|----------|-------|----------|
| `VITE_API_URL` | Your backend URL | ✅ Yes |
| `VITE_APP_NAME` | `Data Detective` | ⚠️ Optional |
| `VITE_APP_VERSION` | `1.0.0` | ⚠️ Optional |
| `VITE_ENV` | `production` | ⚠️ Optional |

**Example:**
```env
VITE_API_URL=https://data-detective-api.onrender.com
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production
```

### Step 5: Deploy

1. Click **"Deploy"**
2. Wait 2-5 minutes for build
3. Your site is live! 🎉

**Your site URL:**
```
https://data-detective.vercel.app
```

### Step 6: Update Backend CORS

**Critical**: Add Vercel domain to backend CORS settings:

```bash
# Backend environment variables
ALLOWED_ORIGINS=https://data-detective.vercel.app
FRONTEND_URL=https://data-detective.vercel.app
```

Redeploy your backend after updating.

---

## Detailed Setup

### Method 1: Git Integration (Recommended)

#### 1. Prepare Repository

The repository already includes optimized configuration:

**File: `frontend/vercel.json`**
- ✅ SPA routing for React Router
- ✅ Security headers (XSS, CSRF protection)
- ✅ Asset caching (1-year cache)
- ✅ API proxy configuration

#### 2. Import to Vercel

1. Login to Vercel Dashboard
2. Click **"Add New..."** → **"Project"**
3. Select your repository from the list
4. Click **"Import"**

#### 3. Project Configuration

Vercel auto-detects Vite, but verify these settings:

```plaintext
┌─────────────────────────┬────────────────────────┐
│ Setting                 │ Value                  │
├─────────────────────────┼────────────────────────┤
│ Framework Preset        │ Vite                   │
│ Root Directory          │ frontend               │
│ Build Command           │ pnpm build             │
│ Output Directory        │ dist                   │
│ Install Command         │ pnpm install           │
│ Node.js Version         │ 20.x                   │
└─────────────────────────┴────────────────────────┘
```

#### 4. Environment Variables

Click **"Environment Variables"** tab:

**Production:**
```env
VITE_API_URL=https://your-backend-api.onrender.com
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production
```

**Preview (optional):**
```env
VITE_API_URL=https://your-backend-api-preview.onrender.com
VITE_ENV=preview
```

**Development (optional):**
```env
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

#### 5. Deploy

1. Click **"Deploy"**
2. Monitor build logs
3. Wait for completion (2-5 minutes)

**Deployment process:**
```
1. Cloning repository...              ✓
2. Installing dependencies (pnpm)...  ✓
3. Building application...            ✓
4. Optimizing assets...               ✓
5. Deploying to edge network...       ✓
6. Provisioning SSL certificate...    ✓
```

#### 6. Verify Deployment

```bash
# Check if site is live
curl -I https://data-detective.vercel.app

# Expected response
HTTP/2 200
content-type: text/html; charset=utf-8
x-vercel-id: sfo1::xxxxxx-xxxxx
strict-transport-security: max-age=31536000
```

---

### Method 2: Vercel CLI

For advanced users and CI/CD pipelines.

#### 1. Install Vercel CLI

```bash
# Global installation
npm install -g vercel

# Verify installation
vercel --version
```

#### 2. Login

```bash
vercel login
# Opens browser for authentication
```

#### 3. Link Project

```bash
cd frontend

# Link to Vercel project
vercel link

# Prompts:
? Set up and deploy "~/data-detective/frontend"? [Y/n] y
? Which scope do you want to deploy to? Your Name
? Link to existing project? [y/N] n
? What's your project's name? data-detective
? In which directory is your code located? ./
```

#### 4. Set Environment Variables

```bash
# Add production environment variables
vercel env add VITE_API_URL production
# Enter: https://data-detective-api.onrender.com

vercel env add VITE_APP_NAME production
# Enter: Data Detective

vercel env add VITE_APP_VERSION production
# Enter: 1.0.0

vercel env add VITE_ENV production
# Enter: production
```

#### 5. Deploy

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod

# View deployment
vercel ls
```

---

## Custom Domain Setup

### 1. Add Domain in Vercel

1. Go to **Settings** → **Domains**
2. Click **"Add"**
3. Enter domain: `datadetective.academy` or `app.yourdomain.com`

### 2. Configure DNS

Choose one option based on your DNS provider:

**Option A: CNAME Record (Subdomain)**
```dns
Type:  CNAME
Name:  www
Value: cname.vercel-dns.com
TTL:   3600
```

**Option B: A Record (Apex Domain)**
```dns
Type:  A
Name:  @
Value: 76.76.21.21
TTL:   3600
```

**Option C: Vercel Nameservers (Recommended)**
```dns
ns1.vercel-dns.com
ns2.vercel-dns.com
```

### 3. Wait for DNS Propagation

- Propagation time: 5 minutes to 48 hours
- Vercel auto-provisions SSL certificate
- Check status in **Domains** tab

### 4. Verify Custom Domain

```bash
curl -I https://yourdomain.com

# Should show Vercel headers and SSL
```

---

## Post-Deployment

### 1. Test Application

**Manual Testing:**

1. Visit your Vercel URL
2. Test user registration
3. Test login
4. Test SQL challenges
5. Test dashboard
6. Test leaderboard

**Automated Testing:**

```bash
# Check homepage
curl -s https://data-detective.vercel.app | grep "Data Detective"

# Check API connectivity (from browser console)
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)
```

### 2. Update Backend CORS

**Critical Step**: Update backend to allow requests from Vercel domain.

**Backend `.env` file:**
```env
# Add Vercel domain to allowed origins
ALLOWED_ORIGINS=https://data-detective.vercel.app,https://yourdomain.com
FRONTEND_URL=https://data-detective.vercel.app
```

**Redeploy backend** after updating environment variables.

### 3. Enable Preview Deployments

Vercel automatically creates preview deployments for pull requests.

**Test it:**

```bash
# Create feature branch
git checkout -b feature/test-preview

# Make a small change
echo "// Test" >> frontend/src/App.tsx

# Commit and push
git add .
git commit -m "Test preview deployment"
git push origin feature/test-preview

# Create PR on GitHub
# → Vercel bot will comment with preview URL
```

### 4. Configure Notifications (Optional)

1. Go to **Settings** → **Notifications**
2. Choose notification method:
   - Email
   - Slack
   - Discord
   - Webhook
3. Select events:
   - Deployment Started
   - Deployment Ready
   - Deployment Failed

---

## Troubleshooting

### Build Fails

**Error: TypeScript errors**

```bash
# Test locally first
cd frontend
pnpm exec tsc --noEmit

# Fix any type errors
# Then redeploy
```

**Error: Missing dependencies**

```bash
# Verify package.json is committed
git status

# Ensure pnpm-lock.yaml is committed
git add pnpm-lock.yaml
git commit -m "Add lockfile"
git push
```

**Error: Environment variables not set**

```bash
# Check Vercel Dashboard → Settings → Environment Variables
# Ensure VITE_API_URL is set for Production environment

# Redeploy after adding variables:
# Vercel Dashboard → Deployments → Latest → "Redeploy"
```

### 404 on Routes

**Problem:** Routes like `/dashboard` return 404

**Solution:** Verify `vercel.json` has SPA routing:

```json
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

### API Connection Fails

**Problem:** Frontend can't connect to backend

**Checklist:**

```bash
# 1. Check VITE_API_URL is correct
# Vercel Dashboard → Settings → Environment Variables
VITE_API_URL=https://data-detective-api.onrender.com

# 2. Check backend CORS
# Backend .env should include:
ALLOWED_ORIGINS=https://data-detective.vercel.app

# 3. Check backend is running
curl https://data-detective-api.onrender.com/health

# 4. Check browser console for CORS errors
# Open DevTools → Console → Network tab
```

### Environment Variables Not Working

**Problem:** Environment variables not loaded

**Solutions:**

```bash
# 1. Ensure variables are prefixed with VITE_
VITE_API_URL=...  # ✓ Correct
API_URL=...       # ✗ Won't work

# 2. Redeploy after adding variables
# Vercel doesn't automatically rebuild on env changes

# 3. Clear browser cache
# Ctrl+Shift+R or Cmd+Shift+R
```

### Slow Performance

**Problem:** Site loads slowly

**Checks:**

```bash
# 1. Check bundle size
cd frontend
pnpm build:analyze
# Open dist/stats.html

# 2. Verify CDN caching
curl -I https://data-detective.vercel.app/assets/index.js
# Should show: x-vercel-cache: HIT

# 3. Check Web Vitals
# Vercel Dashboard → Analytics → Web Vitals

# 4. If backend is slow (Render.com free tier):
# - Free tier "sleeps" after 15 minutes
# - First request takes 30-60 seconds
# - Consider upgrading to paid tier
```

---

## Advanced Configuration

### Custom Build Configuration

**Custom build script:**

```json
// package.json
{
  "scripts": {
    "build:vercel": "tsc -b && vite build --mode production"
  }
}
```

**Update `vercel.json`:**

```json
{
  "buildCommand": "pnpm build:vercel"
}
```

### API Proxy (Alternative to CORS)

Instead of direct API calls, proxy through Vercel:

**Update `frontend/vercel.json`:**

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://data-detective-api.onrender.com/:path*"
    }
  ]
}
```

**Update frontend API calls:**

```typescript
// frontend/src/services/api.ts
const api = ky.create({
  prefixUrl: '/api', // Use relative path
});
```

**Benefits:**
- No CORS configuration needed
- Hides backend URL from frontend
- Can use Vercel's edge network

### GitHub Actions Integration

**Deploy via GitHub Actions:**

```yaml
# .github/workflows/deploy-vercel.yml
name: Deploy to Vercel

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

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Deploy to Vercel
        working-directory: frontend
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

**Setup secrets:**

```bash
# Get Vercel token
vercel login
# Dashboard → Settings → Tokens → Create

# Add to GitHub:
# Repository → Settings → Secrets → New repository secret
# VERCEL_TOKEN: <your-token>
# VERCEL_ORG_ID: <your-org-id>
# VERCEL_PROJECT_ID: <your-project-id>
```

### Performance Monitoring

**Enable Web Analytics:**

1. Vercel Dashboard → Analytics
2. Tracks automatically (free tier):
   - Page views
   - Unique visitors
   - Top pages
   - Referrers
   - Devices

**Enable Web Vitals:**

1. Already enabled by default
2. Tracks Core Web Vitals:
   - **LCP** (Largest Contentful Paint)
   - **FID** (First Input Delay)
   - **CLS** (Cumulative Layout Shift)
   - **TTFB** (Time to First Byte)

**View metrics:**
```
Dashboard → Analytics → Web Vitals
```

---

## Deployment Checklist

Before deploying:

- [ ] Backend API is deployed and accessible
- [ ] Backend CORS is configured (will update after Vercel deployment)
- [ ] All environment variables are documented
- [ ] TypeScript builds without errors (`pnpm exec tsc --noEmit`)
- [ ] Linting passes (`pnpm lint`)
- [ ] Build succeeds locally (`pnpm build`)

After deploying:

- [ ] Frontend is accessible at Vercel URL
- [ ] SSL certificate is active (HTTPS works)
- [ ] Environment variables are set in Vercel
- [ ] Backend CORS updated with Vercel domain
- [ ] Login/register functionality works
- [ ] API calls succeed (check browser console)
- [ ] All routes work (no 404 errors)
- [ ] Preview deployments enabled for PRs
- [ ] Custom domain configured (if applicable)
- [ ] Team members invited (if applicable)

---

## Cost Summary

### Free Tier (Hobby)

**Included:**
- 100GB bandwidth/month
- Unlimited deployments
- Unlimited preview deployments
- Automatic HTTPS/SSL
- Global CDN
- 6,000 build minutes/month
- Basic Web Analytics

**Limits:**
- Max 100 deployments/day
- Max 3 team members
- Community support only

**Perfect for:**
- Personal projects
- Small classrooms
- Development/testing
- Low to medium traffic

### Pro Tier ($20/month)

**Includes everything in Free, plus:**
- 1TB bandwidth/month
- Advanced analytics
- Password-protected deployments
- Custom deployment protection
- Priority support
- Unlimited team members

**When to upgrade:**
- More than 100GB bandwidth needed
- Large classrooms or schools
- Commercial deployment
- Advanced analytics required

---

## Quick Reference

### Essential Commands

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View deployments
vercel ls

# View logs
vercel logs

# Add environment variable
vercel env add VITE_API_URL production
```

### Important URLs

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Vercel Docs**: https://vercel.com/docs
- **Vercel Status**: https://vercel-status.com
- **Vercel Support**: https://vercel.com/support

### Environment Variables

```env
# Required
VITE_API_URL=https://your-backend-api.onrender.com

# Optional
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0
VITE_ENV=production
```

### Configuration Files

```
frontend/
├── vercel.json          # Vercel configuration
├── .env.example         # Environment template
├── package.json         # Dependencies and scripts
└── vite.config.ts       # Vite configuration
```

---

## Support and Resources

### Documentation

- **Main Deployment Guide**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- **Architecture Guide**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [docs/API.md](API.md)

### Getting Help

**Vercel Issues:**
- Vercel Documentation: https://vercel.com/docs
- Vercel Support: https://vercel.com/support
- Vercel Community: https://github.com/vercel/vercel/discussions

**Application Issues:**
- Check [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review browser console for errors
- Check backend logs for API errors

---

**Last Updated**: 2025-11-17

**Version**: 1.0.0

**Contributors**: Claude AI Assistant
