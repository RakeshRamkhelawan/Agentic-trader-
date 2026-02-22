# E2E Testing with Playwright

This directory contains end-to-end tests using [Playwright](https://playwright.dev/).

## Setup

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Create .env.test for test-specific env vars
cp .env.example .env.test
```

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test auth.spec.ts

# Run tests in specific browser
npx playwright test --project=chromium
```

## Test Structure

```
e2e/
├── auth.spec.ts        # Authentication flows
├── dashboard.spec.ts   # Dashboard functionality
├── trading.spec.ts     # Trading flows
└── README.md           # This file
```

## Critical Flows Covered

1. **Authentication (auth.spec.ts)**
   - Login page accessibility
   - Auth0 integration
   - Protected routes
   - Logout

2. **Dashboard (dashboard.spec.ts)**
   - Page load
   - Navigation
   - Market data display
   - Responsive design

3. **Trading (trading.spec.ts)**
   - Terminal load
   - Orderbook display
   - Order form validation
   - Active orders

## Authentication Testing

For E2E tests requiring authentication, you have two options:

### Option 1: Mock Authentication (Recommended for CI)

```typescript
// In test setup
await page.addInitScript(() => {
  window.localStorage.setItem('auth_mock', JSON.stringify({
    isAuthenticated: true,
    user: { id: 'test-user', email: 'test@example.com' }
  }));
});
```

### Option 2: Test Credentials

```bash
# Set test credentials in environment
TEST_USERNAME=test@example.com
TEST_PASSWORD=testpassword
```

## Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Mock external APIs** when possible for faster, more reliable tests
3. **Clean up state** after each test
4. **Use page objects** for complex page interactions

## CI/CD Integration

Tests run automatically on:
- Pull request creation
- Merge to main
- Manual trigger

See `.github/workflows/ci.yml` for configuration.
