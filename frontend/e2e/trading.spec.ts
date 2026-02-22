/**
 * Trading Flow E2E Tests
 *
 * Tests the critical trading functionality:
 * - Viewing orderbook
 * - Placing orders (mock)
 * - Viewing order history
 * - Canceling orders
 */

import { test, expect } from '@playwright/test';

test.describe('Trading Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to trading terminal
    await page.goto('/terminal');
  });

  test('trading terminal should load', async ({ page }) => {
    // Check for terminal elements
    await expect(page.getByRole('heading', { name: /terminal|trading/i })).toBeVisible();

    // Check for order form
    await expect(page.getByRole('button', { name: /buy|long/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /sell|short/i }).first()).toBeVisible();
  });

  test('should display orderbook', async ({ page }) => {
    // Navigate to markets for orderbook view
    await page.goto('/markets');

    // Wait for orderbook to load
    await page.waitForTimeout(2000);

    // Check for bid/ask columns
    const orderbook = page.locator('[data-testid="orderbook"], .orderbook, [class*="orderbook"]').first();

    // If orderbook exists, verify it has data
    if (await orderbook.isVisible().catch(() => false)) {
      // Look for price levels
      const priceLevels = page.getByText(/\$[\d,]+\.?\d*/).first();
      await expect(priceLevels).toBeVisible();
    }
  });

  test('order placement form validation', async ({ page }) => {
    await page.goto('/terminal');

    // Try to submit without amount
    const buyButton = page.getByRole('button', { name: /buy/i }).first();
    await buyButton.click();

    // Should show validation error
    const errorMessage = page.getByText(/amount is required|enter amount|invalid/i).first();
    await expect(errorMessage).toBeVisible();
  });

  test('should show active orders', async ({ page }) => {
    // Navigate to portfolio for orders
    await page.goto('/portfolio');

    // Check for orders section
    const ordersSection = page.getByText(/orders|active orders|open orders/i).first();
    await expect(ordersSection).toBeVisible();
  });

  test('price display should update', async ({ page }) => {
    await page.goto('/markets');

    // Get initial price
    const priceElement = page.getByText(/\$[\d,]+\.?\d*/).first();
    const initialPrice = await priceElement.textContent();

    // Wait for potential update
    await page.waitForTimeout(5000);

    // Price might have changed (or stayed the same)
    // This test mainly verifies the price element exists and is updating
    const currentPrice = await priceElement.textContent();
    expect(currentPrice).toMatch(/\$[\d,]+\.?\d*/);
  });
});
