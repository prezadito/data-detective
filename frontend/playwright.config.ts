import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 *
 * This configuration sets up end-to-end testing for the Data Detective Academy frontend.
 * Tests run against a local development server with multiple browser configurations.
 *
 * Key Features:
 * - Multi-browser testing (Chromium, Firefox)
 * - Parallel test execution
 * - Automatic screenshot and video capture on failure
 * - Auto-start development server
 * - Trace collection for debugging
 */

export default defineConfig({
  // Test directory containing E2E tests
  testDir: './tests/e2e',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry failed tests (2 retries in CI, 0 locally for faster feedback)
  retries: process.env.CI ? 2 : 0,

  // Number of parallel workers (4 locally, 1 in CI for stability)
  workers: process.env.CI ? 1 : 4,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'], // Console output
    ['json', { outputFile: 'test-results/results.json' }],
  ],

  // Global test timeout (30 seconds)
  timeout: 30000,

  // Expect timeout for assertions (5 seconds)
  expect: {
    timeout: 5000,
  },

  // Shared settings for all projects
  use: {
    // Base URL for navigation (e.g., page.goto('/'))
    baseURL: 'http://localhost:3000',

    // Collect trace on failure for debugging
    trace: 'retain-on-failure',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video recording on failure
    video: 'retain-on-failure',

    // Navigation timeout
    navigationTimeout: 10000,

    // Action timeout (click, fill, etc.)
    actionTimeout: 5000,
  },

  // Browser projects for cross-browser testing
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Additional Chromium-specific settings
        viewport: { width: 1280, height: 720 },
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        // Additional Firefox-specific settings
        viewport: { width: 1280, height: 720 },
      },
    },

    // Uncomment to add Safari/WebKit testing
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // Mobile viewport testing (optional)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
  ],

  // Web server configuration - automatically starts frontend dev server
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // 2 minutes to start
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
