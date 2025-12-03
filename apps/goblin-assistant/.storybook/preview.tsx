import type { Preview } from '@storybook/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import '../src/index.css';
import { ContrastModeProvider } from '../src/hooks/useContrastMode';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        {
          name: 'dark',
          value: '#0a0a0a',
        },
        {
          name: 'light',
          value: '#ffffff',
        },
      ],
    },
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
        ],
      },
    },
  },
  decorators: [
    (Story) => (
      <ContrastModeProvider>
        <BrowserRouter>
          <div style={{ padding: '2rem', minHeight: '100vh' }}>
            <Story />
          </div>
        </BrowserRouter>
      </ContrastModeProvider>
    ),
  ],
  globalTypes: {
    theme: {
      description: 'Global theme for components',
      defaultValue: 'dark',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: ['dark', 'light'],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;
