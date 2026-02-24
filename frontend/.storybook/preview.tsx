import type { Preview } from '@storybook/react';
import React from 'react';
import '../src/index.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        {
          name: 'dark',
          value: '#000000',
        },
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'card',
          value: '#111111',
        },
      ],
    },
    layout: 'padded',
  },
  decorators: [
    (Story) => (
      <div className="min-h-screen bg-black text-white p-4">
        <Story />
      </div>
    ),
  ],
};

export default preview;
