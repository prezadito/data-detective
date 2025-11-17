import { Page, expect } from '@playwright/test';

/**
 * E2E Test Helper Utilities
 *
 * Common helper functions for Playwright E2E tests
 */

/**
 * Wait for navigation to a specific URL pattern
 * @param page - Playwright page object
 * @param urlPattern - URL pattern to wait for (string or regex)
 * @param options - Additional wait options
 */
export async function waitForNavigation(
  page: Page,
  urlPattern: string | RegExp,
  options?: { timeout?: number }
): Promise<void> {
  await page.waitForURL(urlPattern, { timeout: options?.timeout ?? 10000 });
  await page.waitForLoadState('networkidle', { timeout: options?.timeout ?? 10000 });
}

/**
 * Wait for an API call to complete
 * @param page - Playwright page object
 * @param urlPattern - API URL pattern to wait for
 * @param options - Additional wait options
 */
export async function waitForAPICall(
  page: Page,
  urlPattern: string | RegExp,
  options?: { method?: string; status?: number; timeout?: number }
): Promise<void> {
  await page.waitForResponse(
    (response) => {
      const urlMatches =
        typeof urlPattern === 'string'
          ? response.url().includes(urlPattern)
          : urlPattern.test(response.url());

      const methodMatches = options?.method ? response.request().method() === options.method : true;
      const statusMatches = options?.status ? response.status() === options.status : true;

      return urlMatches && methodMatches && statusMatches;
    },
    { timeout: options?.timeout ?? 5000 }
  );
}

/**
 * Fill and submit a form
 * @param page - Playwright page object
 * @param formData - Object with field selectors as keys and values to fill
 * @param submitButtonSelector - Selector for the submit button
 */
export async function fillAndSubmitForm(
  page: Page,
  formData: Record<string, string>,
  submitButtonSelector: string
): Promise<void> {
  // Fill all form fields
  for (const [selector, value] of Object.entries(formData)) {
    await page.fill(selector, value);
  }

  // Click submit button
  await page.click(submitButtonSelector);
}

/**
 * Clear localStorage (useful for cleaning up test data)
 * @param page - Playwright page object
 */
export async function clearLocalStorage(page: Page): Promise<void> {
  await page.evaluate(() => localStorage.clear());
}

/**
 * Get value from localStorage
 * @param page - Playwright page object
 * @param key - LocalStorage key
 * @returns Value from localStorage or null if not found
 */
export async function getLocalStorageItem(page: Page, key: string): Promise<string | null> {
  return await page.evaluate((k) => localStorage.getItem(k), key);
}

/**
 * Set value in localStorage
 * @param page - Playwright page object
 * @param key - LocalStorage key
 * @param value - Value to set
 */
export async function setLocalStorageItem(page: Page, key: string, value: string): Promise<void> {
  await page.evaluate(
    ({ k, v }) => localStorage.setItem(k, v),
    { k: key, v: value }
  );
}

/**
 * Take a screenshot with custom naming
 * @param page - Playwright page object
 * @param name - Screenshot name
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true,
  });
}

/**
 * Wait for element to be visible and enabled
 * @param page - Playwright page object
 * @param selector - Element selector
 * @param options - Additional wait options
 */
export async function waitForElement(
  page: Page,
  selector: string,
  options?: { timeout?: number; state?: 'visible' | 'hidden' | 'attached' | 'detached' }
): Promise<void> {
  await page.waitForSelector(selector, {
    state: options?.state ?? 'visible',
    timeout: options?.timeout ?? 5000,
  });
}

/**
 * Scroll to element
 * @param page - Playwright page object
 * @param selector - Element selector
 */
export async function scrollToElement(page: Page, selector: string): Promise<void> {
  await page.locator(selector).scrollIntoViewIfNeeded();
}

/**
 * Wait for text to be visible on page
 * @param page - Playwright page object
 * @param text - Text to wait for
 * @param options - Additional wait options
 */
export async function waitForText(
  page: Page,
  text: string | RegExp,
  options?: { timeout?: number }
): Promise<void> {
  await expect(page.getByText(text)).toBeVisible({ timeout: options?.timeout ?? 5000 });
}

/**
 * Wait for toast message to appear (Data Detective uses sonner)
 * @param page - Playwright page object
 * @param message - Expected toast message (string or regex)
 * @param options - Additional wait options
 */
export async function waitForToast(
  page: Page,
  message: string | RegExp,
  options?: { timeout?: number }
): Promise<void> {
  // Sonner toasts typically have role="status" or appear in a toast container
  const toast = page.locator('[role="status"]', { hasText: message });
  await expect(toast).toBeVisible({ timeout: options?.timeout ?? 5000 });
}

/**
 * Disable auto-refresh timers (useful for leaderboard tests)
 * @param page - Playwright page object
 */
export async function disableAutoRefresh(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Override setInterval to prevent auto-refresh
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).setInterval = () => 0;
  });
}

/**
 * Wait for loading spinner to disappear
 * @param page - Playwright page object
 * @param options - Additional wait options
 */
export async function waitForLoadingToComplete(
  page: Page,
  options?: { timeout?: number }
): Promise<void> {
  // Wait for any loading spinners to disappear
  const spinners = page.locator('.animate-spin, [aria-label*="loading" i]');
  const count = await spinners.count();

  if (count > 0) {
    await expect(spinners.first()).toBeHidden({ timeout: options?.timeout ?? 10000 });
  }
}

/**
 * Get table data from a table element
 * @param page - Playwright page object
 * @param tableSelector - Selector for the table
 * @returns Array of row data (each row is an array of cell text)
 */
export async function getTableData(page: Page, tableSelector: string): Promise<(string | undefined)[][]> {
  return await page.evaluate((selector) => {
    const table = document.querySelector(selector);
    if (!table) return [];

    const rows = Array.from(table.querySelectorAll('tbody tr'));
    return rows.map((row) => {
      const cells = Array.from(row.querySelectorAll('td'));
      return cells.map((cell) => cell.textContent?.trim());
    });
  }, tableSelector);
}
