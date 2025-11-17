import { test, expect, TEST_USERS } from './fixtures/auth';
import {
  waitForNavigation,
  waitForAPICall,
  clearLocalStorage,
  getLocalStorageItem,
  waitForLoadingToComplete,
} from './support/helpers';

/**
 * Student E2E Test Suite
 *
 * Tests the complete student user journey:
 * - Registration and authentication
 * - Challenge solving workflow
 * - Progress tracking
 * - Leaderboard interaction
 */

test.describe('Student Authentication Flow', () => {
  test('should allow user registration with valid details', async ({ page }) => {
    // Navigate to register page
    await page.goto('/register');

    // Generate unique email for this test run
    const uniqueEmail = `student-${Date.now()}@test.com`;

    // Fill registration form
    await page.fill('input[name="name"]', 'New Test Student');
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', 'Test123!');

    // Select student role (if role selector exists)
    const roleSelector = page.locator('select[name="role"]');
    if (await roleSelector.count() > 0) {
      await roleSelector.selectOption('student');
    }

    // Submit registration
    await page.click('button[type="submit"]');

    // Should redirect to login page or show success message
    await expect(page).toHaveURL(/\/(login|practice)/, { timeout: 10000 });
  });

  test('should login with valid credentials', async ({ page, testUsers }) => {
    // Clear any existing auth
    await clearLocalStorage(page);

    // Navigate to login page
    await page.goto('/login');

    // Fill login form
    await page.fill('input[type="email"]', testUsers.student.email);
    await page.fill('input[type="password"]', testUsers.student.password);

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation to practice page
    await waitForNavigation(page, /\/practice/);

    // Verify access token in localStorage
    const token = await getLocalStorageItem(page, 'access_token');
    expect(token).not.toBeNull();

    // Verify user name appears in navigation
    await expect(page.getByText(testUsers.student.name)).toBeVisible();
  });

  test('should redirect to login when accessing protected route while not authenticated', async ({
    page,
  }) => {
    // Clear authentication
    await clearLocalStorage(page);

    // Try to access practice page directly
    await page.goto('/practice');

    // Should redirect to login
    await waitForNavigation(page, /\/login/);
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show error for invalid login credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await page.fill('input[type="email"]', 'invalid@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');

    // Submit login
    await page.click('button[type="submit"]');

    // Should show error message (toast or inline error)
    await expect(
      page.locator('text=/invalid.*credentials|login.*failed/i')
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Challenge Solving Flow', () => {
  test('should display challenge with all required elements', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to practice page
    await page.goto('/practice');
    await waitForLoadingToComplete(page);

    // Should show unit selector
    await expect(page.getByRole('button', { name: /unit 1/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /unit 2/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /unit 3/i })).toBeVisible();

    // Should show challenge indicator
    await expect(page.getByText(/challenge 1 of/i)).toBeVisible();

    // Should show navigation buttons
    await expect(page.getByRole('button', { name: /previous|prev/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /next/i })).toBeVisible();

    // Should show challenge title (first challenge is "SELECT All Columns")
    await expect(page.getByText(/select all columns/i)).toBeVisible();

    // Should show query editor (textarea or code editor)
    const queryEditor = page.locator('textarea, [role="textbox"]').first();
    await expect(queryEditor).toBeVisible();

    // Should show submit button
    await expect(page.getByRole('button', { name: /submit query/i })).toBeVisible();
  });

  test('should complete full challenge journey: view → solve → submit → success', async ({
    authenticatedStudent,
  }) => {
    const page = authenticatedStudent;

    // Start at practice page
    await page.goto('/practice');
    await waitForLoadingToComplete(page);

    // Verify we're on Unit 1, Challenge 1
    await expect(page).toHaveURL(/unit=1.*challenge=1/);

    // Enter correct SQL query for first challenge
    const queryEditor = page.locator('textarea, [role="textbox"]').first();
    await queryEditor.fill('SELECT * FROM users');

    // Wait a moment for auto-save (debounced)
    await page.waitForTimeout(600);

    // Click submit button
    await page.click('button[type="submit"]:has-text("Submit")');

    // Wait for API call to complete
    await waitForAPICall(page, '/progress/submit', { method: 'POST', status: 200 });

    // Should show success message with points
    await expect(page.getByText(/congratulations|earned.*points/i)).toBeVisible({
      timeout: 5000,
    });

    // Should auto-navigate to next challenge after 2 seconds
    await page.waitForTimeout(2500);
    await expect(page).toHaveURL(/unit=1.*challenge=2/, { timeout: 5000 });
  });

  test('should handle incorrect query submission', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/practice?unit=1&challenge=1');
    await waitForLoadingToComplete(page);

    // Enter incorrect SQL query
    const queryEditor = page.locator('textarea, [role="textbox"]').first();
    await queryEditor.fill('SELECT name'); // Incorrect - should be SELECT * FROM users

    // Submit query
    await page.click('button[type="submit"]:has-text("Submit")');

    // Should show error message
    await expect(page.locator('text=/incorrect|wrong|error/i')).toBeVisible({ timeout: 5000 });

    // Should remain on same challenge
    await expect(page).toHaveURL(/unit=1.*challenge=1/);
  });

  test('should navigate between challenges using prev/next buttons', async ({
    authenticatedStudent,
  }) => {
    const page = authenticatedStudent;

    // Start at Unit 1, Challenge 2
    await page.goto('/practice?unit=1&challenge=2');
    await waitForLoadingToComplete(page);

    // Click Previous button
    await page.click('button:has-text("Previous"), button:has-text("Prev")');

    // Should navigate to Challenge 1
    await expect(page).toHaveURL(/unit=1.*challenge=1/, { timeout: 5000 });
    await expect(page.getByText(/challenge 1 of/i)).toBeVisible();

    // Click Next button
    await page.click('button:has-text("Next")');

    // Should navigate back to Challenge 2
    await expect(page).toHaveURL(/unit=1.*challenge=2/, { timeout: 5000 });
    await expect(page.getByText(/challenge 2 of/i)).toBeVisible();
  });

  test('should switch units using unit selector', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Start at Unit 1
    await page.goto('/practice?unit=1&challenge=2');
    await waitForLoadingToComplete(page);

    // Click Unit 2 button
    await page.click('button:has-text("Unit 2")');

    // Should navigate to Unit 2, Challenge 1
    await expect(page).toHaveURL(/unit=2.*challenge=1/, { timeout: 5000 });
    await waitForLoadingToComplete(page);

    // Click Unit 3 button
    await page.click('button:has-text("Unit 3")');

    // Should navigate to Unit 3, Challenge 1
    await expect(page).toHaveURL(/unit=3.*challenge=1/, { timeout: 5000 });
  });

  test('should save query draft to localStorage', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/practice?unit=1&challenge=1');
    await waitForLoadingToComplete(page);

    // Enter a query
    const queryEditor = page.locator('textarea, [role="textbox"]').first();
    const testQuery = 'SELECT * FROM test_table';
    await queryEditor.fill(testQuery);

    // Wait for debounced auto-save
    await page.waitForTimeout(600);

    // Verify draft saved to localStorage
    const draftKey = 'practice_query_draft_1_1';
    const savedDraft = await getLocalStorageItem(page, draftKey);
    expect(savedDraft).toBe(testQuery);
  });

  test('should disable previous button on first challenge', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to first challenge
    await page.goto('/practice?unit=1&challenge=1');
    await waitForLoadingToComplete(page);

    // Previous button should be disabled
    const prevButton = page.getByRole('button', { name: /previous|prev/i });
    await expect(prevButton).toBeDisabled();
  });

  test('should disable next button on last challenge', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to last challenge (Unit 3, Challenge 2)
    await page.goto('/practice?unit=3&challenge=2');
    await waitForLoadingToComplete(page);

    // Next button should be disabled
    const nextButton = page.getByRole('button', { name: /next/i });
    await expect(nextButton).toBeDisabled();
  });
});

test.describe('Progress Tracking', () => {
  test('should display progress page with summary statistics', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to progress page
    await page.goto('/progress');
    await waitForLoadingToComplete(page);

    // Should show page title
    await expect(page.getByRole('heading', { name: /your progress/i })).toBeVisible();

    // Should show stats cards
    await expect(page.getByText(/total points/i)).toBeVisible();
    await expect(page.getByText(/challenges completed/i)).toBeVisible();
    await expect(page.getByText(/completion rate/i)).toBeVisible();

    // Should show progress bar
    await expect(page.locator('text=/overall progress/i')).toBeVisible();

    // Should show list of challenges
    await expect(page.getByText(/select all columns/i)).toBeVisible();
  });

  test('should navigate to challenge when clicking on progress item', async ({
    authenticatedStudent,
  }) => {
    const page = authenticatedStudent;

    await page.goto('/progress');
    await waitForLoadingToComplete(page);

    // Find and click on a challenge in the list
    // Look for challenge cards or list items
    const challengeItem = page.locator('text=/select all columns/i').first();
    await challengeItem.click();

    // Should navigate to practice page with that challenge
    await expect(page).toHaveURL(/\/practice/, { timeout: 5000 });
  });

  test('should filter progress by unit', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/progress');
    await waitForLoadingToComplete(page);

    // Check if unit filter exists
    const unit1Button = page.getByRole('button', { name: /^unit 1$/i });
    if (await unit1Button.count() > 0) {
      // Click Unit 1 filter
      await unit1Button.click();

      // URL should update with filter
      // Content should show only Unit 1 challenges
      await expect(page.locator('text=/unit 1/i')).toBeVisible();
    }
  });
});

test.describe('Leaderboard', () => {
  test('should display leaderboard with rankings', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to leaderboard
    await page.goto('/leaderboard');
    await waitForLoadingToComplete(page);

    // Should show page title
    await expect(page.getByRole('heading', { name: /leaderboard/i })).toBeVisible();

    // Should show refresh button
    await expect(page.getByRole('button', { name: /refresh/i })).toBeVisible();

    // Should show auto-refresh toggle
    await expect(page.getByText(/auto-refresh/i)).toBeVisible();

    // Should show leaderboard table
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // Table should have columns
    await expect(page.getByRole('columnheader', { name: /rank/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /student|name/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /points/i })).toBeVisible();
  });

  test('should manually refresh leaderboard', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/leaderboard');
    await waitForLoadingToComplete(page);

    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await refreshButton.click();

    // Should show loading state briefly
    await expect(refreshButton).toHaveText(/refreshing/i, { timeout: 1000 }).catch(() => {});

    // Wait for API call
    await waitForAPICall(page, '/leaderboard', { timeout: 5000 });

    // Should show updated timestamp
    await expect(page.getByText(/just now|seconds ago/i)).toBeVisible({ timeout: 5000 });
  });

  test('should toggle auto-refresh', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/leaderboard');
    await waitForLoadingToComplete(page);

    // Find auto-refresh toggle
    const autoRefreshToggle = page.locator('button:has-text("Auto-refresh")');
    await expect(autoRefreshToggle).toBeVisible();

    // Get initial state
    const initialText = await autoRefreshToggle.textContent();
    const isOn = initialText?.includes('ON');

    // Click toggle
    await autoRefreshToggle.click();

    // State should change
    await expect(autoRefreshToggle).toHaveText(isOn ? /OFF/i : /ON/i);
  });

  test('should highlight current user in leaderboard', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/leaderboard');
    await waitForLoadingToComplete(page);

    // Should find current user's row (typically highlighted)
    const userRow = page.locator(`tr:has-text("${TEST_USERS.student.name}")`);

    // User row should exist in table
    await expect(userRow).toBeVisible();
  });
});

test.describe('Navigation and Routing', () => {
  test('should navigate between main pages using navigation menu', async ({
    authenticatedStudent,
  }) => {
    const page = authenticatedStudent;

    // Start at practice page
    await page.goto('/practice');
    await waitForLoadingToComplete(page);

    // Navigate to Progress
    await page.click('a[href="/progress"], nav a:has-text("Progress")');
    await expect(page).toHaveURL(/\/progress/, { timeout: 5000 });

    // Navigate to Leaderboard
    await page.click('a[href="/leaderboard"], nav a:has-text("Leaderboard")');
    await expect(page).toHaveURL(/\/leaderboard/, { timeout: 5000 });

    // Navigate back to Practice
    await page.click('a[href="/practice"], nav a:has-text("Practice")');
    await expect(page).toHaveURL(/\/practice/, { timeout: 5000 });
  });

  test('should persist authentication across page refreshes', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Navigate to practice page
    await page.goto('/practice');

    // Verify authenticated
    const tokenBefore = await getLocalStorageItem(page, 'access_token');
    expect(tokenBefore).not.toBeNull();

    // Reload page
    await page.reload();
    await waitForLoadingToComplete(page);

    // Should still be authenticated
    const tokenAfter = await getLocalStorageItem(page, 'access_token');
    expect(tokenAfter).not.toBeNull();

    // Should not redirect to login
    await expect(page).toHaveURL(/\/practice/);
  });

  test('should logout successfully', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    await page.goto('/practice');

    // Find and click logout button (might be in profile menu or nav)
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');

    if (await logoutButton.count() > 0) {
      await logoutButton.click();

      // Should clear token
      await page.waitForTimeout(500);
      const token = await getLocalStorageItem(page, 'access_token');
      expect(token).toBeNull();

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
    }
  });
});
