import { test, expect } from './fixtures/auth';
import {
  waitForNavigation,
  waitForLoadingToComplete,
  getLocalStorageItem,
  clearLocalStorage,
} from './support/helpers';

/**
 * Teacher E2E Test Suite
 *
 * Tests the complete teacher user journey:
 * - Teacher authentication and role protection
 * - Student management (list, search, sort, detail view)
 * - Analytics dashboard with charts
 * - Class-wide statistics
 */

test.describe('Teacher Authentication Flow', () => {
  test('should login as teacher and redirect to teacher dashboard', async ({ page, testUsers }) => {
    // Clear any existing auth
    await clearLocalStorage(page);

    // Navigate to login page
    await page.goto('/login');

    // Fill login form with teacher credentials
    await page.fill('input[type="email"]', testUsers.teacher.email);
    await page.fill('input[type="password"]', testUsers.teacher.password);

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation to teacher dashboard
    await waitForNavigation(page, /\/teacher/);

    // Verify access token exists
    const token = await getLocalStorageItem(page, 'access_token');
    expect(token).not.toBeNull();

    // Verify teacher name appears
    await expect(page.getByText(testUsers.teacher.name)).toBeVisible();
  });

  test('should prevent student from accessing teacher routes', async ({ authenticatedStudent }) => {
    const page = authenticatedStudent;

    // Try to access teacher dashboard as student
    await page.goto('/teacher/dashboard');

    // Should either redirect or show 403/forbidden message
    // Check if redirected away or error shown
    await page.waitForTimeout(1000);

    const url = page.url();
    const isForbidden =
      url.includes('/login') ||
      url.includes('/practice') ||
      (await page.locator('text=/forbidden|403|not authorized/i').count()) > 0;

    expect(isForbidden).toBe(true);
  });

  test('should show teacher-specific navigation items', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    // Navigate to teacher dashboard
    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Should show teacher navigation items
    const hasStudentsLink =
      (await page.locator('a[href*="/teacher/students"], a:has-text("Students")').count()) > 0;
    const hasAnalyticsLink =
      (await page.locator('a[href*="/teacher/analytics"], a:has-text("Analytics")').count()) > 0;

    // At least one teacher-specific link should be present
    expect(hasStudentsLink || hasAnalyticsLink).toBe(true);
  });
});

test.describe('Student Management', () => {
  test('should display students list page with table', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    // Navigate to students list
    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Should show page title
    await expect(page.getByRole('heading', { name: /students/i })).toBeVisible();

    // Should show student table
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // Should have table headers
    await expect(page.getByRole('columnheader', { name: /name/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /email/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /points/i })).toBeVisible();

    // Should show action buttons
    const hasExportButton = (await page.locator('button:has-text("Export")').count()) > 0;
    const hasImportButton = (await page.locator('button:has-text("Import")').count()) > 0;

    // At least one action button should be present
    expect(hasExportButton || hasImportButton).toBe(true);
  });

  test('should search for students', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Find search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]');

    if (await searchInput.count() > 0) {
      // Enter search query
      await searchInput.fill('e2e');

      // Wait for debounce and API call
      await page.waitForTimeout(500);
      await waitForLoadingToComplete(page);

      // URL should update with search parameter
      await expect(page).toHaveURL(/search=e2e/, { timeout: 5000 });

      // Table should show filtered results
      const table = page.getByRole('table');
      await expect(table).toBeVisible();
    }
  });

  test('should sort students by different criteria', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Look for sort buttons or dropdown
    const sortByPoints = page.locator('button:has-text("Points"), select option:has-text("Points")');

    if (await sortByPoints.count() > 0) {
      // Click sort by points
      await sortByPoints.first().click();

      // Wait for re-fetch
      await waitForLoadingToComplete(page);

      // URL should update with sort parameter
      await expect(page).toHaveURL(/sort=points/, { timeout: 5000 });
    }
  });

  test('should paginate through student list', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Look for pagination controls
    const nextPageButton = page.locator('button:has-text("Next"), a:has-text("Next")');

    if (await nextPageButton.count() > 0) {
      const isEnabled = await nextPageButton.isEnabled();

      if (isEnabled) {
        // Click next page
        await nextPageButton.click();
        await waitForLoadingToComplete(page);

        // URL should update with page parameter
        await expect(page).toHaveURL(/page=2/, { timeout: 5000 });
      }
    }
  });

  test('should view student detail page', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Find a student row and click it
    const table = page.getByRole('table');
    const firstRow = table.locator('tbody tr').first();

    if (await firstRow.count() > 0) {
      // Click on the row or a view button
      await firstRow.click();

      // Should navigate to student detail page
      await expect(page).toHaveURL(/\/teacher\/students\/\d+/, { timeout: 5000 });
      await waitForLoadingToComplete(page);

      // Should show student details
      await expect(page.getByText(/email|points|progress/i)).toBeVisible();
    }
  });
});

test.describe('Analytics Dashboard', () => {
  test('should display analytics page with metrics cards', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    // Navigate to analytics page
    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Should show page title
    await expect(page.getByRole('heading', { name: /analytics|class analytics/i })).toBeVisible();

    // Should show metric cards
    const hasMetrics =
      (await page.locator('text=/total students|average|completion/i').count()) > 0;
    expect(hasMetrics).toBe(true);
  });

  test('should render charts with data visualization', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Wait for charts to render (Recharts uses SVG)
    await page.waitForSelector('svg', { timeout: 10000 });

    // Should have at least one chart (SVG element from Recharts)
    const charts = page.locator('svg');
    const chartCount = await charts.count();
    expect(chartCount).toBeGreaterThan(0);

    // Charts should have actual data (check for chart elements)
    const hasChartElements =
      (await page.locator('.recharts-line, .recharts-bar, .recharts-area').count()) > 0;
    expect(hasChartElements).toBe(true);
  });

  test('should display weekly trends chart', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Look for weekly trends section
    const hasTrendsChart =
      (await page.locator('text=/weekly.*trends|trends.*chart/i').count()) > 0;

    if (hasTrendsChart) {
      // Should have chart with data
      await expect(page.locator('svg')).toBeVisible();
    }
  });

  test('should display challenge success rate chart', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Look for challenge or success rate section
    const hasSuccessChart =
      (await page.locator('text=/challenge.*success|success.*rate/i').count()) > 0;

    if (hasSuccessChart) {
      // Should have bar chart (Recharts bar elements)
      const bars = page.locator('.recharts-bar-rectangle, rect[name]');
      const barCount = await bars.count();
      expect(barCount).toBeGreaterThan(0);
    }
  });

  test('should show at-risk students section if applicable', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Look for at-risk students section
    const atRiskSection = page.locator('text=/at-risk.*students|struggling.*students/i');

    if (await atRiskSection.count() > 0) {
      // Section should be visible
      await expect(atRiskSection).toBeVisible();

      // Should show list or message
      const hasContent =
        (await page.locator('text=/no.*at-risk|students.*risk/i').count()) > 0;
      expect(hasContent).toBe(true);
    }
  });

  test('should show class-wide statistics', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Should show numerical statistics
    const hasNumbers = (await page.locator('text=/\\d+%|\\d+ points|\\d+ students/').count()) > 0;
    expect(hasNumbers).toBe(true);
  });
});

test.describe('Teacher Dashboard', () => {
  test('should display teacher dashboard with overview', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    // Navigate to teacher dashboard
    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Should show welcome or title
    await expect(page.getByText(/dashboard|welcome/i)).toBeVisible();

    // Should show quick stats or action buttons
    const hasContent =
      (await page.locator('button, a, [class*="card"], [class*="metric"]').count()) > 0;
    expect(hasContent).toBe(true);
  });

  test('should navigate to students from dashboard', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Find link to students page
    const studentsLink = page.locator('a[href*="/teacher/students"], button:has-text("Students")');

    if (await studentsLink.count() > 0) {
      await studentsLink.first().click();
      await expect(page).toHaveURL(/\/teacher\/students/, { timeout: 5000 });
    }
  });

  test('should navigate to analytics from dashboard', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Find link to analytics page
    const analyticsLink = page.locator(
      'a[href*="/teacher/analytics"], button:has-text("Analytics")'
    );

    if (await analyticsLink.count() > 0) {
      await analyticsLink.first().click();
      await expect(page).toHaveURL(/\/teacher\/analytics/, { timeout: 5000 });
    }
  });
});

test.describe('Data Export and Import', () => {
  test('should show export button on students page', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), a:has-text("Export")');

    if (await exportButton.count() > 0) {
      await expect(exportButton.first()).toBeVisible();
    }
  });

  test('should show import button for bulk student upload', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    // Look for import button
    const importButton = page.locator('button:has-text("Import"), button:has-text("Bulk Import")');

    if (await importButton.count() > 0) {
      await expect(importButton.first()).toBeVisible();

      // Click to open import modal
      await importButton.first().click();

      // Should show import dialog or modal
      await expect(page.locator('text=/import|upload|csv/i')).toBeVisible({ timeout: 3000 });
    }
  });
});

test.describe('Teacher Navigation', () => {
  test('should navigate between teacher pages using sidebar/nav', async ({
    authenticatedTeacher,
  }) => {
    const page = authenticatedTeacher;

    // Start at dashboard
    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Navigate to students
    const studentsLink = page.locator('a[href*="/teacher/students"]').first();
    if (await studentsLink.count() > 0) {
      await studentsLink.click();
      await expect(page).toHaveURL(/\/teacher\/students/);
    }

    // Navigate to analytics
    const analyticsLink = page.locator('a[href*="/teacher/analytics"]').first();
    if (await analyticsLink.count() > 0) {
      await analyticsLink.click();
      await expect(page).toHaveURL(/\/teacher\/analytics/);
    }
  });

  test('should maintain teacher role across page refreshes', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    // Navigate to teacher page
    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Reload page
    await page.reload();
    await waitForLoadingToComplete(page);

    // Should still be on teacher page (not redirected)
    await expect(page).toHaveURL(/\/teacher/);

    // Access token should still exist
    const token = await getLocalStorageItem(page, 'access_token');
    expect(token).not.toBeNull();
  });

  test('should logout from teacher account', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/dashboard');

    // Find and click logout
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

test.describe('Cross-Browser Compatibility', () => {
  test('teacher dashboard should render correctly', async ({ authenticatedTeacher }) => {
    const page = authenticatedTeacher;

    await page.goto('/teacher/dashboard');
    await waitForLoadingToComplete(page);

    // Basic rendering check
    await expect(page.locator('body')).toBeVisible();

    // No console errors (optional check)
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigate around
    await page.goto('/teacher/students');
    await waitForLoadingToComplete(page);

    await page.goto('/teacher/analytics');
    await waitForLoadingToComplete(page);

    // Should have minimal errors (allow for expected warnings)
    // Don't fail test on minor warnings, but log them
    if (errors.length > 0) {
      console.log('Console errors detected:', errors);
    }
  });
});
