import React from 'react';
import { initialize, mswDecorator } from 'msw-storybook-addon';

// Initialize MSW (optional, for mocking API)
initialize();

export const decorators = [
  mswDecorator, // To mock API responses per-story if needed
  (Story: React.ComponentType) => <div style={{ padding: 16, fontFamily: 'Inter, system-ui' }}><Story/></div>,
];

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: { expanded: true },
  a11y: { element: '#root' },
};
