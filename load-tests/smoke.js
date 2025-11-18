/**
 * Smoke Test for Data Detective Academy
 *
 * Purpose: Quick verification that all critical endpoints work
 * Load: Minimal (1 VU, 1 minute)
 * Use: After deployments, in CI/CD pipeline
 *
 * Run: k6 run smoke.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Configuration
export const options = {
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests should be below 1s
    http_req_failed: ['rate<0.01'],     // Less than 1% errors
    errors: ['rate<0.01'],
  },
};

// Environment variables
const API_URL = __ENV.API_URL || 'http://localhost:8000';
const STUDENT_EMAIL = __ENV.STUDENT_EMAIL || 'student@example.com';
const STUDENT_PASSWORD = __ENV.STUDENT_PASSWORD || 'password123';

export default function () {
  // Test 1: Health check
  let response = http.get(`${API_URL}/health`);
  check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check has status field': (r) => JSON.parse(r.body).status !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: API info
  response = http.get(`${API_URL}/api/info`);
  check(response, {
    'api info status is 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: Login
  const loginPayload = `username=${STUDENT_EMAIL}&password=${STUDENT_PASSWORD}`;
  response = http.post(`${API_URL}/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  const loginSuccess = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login returns access token': (r) => JSON.parse(r.body).access_token !== undefined,
  });

  if (!loginSuccess) {
    errorRate.add(1);
    return; // Stop test if login fails
  }

  const authToken = JSON.parse(response.body).access_token;
  const authHeaders = {
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  };

  sleep(1);

  // Test 4: Get current user
  response = http.get(`${API_URL}/users/me`, authHeaders);
  check(response, {
    'get user status is 200': (r) => r.status === 200,
    'user has email': (r) => JSON.parse(r.body).email !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 5: Get challenges
  response = http.get(`${API_URL}/challenges`, authHeaders);
  check(response, {
    'get challenges status is 200': (r) => r.status === 200,
    'challenges has units': (r) => JSON.parse(r.body).units !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 6: Get progress
  response = http.get(`${API_URL}/progress/me`, authHeaders);
  check(response, {
    'get progress status is 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // Test 7: Get leaderboard
  response = http.get(`${API_URL}/leaderboard`, authHeaders);
  check(response, {
    'get leaderboard status is 200': (r) => r.status === 200,
    'leaderboard has entries': (r) => JSON.parse(r.body).leaderboard !== undefined,
  }) || errorRate.add(1);

  sleep(2);
}

export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  const green = enableColors ? '\x1b[32m' : '';
  const red = enableColors ? '\x1b[31m' : '';
  const reset = enableColors ? '\x1b[0m' : '';

  let summary = '\n';
  summary += `${indent}✓ Smoke Test Results\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  const checksPassed = checks ? (checks.values.passes / checks.values.value * 100).toFixed(2) : 0;
  const checksColor = checksPassed === '100.00' ? green : red;
  summary += `${indent}Checks Passed: ${checksColor}${checksPassed}%${reset}\n`;

  // HTTP requests
  const httpReqs = data.metrics.http_reqs;
  summary += `${indent}Total Requests: ${httpReqs ? httpReqs.values.count : 0}\n`;

  // Response time
  const duration = data.metrics.http_req_duration;
  if (duration) {
    summary += `${indent}Response Time (avg): ${duration.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}Response Time (p95): ${duration.values['p(95)'].toFixed(2)}ms\n`;
  }

  // Error rate
  const failed = data.metrics.http_req_failed;
  const failedRate = failed ? (failed.values.rate * 100).toFixed(2) : 0;
  const failedColor = failedRate === '0.00' ? green : red;
  summary += `${indent}Error Rate: ${failedColor}${failedRate}%${reset}\n\n`;

  // Pass/Fail
  const passed = checksPassed === '100.00' && failedRate === '0.00';
  const status = passed ? `${green}✓ PASSED${reset}` : `${red}✗ FAILED${reset}`;
  summary += `${indent}Status: ${status}\n`;

  return summary;
}
