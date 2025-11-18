/**
 * Stress Test for Data Detective Academy
 *
 * Purpose: Find system breaking points
 * Load: Progressive increase to 400 VUs
 * Use: Identify performance limits and bottlenecks
 *
 * Run: k6 run stress.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const requestCounter = new Counter('total_requests');

// Configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Warm up
    { duration: '5m', target: 100 },  // Normal load
    { duration: '5m', target: 200 },  // Increasing stress
    { duration: '5m', target: 300 },  // High stress
    { duration: '5m', target: 400 },  // Breaking point
    { duration: '3m', target: 0 },    // Recovery
  ],
  thresholds: {
    http_req_duration: ['p(99)<2000'], // Relaxed threshold for stress test
    errors: ['rate<0.05'],              // Allow up to 5% errors during stress
  },
};

// Environment variables
const API_URL = __ENV.API_URL || 'http://localhost:8000';
const STUDENT_EMAIL = __ENV.STUDENT_EMAIL || `student${randomIntBetween(1, 100)}@example.com`;
const STUDENT_PASSWORD = __ENV.STUDENT_PASSWORD || 'password123';

export default function () {
  requestCounter.add(1);

  // Mix of different request types to simulate real stress
  const requestType = Math.random();

  if (requestType < 0.3) {
    // Health check spam (30%)
    const res = http.get(`${API_URL}/health`);
    check(res, {
      'health check ok': (r) => r.status === 200,
    }) || errorRate.add(1);

  } else if (requestType < 0.6) {
    // Authentication requests (30%)
    const payload = `username=${STUDENT_EMAIL}&password=${STUDENT_PASSWORD}`;
    const res = http.post(`${API_URL}/auth/login`, payload, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    check(res, {
      'login status ok': (r) => r.status === 200 || r.status === 401,
    }) || errorRate.add(1);

    if (res.status === 200) {
      const token = JSON.parse(res.body).access_token;
      const headers = {
        headers: { Authorization: `Bearer ${token}` },
      };

      sleep(0.5);

      // Make authenticated request
      const challengeRes = http.get(`${API_URL}/challenges`, headers);
      check(challengeRes, {
        'challenges ok': (r) => r.status === 200,
      }) || errorRate.add(1);
    }

  } else if (requestType < 0.85) {
    // Leaderboard requests (25%) - tests caching under stress
    const res = http.get(`${API_URL}/leaderboard`, {
      headers: { Authorization: `Bearer dummy-token` },
    });

    check(res, {
      'leaderboard request completed': (r) => r.status === 200 || r.status === 401,
    }) || errorRate.add(1);

  } else {
    // Landing page requests (15%)
    const res = http.get(`${API_URL}/`);
    check(res, {
      'landing page ok': (r) => r.status === 200,
    }) || errorRate.add(1);
  }

  // Variable sleep time based on load
  const vus = __VU;
  if (vus < 100) {
    sleep(randomIntBetween(1, 3));
  } else if (vus < 200) {
    sleep(randomIntBetween(0.5, 2));
  } else if (vus < 300) {
    sleep(randomIntBetween(0.2, 1));
  } else {
    sleep(randomIntBetween(0.1, 0.5)); // High stress - rapid requests
  }
}

export function handleSummary(data) {
  const metrics = data.metrics;

  console.log('\n' + '='.repeat(80));
  console.log('STRESS TEST SUMMARY');
  console.log('='.repeat(80));

  // Performance degradation analysis
  const avgDuration = metrics.http_req_duration.values.avg;
  const p95Duration = metrics.http_req_duration.values['p(95)'];
  const p99Duration = metrics.http_req_duration.values['p(99)'];
  const maxDuration = metrics.http_req_duration.values.max;

  console.log('\nResponse Times:');
  console.log(`  Average: ${avgDuration.toFixed(2)}ms`);
  console.log(`  P95: ${p95Duration.toFixed(2)}ms`);
  console.log(`  P99: ${p99Duration.toFixed(2)}ms`);
  console.log(`  Max: ${maxDuration.toFixed(2)}ms`);

  // Error analysis
  const totalReqs = metrics.http_reqs.values.count;
  const failedReqs = metrics.http_req_failed.values.rate * totalReqs;
  const errorRatePercent = (metrics.http_req_failed.values.rate * 100).toFixed(2);

  console.log('\nReliability:');
  console.log(`  Total Requests: ${totalReqs}`);
  console.log(`  Failed Requests: ${failedReqs.toFixed(0)}`);
  console.log(`  Error Rate: ${errorRatePercent}%`);

  // Throughput
  const duration = data.state.testRunDurationMs / 1000;
  const throughput = (totalReqs / duration).toFixed(2);

  console.log('\nThroughput:');
  console.log(`  Requests/Second: ${throughput}`);
  console.log(`  Test Duration: ${(duration / 60).toFixed(2)} minutes`);

  // Breaking point analysis
  console.log('\nStress Analysis:');
  if (p99Duration > 2000) {
    console.log('  ⚠️  P99 response time exceeded 2s - system under heavy stress');
  } else {
    console.log('  ✓ P99 response time within acceptable range');
  }

  if (errorRatePercent > 5) {
    console.log(`  ⚠️  Error rate ${errorRatePercent}% exceeds 5% threshold`);
  } else {
    console.log('  ✓ Error rate within acceptable range');
  }

  // Recommendations
  console.log('\nRecommendations:');
  if (avgDuration > 500) {
    console.log('  • Consider adding more server resources');
    console.log('  • Review database query performance');
    console.log('  • Increase connection pool size');
  }
  if (p95Duration > 1000) {
    console.log('  • Implement additional caching');
    console.log('  • Optimize slow endpoints');
  }
  if (errorRatePercent > 1) {
    console.log('  • Review error logs for failure patterns');
    console.log('  • Check for connection pool exhaustion');
    console.log('  • Verify rate limiting configuration');
  }

  console.log('='.repeat(80) + '\n');

  return {
    'stress-test-results.json': JSON.stringify(data, null, 2),
  };
}
