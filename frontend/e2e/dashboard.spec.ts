/**
 * Dashboard E2E Tests
 *
 * Tests the dashboard functionality:
 * - Page load
 * - Data display
 * - Navigation
 * - Real-time updates (WebSocket)
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  // Helper to authenticate before dashboard tests
  test.beforeEach(async ({ page }) => {
    // Navigate to login and authenticate (or mock authentication)
    await page.goto('/login');

    // TODO: Implement authentication helper or mock
    // For now, we'll assume the user is redirected to Auth0
    // In a real test, you'd mock the auth state or use test credentials
  });

  test('dashboard should load with all sections', async ({ page }) => {
    // Navigate to dashboard (assuming authenticated)
    await page.goto('/dashboard');

    // Check for main dashboard elements
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    // Check for portfolio section
    await expect(page.getByText(/portfolio|holdings/i).first()).toBeVisible();

    // Check for market data
    await expect(page.getByText(/markets|assets/i).first()).toBeVisible();

    // Check for agent status
    await expect(page.getByText(/agents|ai advisor/i).first()).toBeVisible();
  });

  test('sidebar navigation should work', async ({ page }) => {
    await page.goto('/dashboard');

    // Test navigation to Markets
    await page.getByRole('link', { name: /markets/i }).click();
    await expect(page).toHaveURL(/\/markets/);

    // Test navigation to Portfolio
    await page.getByRole('link', { name: /portfolio/i }).click();
    await expect(page).toHaveURL(/\/portfolio/);

    // Test navigation back to Dashboard
    await page.getByRole('link', { name: /dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display market data', async ({ page }) => {
    await page.goto('/markets');

    // Wait for market data to load
    await page.waitForTimeout(2000);

    // Check for asset symbols (BTC, ETH, etc.)
    const assetSymbols = page.getByText(/BTC|ETH|SOL|ADA/);
    await expect(assetSymbols.first()).toBeVisible();

    // Check for price displays
    const prices = page.getByText(/\$[\d,]+\.?\d*/);
    await expect(prices.first()).toBeVisible();
  });

  test('should show connection status indicator', async ({ page }) => {
    await page.goto('/dashboard');

    // Look for WebSocket connection indicator
    const connectionIndicator = page.getByText(/connected|live|●/i).first();
    await expect(connectionIndicator).toBeVisible();
  });

  test('responsive design - mobile sidebar', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Sidebar should be collapsed or hidden on mobile
    const sidebar = page.locator('aside, nav[role="navigation"]').first();

    // Check if sidebar is not visible or in mobile mode
    const isMobile = await sidebar.evaluate((el) => {
      return window.getComputedStyle(el).display === 'none' ||
             window.getComputedStyle(el).width === '72px';
    });

    expect(isMobile).toBeTruthy();
  });
});
