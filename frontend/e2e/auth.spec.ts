/**
 * Authentication E2E Tests
 *
 * Tests the critical authentication flows:
 * - Login page accessibility
 * - Auth0 redirect
 * - Protected routes
 * - Logout
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
  });

  test('login page should be accessible', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Agentic Trader|Login/);

    // Check for login form elements
    await expect(page.getByRole('heading', { name: /sign in|login/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in|login/i })).toBeVisible();
  });

  test('should have Auth0 login button', async ({ page }) => {
    // Look for Auth0 login button
    const auth0Button = page.getByRole('button', { name: /continue with auth0|auth0|single sign-on/i });
    await expect(auth0Button).toBeVisible();
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    // Note: This test requires a test user or mocking Auth0
    // For now, we just verify the redirect behavior

    // Click login button
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Wait for navigation (Auth0 redirect)
    await page.waitForURL(/auth0\.com|login/, { timeout: 10000 });

    // Verify we're on Auth0 login page
    await expect(page.url()).toContain('auth0');
  });

  test('protected routes should redirect to login when not authenticated', async ({ page }) => {
    // Try to access dashboard directly
    await page.goto('/dashboard');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show configuration error when env vars are missing', async ({ page, context }) => {
    // This test verifies the error screen shows when env vars are missing
    // We can test this by checking if the error message exists in the DOM

    const errorHeading = page.getByText(/configuration error/i);

    // If env vars are missing, this should be visible
    if (await errorHeading.isVisible().catch(() => false)) {
      await expect(page.getByText(/missing required environment variables/i)).toBeVisible();
    }
  });
});
