import { test as base, Page } from '@playwright/test';

/**
 * Test user credentials for E2E tests
 *
 * IMPORTANT: These users must exist in the backend database before running tests.
 * You can create them by:
 * 1. Starting the backend server
 * 2. Navigating to http://localhost:3000/register
 * 3. Creating users with these credentials
 */
export const TEST_USERS = {
  student: {
    email: 'e2e-student@test.com',
    password: 'Test123!',
    name: 'E2E Test Student',
    role: 'student' as const,
  },
  teacher: {
    email: 'e2e-teacher@test.com',
    password: 'Test123!',
    name: 'E2E Test Teacher',
    role: 'teacher' as const,
  },
};

/**
 * Custom test fixtures for authenticated contexts
 */
type AuthFixtures = {
  /**
   * Page context with authenticated student session
   * Automatically logs in as a student before each test
   */
  authenticatedStudent: Page;

  /**
   * Page context with authenticated teacher session
   * Automatically logs in as a teacher before each test
   */
  authenticatedTeacher: Page;

  /**
   * Test user credentials (for manual login)
   */
  testUsers: typeof TEST_USERS;
};

/**
 * Helper function to perform login
 */
async function login(page: Page, email: string, password: string): Promise<void> {
  // Navigate to login page
  await page.goto('/login');

  // Wait for login form to be visible
  await page.waitForSelector('input[type="email"]', { state: 'visible' });

  // Fill in credentials
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for navigation to complete (either to /practice for students or /teacher/dashboard for teachers)
  await page.waitForURL(/\/(practice|teacher\/dashboard)/, { timeout: 10000 });

  // Verify authentication token exists in localStorage
  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  if (!token) {
    throw new Error('Login failed: No access token found in localStorage');
  }
}

/**
 * Helper function to check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  return token !== null;
}

/**
 * Helper function to logout
 */
export async function logout(page: Page): Promise<void> {
  await page.evaluate(() => localStorage.clear());
}

/**
 * Extend base test with custom fixtures
 */
export const test = base.extend<AuthFixtures>({
  /**
   * Fixture: Authenticated student context
   */
  authenticatedStudent: async ({ page }, use) => {
    // Setup: Login as student
    await login(page, TEST_USERS.student.email, TEST_USERS.student.password);

    // Provide page to test
    await use(page);

    // Teardown: Clear authentication
    await logout(page);
  },

  /**
   * Fixture: Authenticated teacher context
   */
  authenticatedTeacher: async ({ page }, use) => {
    // Setup: Login as teacher
    await login(page, TEST_USERS.teacher.email, TEST_USERS.teacher.password);

    // Provide page to test
    await use(page);

    // Teardown: Clear authentication
    await logout(page);
  },

  /**
   * Fixture: Test user credentials
   */
  testUsers: async ({}, use) => {
    await use(TEST_USERS);
  },
});

export { expect } from '@playwright/test';
