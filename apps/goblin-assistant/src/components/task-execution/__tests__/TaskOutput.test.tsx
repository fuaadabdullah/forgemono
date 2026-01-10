import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, test, expect } from '@jest/globals';

import { TaskOutput } from '../TaskOutput';

describe('TaskOutput', () => {
  test('renders chunk contents and summary when done', () => {
    const output = [
      { content: 'First part', token_count: 5 },
      { content: ' and final part', done: true, tokens: 8, cost: 0.00123 },
    ];

    render(<TaskOutput streamOutput={output as any} isStreaming={false} />);

    expect(screen.getByText(/First part/i)).toBeTruthy();
    expect(screen.getByText(/and final part/i)).toBeTruthy();
    // assert that tokens and cost summary is shown
    expect(screen.getByText(/Tokens:/i)).toBeTruthy();
    expect(screen.getByText(/Cost:/i)).toBeTruthy();
    // cost should be rendered to 4 decimal places
    expect(screen.getByText(/\$0.0012/i)).toBeTruthy();
  });
});
