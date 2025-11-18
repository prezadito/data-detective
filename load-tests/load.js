/**.
 * Load Test for Data Detective Academy
 *
 * Purpose: Simulate expected production load
 * Load: 100 VUs, 17 minutes total
 * Scenarios: Student (50%), Anonymous (30%), Auth (15%), Teacher (5%)
 *
 * Run: k6 run load.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const challengeDuration = new Trend('challenge_duration');
const leaderboardDuration = new Trend('leaderboard_duration');
const submissionCounter = new Counter('challenge_submissions');

// Configuration
export const options = {
  stages: [
    { duration: '5m', target: 100 },  // Ramp up to 100 VUs
    { duration: '10m', target: 100 }, // Stay at 100 VUs
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // Response time thresholds
    http_req_failed: ['rate<0.01'],                 // Less than 1% errors
    errors: ['rate<0.01'],
    login_duration: ['p(95)<500'],
    challenge_duration: ['p(95)<1000'],
    leaderboard_duration: ['p(95)<2000'],
  },
};

// Environment variables
const API_URL = __ENV.API_URL || 'http://localhost:8000';
const STUDENT_EMAIL = __ENV.STUDENT_EMAIL || 'student@example.com';
const STUDENT_PASSWORD = __ENV.STUDENT_PASSWORD || 'password123';
const TEACHER_EMAIL = __ENV.TEACHER_EMAIL || 'teacher@example.com';
const TEACHER_PASSWORD = __ENV.TEACHER_PASSWORD || 'password123';

// Test scenarios weighted by realistic usage
export default function () {
  const scenario = weightedChoice([
    { weight: 50, fn: studentScenario },
    { weight: 30, fn: anonymousScenario },
    { weight: 15, fn: authScenario },
    { weight: 5, fn: teacherScenario },
  ]);

  scenario();
}

/**
 * Student scenario: View challenges, submit solutions, check progress
 */
function studentScenario() {
  group('Student Workflow', function () {
    // Login
    const token = login(STUDENT_EMAIL, STUDENT_PASSWORD);
    if (!token) {
      return;
    }

    const headers = {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    sleep(randomIntBetween(1, 3));

    // View challenges
    group('View Challenges', function () {
      const start = Date.now();
      const res = http.get(`${API_URL}/challenges`, headers);
      challengeDuration.add(Date.now() - start);

      check(res, {
        'challenges loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(2, 5));

    // View specific challenge
    const unitId = randomIntBetween(1, 3);
    const challengeId = randomIntBetween(1, 3);

    group('View Challenge Details', function () {
      const res = http.get(
        `${API_URL}/challenges/${unitId}/${challengeId}`,
        headers
      );

      check(res, {
        'challenge details loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(10, 30)); // Student thinks about solution

    // Submit solution (30% chance)
    if (Math.random() < 0.3) {
      group('Submit Solution', function () {
        const queries = [
          'SELECT * FROM users',
          'SELECT name, email FROM users WHERE role = "student"',
          'SELECT COUNT(*) FROM users',
        ];

        const payload = JSON.stringify({
          unit_id: unitId,
          challenge_id: challengeId,
          query: queries[randomIntBetween(0, queries.length - 1)],
        });

        const res = http.post(`${API_URL}/progress/submit`, payload, headers);
        submissionCounter.add(1);

        check(res, {
          'solution submitted': (r) => r.status === 200 || r.status === 400,
        }) || errorRate.add(1);
      });

      sleep(randomIntBetween(2, 5));
    }

    // Check progress
    group('Check Progress', function () {
      const res = http.get(`${API_URL}/progress/me`, headers);

      check(res, {
        'progress loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(1, 3));

    // View leaderboard (20% chance)
    if (Math.random() < 0.2) {
      group('View Leaderboard', function () {
        const start = Date.now();
        const res = http.get(`${API_URL}/leaderboard`, headers);
        leaderboardDuration.add(Date.now() - start);

        check(res, {
          'leaderboard loaded': (r) => r.status === 200,
        }) || errorRate.add(1);
      });

      sleep(randomIntBetween(2, 5));
    }

    // Check profile
    group('View Profile', function () {
      const res = http.get(`${API_URL}/users/me`, headers);

      check(res, {
        'profile loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(1, 3));
  });
}

/**
 * Anonymous scenario: View landing page, browse public content
 */
function anonymousScenario() {
  group('Anonymous User', function () {
    // View landing page
    group('Landing Page', function () {
      const res = http.get(`${API_URL}/`);

      check(res, {
        'landing page loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(2, 5));

    // View features page
    group('Features Page', function () {
      const res = http.get(`${API_URL}/features`);

      check(res, {
        'features page loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(3, 8));

    // View pricing page
    group('Pricing Page', function () {
      const res = http.get(`${API_URL}/pricing`);

      check(res, {
        'pricing page loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(2, 5));
  });
}

/**
 * Authentication scenario: Register, login, password reset
 */
function authScenario() {
  group('Authentication Flow', function () {
    const scenario = Math.random();

    if (scenario < 0.6) {
      // Login (60%)
      group('Login', function () {
        login(STUDENT_EMAIL, STUDENT_PASSWORD);
      });

      sleep(randomIntBetween(1, 3));

    } else if (scenario < 0.9) {
      // Login and logout (30%)
      group('Login and Logout', function () {
        const loginRes = login(STUDENT_EMAIL, STUDENT_PASSWORD);
        if (!loginRes) return;

        sleep(randomIntBetween(5, 10));

        const token = loginRes;
        const refreshToken = loginRes; // In real scenario, extract from response

        // Logout
        const payload = JSON.stringify({ refresh_token: refreshToken });
        const res = http.post(`${API_URL}/auth/logout`, payload, {
          headers: { 'Content-Type': 'application/json' },
        });

        check(res, {
          'logout successful': (r) => r.status === 200,
        }) || errorRate.add(1);
      });

    } else {
      // Token refresh (10%)
      group('Token Refresh', function () {
        // First login to get tokens
        const loginPayload = `username=${STUDENT_EMAIL}&password=${STUDENT_PASSWORD}`;
        const loginRes = http.post(`${API_URL}/auth/login`, loginPayload, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        if (loginRes.status === 200) {
          const tokens = JSON.parse(loginRes.body);

          sleep(randomIntBetween(1, 2));

          // Refresh token
          const refreshPayload = JSON.stringify({
            refresh_token: tokens.refresh_token,
          });

          const refreshRes = http.post(`${API_URL}/auth/refresh`, refreshPayload, {
            headers: { 'Content-Type': 'application/json' },
          });

          check(refreshRes, {
            'token refreshed': (r) => r.status === 200,
          }) || errorRate.add(1);
        }
      });
    }

    sleep(randomIntBetween(1, 3));
  });
}

/**
 * Teacher scenario: View analytics, export data
 */
function teacherScenario() {
  group('Teacher Workflow', function () {
    // Login as teacher
    const token = login(TEACHER_EMAIL, TEACHER_PASSWORD);
    if (!token) {
      return;
    }

    const headers = {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    sleep(randomIntBetween(1, 3));

    // View students list
    group('View Students', function () {
      const res = http.get(`${API_URL}/users?limit=50`, headers);

      check(res, {
        'students list loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(2, 5));

    // View class analytics
    group('View Analytics', function () {
      const res = http.get(`${API_URL}/analytics/class`, headers);

      check(res, {
        'analytics loaded': (r) => r.status === 200,
      }) || errorRate.add(1);
    });

    sleep(randomIntBetween(3, 8));

    // View specific student progress (20% chance)
    if (Math.random() < 0.2) {
      group('View Student Progress', function () {
        // Use a known student ID (in real test, would be dynamic)
        const studentId = randomIntBetween(1, 100);
        const res = http.get(`${API_URL}/progress/user/${studentId}`, headers);

        check(res, {
          'student progress loaded': (r) => r.status === 200 || r.status === 404,
        }) || errorRate.add(1);
      });

      sleep(randomIntBetween(2, 5));
    }

    // Export data (10% chance)
    if (Math.random() < 0.1) {
      group('Export Data', function () {
        const res = http.get(`${API_URL}/export/students`, headers);

        check(res, {
          'data exported': (r) => r.status === 200,
          'csv returned': (r) => r.headers['Content-Type'].includes('text/csv'),
        }) || errorRate.add(1);
      });

      sleep(randomIntBetween(1, 3));
    }
  });
}

/**
 * Helper: Login and return auth token
 */
function login(email, password) {
  const start = Date.now();
  const payload = `username=${email}&password=${password}`;
  const res = http.post(`${API_URL}/auth/login`, payload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  loginDuration.add(Date.now() - start);

  const success = check(res, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => JSON.parse(r.body).access_token !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    return null;
  }

  return JSON.parse(res.body).access_token;
}

/**
 * Helper: Weighted random choice
 */
function weightedChoice(choices) {
  const totalWeight = choices.reduce((sum, choice) => sum + choice.weight, 0);
  let random = Math.random() * totalWeight;

  for (const choice of choices) {
    random -= choice.weight;
    if (random <= 0) {
      return choice.fn;
    }
  }

  return choices[0].fn;
}

// Summary handler
export function handleSummary(data) {
  const passed = data.metrics.http_req_failed.values.rate < 0.01 &&
                 data.metrics.http_req_duration.values['p(95)'] < 500;

  console.log('\n' + '='.repeat(80));
  console.log('LOAD TEST SUMMARY');
  console.log('='.repeat(80));
  console.log(`Status: ${passed ? '✓ PASSED' : '✗ FAILED'}`);
  console.log(`Total Requests: ${data.metrics.http_reqs.values.count}`);
  console.log(`Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`);
  console.log(`Avg Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`);
  console.log(`P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
  console.log(`P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms`);
  console.log(`Challenge Submissions: ${data.metrics.challenge_submissions.values.count}`);
  console.log('='.repeat(80) + '\n');

  return {
    'summary.json': JSON.stringify(data, null, 2),
  };
}
