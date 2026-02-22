# Storybook

> Component documentation and development environment

## Setup

```bash
# Install Storybook dependencies
npm install --save-dev @storybook/react-vite @storybook/addon-essentials @storybook/addon-interactions @storybook/addon-a11y

# Run Storybook
npm run storybook
```

## Usage

```bash
# Start Storybook development server
npm run storybook

# Build static Storybook
npm run build-storybook
```

## Writing Stories

### Basic Story

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
};

export default meta;

export const Primary: StoryObj = {
  args: {
    children: 'Click me',
    variant: 'default',
  },
};
```

### With Decorators

```typescript
export const DarkMode: Story = {
  decorators: [
    (Story) => (
      <div className="dark bg-black p-4">
        <Story />
      </div>
    ),
  ],
};
```

## Best Practices

1. **One story per file** for complex components
2. **Use argTypes** for props documentation
3. **Add a11y tests** with @storybook/addon-a11y
4. **Use realistic data** in stories

## Available Stories

- UI Components: Button, Card, Input, etc.
- Dashboard: Charts, Metrics, Lists
- Trading: Order forms, Orderbook

## Deployment

Build and deploy to Chromatic, Netlify, or GitHub Pages:

```bash
npm run build-storybook
# Deploy storybook-static/ directory
```
