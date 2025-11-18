# CI/CD Pipeline Documentation

Complete guide to the Data Detective Academy Continuous Integration and Continuous Deployment (CI/CD) pipeline.

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [Backend CI/CD](#backend-cicd)
- [Frontend CI/CD](#frontend-cicd)
- [Local Testing](#local-testing)
- [Interpreting CI Results](#interpreting-ci-results)
- [Deployment Process](#deployment-process)
- [Status Badges](#status-badges)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Overview

### What is CI/CD?

**Continuous Integration (CI)** automatically tests and validates code changes whenever you push to the repository. This ensures code quality and catches bugs early.

**Continuous Deployment (CD)** automatically deploys validated code to production when changes are merged to the main branch.

### Pipeline Goals

Our CI/CD pipeline ensures:
- ✅ All tests pass before merging
- ✅ Code follows linting and formatting standards
- ✅ TypeScript types are correct
- ✅ Builds complete successfully
- ✅ Production deploys only validated code

### Technology Stack

- **CI/CD Platform**: GitHub Actions
- **Backend Deployment**: Render.com (auto-deploy)
- **Frontend Deployment**: Vercel (auto-deploy)
- **Coverage**: Codecov (optional)

---

## Workflow Architecture

### File Structure

```
.github/
└── workflows/
    ├── backend.yml      # Backend CI/CD pipeline
    └── frontend.yml     # Frontend CI/CD pipeline
```

### Workflow Triggers

Both workflows trigger on:
- **Push** to `main`, `develop`, or `claude/**` branches
- **Pull requests** to `main` or `develop` branches
- **Path filters**: Only when relevant files change

### Job Execution Flow

**Backend Workflow**:
```
┌─────────────────────────────┐
│   Push/PR Event             │
│   (backend/** changes)      │
└────────────┬────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   TEST          LINT
   (pytest)      (ruff)
      │             │
      └──────┬──────┘
             │ (both must pass)
             ▼
          DEPLOY
    (main branch only)
```

**Frontend Workflow**:
```
┌─────────────────────────────┐
│   Push/PR Event             │
│   (frontend/** changes)     │
└────────────┬────────────────┘
             │
      ┌──────┴──────┬──────────┬──────────┐
      │             │          │          │
      ▼             ▼          ▼          ▼
    TEST         LINT      TYPECHECK   BUILD
  (vitest)     (eslint)     (tsc)    (vite)
      │             │          │          │
      └──────┬──────┴──────────┴──────────┘
             │ (all must pass)
             ▼
          DEPLOY
    (main branch only)
```

---

## Backend CI/CD

**Workflow File**: `.github/workflows/backend.yml`

### Jobs

#### 1. Test Job

**Purpose**: Run backend test suite with coverage

**Steps**:
1. Checkout code
2. Setup Python 3.13
3. Install `uv` package manager
4. Cache dependencies
5. Install project dependencies
6. Run pytest with coverage
7. Upload coverage to Codecov
8. Save test results as artifacts

**Commands**:
```bash
uv sync --all-extras
uv run pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
```

**Runtime**: ~2-3 minutes
**Matrix**: Python 3.13 only

#### 2. Lint Job

**Purpose**: Check code quality and formatting

**Steps**:
1. Checkout code
2. Setup Python 3.13
3. Install uv and dependencies
4. Run ruff linting
5. Run ruff format check

**Commands**:
```bash
uv run ruff check .
uv run ruff format --check .
```

**Runtime**: ~1-2 minutes

#### 3. Deploy Job

**Purpose**: Notify about deployment

**Triggers**: Only on `main` branch push after all checks pass

**Steps**:
1. Display deployment information
2. Create GitHub commit status

**Notes**:
- Render.com auto-deploys from `main` branch
- No manual trigger needed
- Monitor at: https://dashboard.render.com

---

## Frontend CI/CD

**Workflow File**: `.github/workflows/frontend.yml`

### Jobs

#### 1. Test Job

**Purpose**: Run frontend test suite with coverage

**Steps**:
1. Checkout code
2. Setup pnpm
3. Setup Node.js (matrix: 18, 20)
4. Cache pnpm dependencies
5. Install dependencies (frozen lockfile)
6. Run vitest with coverage
7. Upload coverage (Node 18 only)
8. Save test results as artifacts

**Commands**:
```bash
pnpm install --frozen-lockfile
pnpm test -- --run --coverage
```

**Runtime**: ~3-4 minutes per Node version
**Matrix**: Node 18 and 20 (parallel execution)

#### 2. Lint Job

**Purpose**: Check code quality with ESLint

**Steps**:
1. Checkout code
2. Setup pnpm and Node.js 18
3. Install dependencies
4. Run ESLint

**Commands**:
```bash
pnpm lint
```

**Runtime**: ~2-3 minutes

#### 3. Typecheck Job

**Purpose**: Validate TypeScript types

**Steps**:
1. Checkout code
2. Setup pnpm and Node.js 18
3. Install dependencies
4. Run TypeScript compiler in check mode

**Commands**:
```bash
pnpm exec tsc --noEmit
```

**Runtime**: ~1-2 minutes

#### 4. Build Job

**Purpose**: Verify production build succeeds

**Steps**:
1. Checkout code
2. Setup pnpm and Node.js 18
3. Install dependencies
4. Build with Vite
5. Display build size
6. Upload build artifacts

**Commands**:
```bash
pnpm build
```

**Runtime**: ~2-3 minutes

#### 5. Deploy Job

**Purpose**: Notify about deployment

**Triggers**: Only on `main` branch push after all checks pass

**Steps**:
1. Display deployment information
2. Create GitHub commit status

**Notes**:
- Vercel auto-deploys from `main` branch
- No manual trigger needed
- Monitor at: https://vercel.com/dashboard

---

## Local Testing

### Run Tests Before Pushing

**Backend**:
```bash
cd backend

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=app

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .

# Auto-fix linting issues
uv run ruff check . --fix

# Auto-format code
uv run ruff format .
```

**Frontend**:
```bash
cd frontend

# Install dependencies
pnpm install --frozen-lockfile

# Run tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# Lint
pnpm lint

# Type check
pnpm exec tsc --noEmit

# Build
pnpm build
```

### Pre-commit Checklist

Before pushing code:

**Backend**:
- [ ] Tests pass: `uv run pytest tests/ -v`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Formatting correct: `uv run ruff format --check .`

**Frontend**:
- [ ] Tests pass: `pnpm test -- --run`
- [ ] Linting passes: `pnpm lint`
- [ ] Types valid: `pnpm exec tsc --noEmit`
- [ ] Build succeeds: `pnpm build`

---

## Interpreting CI Results

### Viewing Workflow Runs

1. Go to repository on GitHub
2. Click **Actions** tab
3. Select workflow (Backend CI/CD or Frontend CI/CD)
4. Click on a specific run to see details

### Understanding Job Status

**Status Icons**:
- ✅ **Green check**: Job passed
- ❌ **Red X**: Job failed
- 🟡 **Yellow dot**: Job in progress
- ⚫ **Gray circle**: Job skipped or cancelled

**Job Details**:
- Click on a job to see step-by-step logs
- Failed steps are highlighted in red
- Click step to expand full output

### Common Status Checks

On pull requests, you'll see:
- `backend / Test (Python 3.13)` - Backend tests
- `backend / Lint & Format Check` - Backend linting
- `frontend / Test (Node 18)` - Frontend tests (Node 18)
- `frontend / Test (Node 20)` - Frontend tests (Node 20)
- `frontend / Lint` - Frontend linting
- `frontend / Type Check` - TypeScript validation
- `frontend / Build` - Production build

**All checks must pass** before merging to main.

### Reading Test Failures

**Backend Test Failure**:
```
FAILED tests/test_auth.py::test_login - AssertionError: assert 401 == 200
```
- File: `tests/test_auth.py`
- Test: `test_login`
- Error: Expected 200, got 401

**Frontend Test Failure**:
```
FAIL src/components/LoginForm.test.tsx > LoginForm > renders correctly
AssertionError: expected 'Login' to be in the document
```
- File: `src/components/LoginForm.test.tsx`
- Test: `renders correctly`
- Error: Element not found

### Reading Lint Failures

**Backend Lint Error**:
```
backend/app/main.py:45:88: E501 Line too long (95 > 88)
```
- Fix: Shorten line or split across multiple lines

**Frontend Lint Error**:
```
src/App.tsx
  12:7  error  'useState' is defined but never used  no-unused-vars
```
- Fix: Remove unused import or use the variable

### Coverage Reports

Coverage reports show which code is tested:
- **View**: Check artifacts in workflow run
- **Goal**: Aim for 80%+ coverage
- **Trends**: Monitor coverage changes over time

---

## Deployment Process

### How Deployment Works

**Backend (Render.com)**:
1. CI validates code on PR
2. PR merged to `main` branch
3. Render automatically detects push to `main`
4. Render builds backend: `pip install uv && uv sync --no-dev`
5. Render starts service: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Health check: `/health` endpoint
7. New version goes live

**Frontend (Vercel)**:
1. CI validates code on PR
2. PR merged to `main` branch
3. Vercel automatically detects push to `main`
4. Vercel builds frontend: `pnpm build`
5. Vercel deploys to CDN
6. New version goes live

### Monitoring Deployments

**Render Dashboard**:
- URL: https://dashboard.render.com
- View: Build logs, deployment status, service health
- Features: Manual rollback, environment variables, metrics

**Vercel Dashboard**:
- URL: https://vercel.com/dashboard
- View: Build logs, deployment preview, analytics
- Features: Instant rollback, environment variables, performance metrics

### Deployment Timeline

**Typical deployment**:
1. Push to `main`: Immediate
2. CI validation: 5-10 minutes
3. Platform detection: 1-2 minutes
4. Build process: 3-5 minutes
5. Go live: 1-2 minutes

**Total**: ~10-20 minutes from push to production

### Rollback Procedures

**Render Rollback**:
1. Go to Render dashboard
2. Select service
3. Click **Manual Deploy**
4. Select previous successful deployment
5. Confirm rollback

**Vercel Rollback**:
1. Go to Vercel dashboard
2. Select project
3. Go to **Deployments**
4. Find previous successful deployment
5. Click **...** → **Promote to Production**

### Environment Variables

**Backend** (Render):
- Configured in `render.yaml`
- Override in Render dashboard if needed
- Changes require service restart

**Frontend** (Vercel):
- Set in Vercel dashboard
- Must start with `VITE_`
- Changes require rebuild

---

## Status Badges

### Adding CI Badges to README

**Backend Badge**:
```markdown
[![Backend CI/CD](https://github.com/YOUR_USERNAME/data-detective/actions/workflows/backend.yml/badge.svg)](https://github.com/YOUR_USERNAME/data-detective/actions/workflows/backend.yml)
```

**Frontend Badge**:
```markdown
[![Frontend CI/CD](https://github.com/YOUR_USERNAME/data-detective/actions/workflows/frontend.yml/badge.svg)](https://github.com/YOUR_USERNAME/data-detective/actions/workflows/frontend.yml)
```

**Coverage Badges** (if using Codecov):
```markdown
[![codecov](https://codecov.io/gh/YOUR_USERNAME/data-detective/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/data-detective)
```

### Badge Display

Badges show:
- ✅ **Passing**: All checks successful
- ❌ **Failing**: At least one check failed
- **No status**: Workflow never run

---

## Troubleshooting

### Common Issues

#### Issue: Tests pass locally but fail in CI

**Causes**:
- Environment differences
- Missing environment variables
- Different dependency versions
- Timezone or locale issues

**Solutions**:
- Check CI logs for specific error
- Ensure `.env.example` is complete
- Verify `pnpm-lock.yaml` is committed
- Check for hardcoded paths

#### Issue: Cache not working

**Symptoms**:
- Slow dependency installation
- Always downloading packages

**Solutions**:
- Check cache key matches lock file
- Verify cache path is correct
- Clear cache: Settings → Actions → Caches

#### Issue: Workflow not triggering

**Causes**:
- Path filter doesn't match changes
- Branch not in trigger list
- Workflow file has syntax error

**Solutions**:
- Check path filters in workflow file
- Verify branch name
- Validate YAML syntax: https://www.yamllint.com/

#### Issue: Deploy job not running

**Expected**: Deploy job only runs on `main` branch push

**Verification**:
```yaml
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**Solution**: Merge PR to main to trigger deployment

#### Issue: Python 3.13 not available

**Error**: `Version 3.13 was not found`

**Solutions**:
1. Wait for GitHub Actions to update Python versions
2. Temporarily change to Python 3.11 or 3.12:
   ```yaml
   python-version: '3.11'
   ```

#### Issue: pnpm installation fails

**Error**: `Cannot find module 'pnpm'`

**Solutions**:
- Verify `pnpm-lock.yaml` exists
- Check pnpm version in workflow
- Use `pnpm/action-setup@v3`

### Getting Help

**CI failing?**
1. Read error message in workflow logs
2. Check this troubleshooting guide
3. Search GitHub Actions documentation
4. Ask in project discussions or issues

**Deployment failing?**
1. Check platform dashboard (Render/Vercel)
2. Review deployment logs
3. Verify environment variables
4. Check platform status pages

---

## Maintenance

### Updating Workflows

**When to update**:
- Dependency version changes
- Adding new quality checks
- Platform configuration changes
- Performance optimizations

**How to update**:
1. Edit workflow files in `.github/workflows/`
2. Test changes on feature branch
3. Verify workflows run successfully
4. Merge to main

### Updating Dependencies

**Backend Dependencies**:
```bash
cd backend
uv sync --upgrade  # Update all dependencies
# Or update specific package:
uv add package@latest
```

**Frontend Dependencies**:
```bash
cd frontend
pnpm update  # Update all dependencies
# Or update specific package:
pnpm update package@latest
```

**After updating**:
- Run tests locally
- Commit lock file changes
- Verify CI passes

### Updating GitHub Actions

**Check for updates**:
- GitHub Dependabot may create PRs
- Review Actions marketplace for new versions
- Check changelog for breaking changes

**Example update**:
```yaml
# Before
uses: actions/checkout@v3

# After
uses: actions/checkout@v4
```

### Adding New Checks

**Example: Add security scanning**:

```yaml
security:
  name: Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run Trivy scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
```

**Add to deploy dependencies**:
```yaml
deploy:
  needs: [test, lint, security]
```

### Monitoring CI Performance

**Check metrics**:
- Workflow duration trends
- Cache hit rates
- Job failure rates
- Runner costs (if applicable)

**Optimization tips**:
- Use caching effectively
- Run independent jobs in parallel
- Use matrix sparingly
- Skip unnecessary steps

---

## Best Practices

### For Developers

1. **Test locally first**: Always run tests before pushing
2. **Small commits**: Easier to debug CI failures
3. **Descriptive messages**: Help identify what broke
4. **Watch CI**: Don't assume it passes
5. **Fix immediately**: Don't let broken builds linger

### For Maintainers

1. **Keep workflows simple**: Complexity increases maintenance
2. **Document changes**: Update this guide when changing workflows
3. **Monitor costs**: GitHub Actions has usage limits
4. **Regular updates**: Keep actions and dependencies current
5. **Test workflow changes**: Always test on feature branch first

### Security Considerations

1. **Never commit secrets**: Use GitHub Secrets for sensitive data
2. **Review Dependabot PRs**: Update dependencies promptly
3. **Limit workflow permissions**: Use minimum required permissions
4. **Pin action versions**: Avoid `@main`, use `@v4` tags
5. **Audit third-party actions**: Review code before using

---

## Additional Resources

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Render.com Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Codecov Documentation](https://docs.codecov.io/)

### Related Project Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Manual deployment guide
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guidelines
- [MONITORING.md](./MONITORING.md) - Monitoring and error tracking
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - General troubleshooting

### Tools

- [YAML Validator](https://www.yamllint.com/) - Validate workflow syntax
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions) - Find actions
- [Act](https://github.com/nektos/act) - Run GitHub Actions locally

---

## Changelog

### 2025-11-18
- Initial CI/CD pipeline implementation
- Added backend workflow (test, lint, deploy)
- Added frontend workflow (test, lint, typecheck, build, deploy)
- Integrated Codecov for coverage tracking
- Configured auto-deployment notifications

---

**Questions or issues?** Open an issue on GitHub or refer to the troubleshooting section above.
