# Load Testing Guide

Comprehensive load testing for Data Detective Academy using k6.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Running Tests](#running-tests)
- [Interpreting Results](#interpreting-results)
- [Performance Targets](#performance-targets)
- [Troubleshooting](#troubleshooting)

---

## Overview

This directory contains k6 load testing scripts for Data Detective Academy. These tests verify the application can handle expected production load and identify performance bottlenecks.

### Test Types

1. **Smoke Test** (`smoke.js`): Quick verification with minimal load
2. **Load Test** (`load.js`): Expected production load over sustained period
3. **Stress Test** (`stress.js`): Push beyond normal load to find breaking points
4. **Spike Test** (`spike.js`): Sudden traffic spikes
5. **Authentication Test** (`auth-load.js`): Focus on auth endpoints
6. **API Test** (`api-load.js`): Focus on API endpoints

---

## Prerequisites

### Install k6

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Windows:**
```powershell
choco install k6
```

**Docker:**
```bash
docker pull grafana/k6
```

### Environment Setup

Create `.env` file in this directory:

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

Example `.env`:
```
API_URL=http://localhost:8000
# Or production:
# API_URL=https://your-api.onrender.com

STUDENT_EMAIL=student@example.com
STUDENT_PASSWORD=password123
TEACHER_EMAIL=teacher@example.com
TEACHER_PASSWORD=password123
```

---

## Quick Start

### 1. Start Backend Locally

```bash
cd ../backend
uvicorn app.main:app --reload
```

### 2. Run Smoke Test

```bash
cd load-tests
k6 run smoke.js
```

Expected output:
```
     ✓ status was 200
     ✓ transaction time < 1000ms

     checks.........................: 100.00% ✓ 10       ✗ 0
     data_received..................: 5.2 kB  520 B/s
     data_sent......................: 1.8 kB  180 B/s
     http_req_duration..............: avg=150ms  min=100ms  max=200ms
     http_reqs......................: 10      1/s
     vus............................: 1       min=1      max=1
```

### 3. Run Full Load Test

```bash
k6 run load.js
```

---

## Test Scenarios

### Smoke Test (`smoke.js`)

**Purpose**: Verify basic functionality with minimal load

**Load**:
- 1 virtual user
- 1 minute duration
- Tests all critical endpoints

**Run**:
```bash
k6 run smoke.js
```

**Use When**:
- After deploying new code
- Quick sanity check
- CI/CD pipeline

---

### Load Test (`load.js`)

**Purpose**: Simulate expected production load

**Load**:
- Ramp up to 100 virtual users over 5 minutes
- Sustain 100 users for 10 minutes
- Ramp down to 0 over 2 minutes
- **Total**: 17 minutes

**Scenarios**:
- 50% student activity (view challenges, submit solutions)
- 30% anonymous users (view landing page)
- 15% authentication (login, register)
- 5% teacher activity (view analytics, export data)

**Run**:
```bash
k6 run load.js
```

**Run with Docker**:
```bash
docker run --rm -i -e API_URL=http://host.docker.internal:8000 \
  -v $(pwd):/scripts \
  grafana/k6 run /scripts/load.js
```

---

### Stress Test (`stress.js`)

**Purpose**: Find breaking points and limits

**Load**:
- Ramp up to 200 virtual users over 10 minutes
- Sustain 200 users for 5 minutes
- Ramp up to 400 users over 5 minutes
- Sustain 400 users for 5 minutes
- Ramp down to 0 over 2 minutes
- **Total**: 27 minutes

**Run**:
```bash
k6 run stress.js
```

**What to Watch**:
- When do response times start degrading?
- At what point do errors occur?
- Does the system recover after load decreases?

---

### Spike Test (`spike.js`)

**Purpose**: Test sudden traffic spikes (e.g., all students login at class start)

**Load**:
- Start with 10 users
- Spike to 200 users instantly
- Sustain 200 users for 2 minutes
- Drop to 10 users
- **Total**: 5 minutes

**Run**:
```bash
k6 run spike.js
```

**Scenarios**:
- All students login at once (e.g., class starts)
- Teacher releases new challenge
- Leaderboard spike before deadline

---

### Authentication Load Test (`auth-load.js`)

**Purpose**: Test authentication system under load

**Load**:
- 50 virtual users
- 5 minute duration
- Focus on auth endpoints

**Endpoints Tested**:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- POST /auth/password-reset-request

**Run**:
```bash
k6 run auth-load.js
```

---

### API Load Test (`api-load.js`)

**Purpose**: Test all API endpoints systematically

**Load**:
- 100 virtual users
- 10 minute duration

**Endpoints Tested**:
- All public endpoints
- All authenticated endpoints
- All teacher endpoints

**Run**:
```bash
k6 run api-load.js
```

---

## Running Tests

### Basic Execution

```bash
# Run test
k6 run load.js

# Run with custom duration
k6 run --duration 30s smoke.js

# Run with custom VUs
k6 run --vus 50 load.js

# Run with environment variables
k6 run -e API_URL=https://your-api.com load.js
```

### Advanced Options

```bash
# Output results to JSON
k6 run --out json=results.json load.js

# Output to InfluxDB (for Grafana visualization)
k6 run --out influxdb=http://localhost:8086/k6 load.js

# Set thresholds
k6 run --threshold "http_req_duration<500" load.js

# Quiet mode (less output)
k6 run --quiet load.js

# Verbose mode (more output)
k6 run --verbose load.js
```

### Cloud Execution (k6 Cloud)

```bash
# Login to k6 Cloud
k6 login cloud

# Run test in cloud
k6 cloud load.js

# Benefits: Distributed load from multiple locations
```

---

## Interpreting Results

### Key Metrics

#### HTTP Metrics

**`http_req_duration`**: Request duration (response time)
- **avg**: Average response time
- **min**: Fastest response
- **max**: Slowest response
- **med**: Median (50th percentile)
- **p(90)**: 90th percentile (90% of requests faster than this)
- **p(95)**: 95th percentile
- **p(99)**: 99th percentile

**Target**:
- avg < 200ms ✅
- p(95) < 500ms ✅
- p(99) < 1s ✅

**`http_req_failed`**: Percentage of failed requests
- **Target**: < 0.1% (1 in 1000 requests)

**`http_reqs`**: Total number of HTTP requests
- Higher is better (more throughput)

#### Virtual User Metrics

**`vus`**: Number of active virtual users
- Shows current load level

**`vus_max`**: Maximum virtual users reached

#### Data Transfer

**`data_received`**: Data downloaded from server
- Shows bandwidth usage

**`data_sent`**: Data uploaded to server

#### Checks

**`checks`**: Percentage of successful assertions
- **Target**: 100% ✅

**Example**:
```javascript
check(response, {
  'status is 200': (r) => r.status === 200,
  'response time < 500ms': (r) => r.timings.duration < 500,
});
```

### Sample Output

```
     ✓ status was 200
     ✓ response time < 500ms
     ✓ leaderboard returned data

     checks.........................: 100.00% ✓ 15234    ✗ 0
     data_received..................: 52 MB   870 kB/s
     data_sent......................: 8.1 MB  135 kB/s
     http_req_blocked...............: avg=1.2ms    min=0s    max=500ms  p(95)=2ms
     http_req_connecting............: avg=500µs    min=0s    max=200ms  p(95)=1ms
     http_req_duration..............: avg=180ms    min=50ms  max=2s     p(95)=400ms
       { expected_response:true }...: avg=180ms    min=50ms  max=2s     p(95)=400ms
     http_req_failed................: 0.00%   ✓ 0        ✗ 15234
     http_req_receiving.............: avg=1ms      min=100µs max=50ms   p(95)=5ms
     http_req_sending...............: avg=500µs    min=50µs  max=20ms   p(95)=2ms
     http_req_tls_handshaking.......: avg=0s       min=0s    max=0s     p(95)=0s
     http_req_waiting...............: avg=178ms    min=50ms  max=1.9s   p(95)=395ms
     http_reqs......................: 15234   254.23/s
     iteration_duration.............: avg=390ms    min=250ms max=3s     p(95)=800ms
     iterations.....................: 15234   254.23/s
     vus............................: 100     min=0      max=100
     vus_max........................: 100     min=100    max=100
```

### Interpreting This Output

✅ **Good Signs**:
- All checks passing (100%)
- http_req_failed = 0%
- avg response time = 180ms (< 200ms target)
- p(95) = 400ms (< 500ms target)
- Sustained 254 requests/second

⚠️ **Warning Signs**:
- max response time = 2s (investigate slowest requests)

### What to Look For

**Performance Degradation**:
- Response times increasing over test duration
- Indicates memory leaks, connection pool exhaustion

**Error Rate**:
- Any non-zero error rate requires investigation
- Check error messages in output

**Throughput**:
- Requests/second should remain constant
- Decreasing throughput indicates bottleneck

---

## Performance Targets

### Response Time Targets

| Endpoint Type | Target (avg) | Target (p95) | Target (p99) |
|---------------|--------------|--------------|--------------|
| Health Check  | < 50ms       | < 100ms      | < 200ms      |
| Authentication| < 300ms      | < 500ms      | < 1s         |
| List Endpoints| < 200ms      | < 500ms      | < 1s         |
| Challenge Submit | < 500ms   | < 1s         | < 2s         |
| Analytics     | < 1s         | < 2s         | < 3s         |

### Throughput Targets

| Scenario | Target |
|----------|--------|
| Concurrent Users | 100+ |
| Requests/Second | 100+ |
| Login Requests/Second | 10+ |
| Challenge Submissions/Minute | 50+ |

### Reliability Targets

| Metric | Target |
|--------|--------|
| Error Rate | < 0.1% |
| Uptime | 99.9% |
| Success Rate | > 99.9% |

---

## Troubleshooting

### High Response Times

**Symptoms**:
- avg > 1s
- p(95) > 2s

**Possible Causes**:
1. Database slow queries
2. No database indexes
3. No caching
4. Network latency

**Solutions**:
```bash
# Check database performance
# See slow query logs
# Add indexes where needed

# Enable caching
# Leaderboard, analytics already cached

# Check database connection pool
# May need to increase pool size
```

### High Error Rate

**Symptoms**:
- http_req_failed > 1%
- checks < 100%

**Possible Causes**:
1. Rate limiting triggered
2. Database connection pool exhausted
3. Memory limit reached
4. Application crashes

**Solutions**:
```bash
# Check application logs
docker logs backend-container

# Check Sentry for errors
# Visit Sentry dashboard

# Increase rate limits
# Or reduce test load

# Check memory usage
free -h
docker stats
```

### Failed Checks

**Symptoms**:
- Specific checks failing
- e.g., "status was 200" = 90%

**Debug**:
```javascript
// Add console.log to see actual response
check(response, {
  'status is 200': (r) => {
    if (r.status !== 200) {
      console.log(`Expected 200, got ${r.status}: ${r.body}`);
    }
    return r.status === 200;
  },
});
```

### Connection Refused

**Error**: `dial: connection refused`

**Causes**:
1. Backend not running
2. Wrong API_URL
3. Firewall blocking connections

**Solutions**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check API_URL environment variable
echo $API_URL

# Try with explicit URL
k6 run -e API_URL=http://localhost:8000 load.js
```

---

## Best Practices

### Before Testing

1. **Use Production-Like Environment**
   - Same hardware specs
   - Same database size
   - Same network conditions

2. **Prepare Test Data**
   - Create test users beforehand
   - Seed database with realistic data
   - Don't test against production database

3. **Monitor During Tests**
   - Open monitoring dashboards
   - Watch server metrics (CPU, memory, disk)
   - Check database performance

### During Testing

1. **Start Small**
   - Run smoke test first
   - Gradually increase load
   - Don't jump straight to stress test

2. **Watch for Issues**
   - Monitor error rates
   - Check response times
   - Look for memory leaks

3. **Document Results**
   - Save output to file
   - Take screenshots of dashboards
   - Note any issues observed

### After Testing

1. **Analyze Results**
   - Identify bottlenecks
   - Check for anomalies
   - Compare against targets

2. **Optimize**
   - Fix identified issues
   - Add indexes, caching, etc.
   - Re-run tests to verify improvements

3. **Document Findings**
   - Update performance baseline
   - Share results with team
   - Update deployment guides

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/load-test.yml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run Load Test
        run: |
          cd load-tests
          k6 run --out json=results.json \
            -e API_URL=${{ secrets.STAGING_API_URL }} \
            load.js

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load-tests/results.json
```

---

## Additional Resources

### K6 Documentation
- Official Docs: https://k6.io/docs/
- Examples: https://k6.io/docs/examples/
- API Reference: https://k6.io/docs/javascript-api/

### Grafana Integration
- K6 + Grafana: https://k6.io/docs/results-output/real-time/grafana/
- Example Dashboard: https://grafana.com/grafana/dashboards/2587

### Performance Testing Guide
- Google Web Performance: https://web.dev/performance/
- MDN Performance: https://developer.mozilla.org/en-US/docs/Web/Performance

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
