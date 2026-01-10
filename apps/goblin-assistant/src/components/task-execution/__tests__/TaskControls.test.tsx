import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect } from '@jest/globals';

import { TaskControls } from '../TaskControls';

const makeProps = (overrides = {}) => ({
  goblins: [{ id: 'g1', title: 'Goblin 1', guild: 'Test' }],
  selectedGoblin: 'g1',
  setSelectedGoblin: jest.fn(),
  task: 'Test task',
  setTask: jest.fn(),
  isStreaming: false,
  loading: false,
  startStreamingTask: jest.fn(),
  cancelTask: jest.fn(),
  clearOutput: jest.fn(),
  ...overrides,
});

describe('TaskControls', () => {
  test('renders controls and triggers start/cancel/clear callbacks', () => {
    const props = makeProps();
    render(<TaskControls {...props} />);

    // Should show the goblin select and the execute button
    expect(screen.getByLabelText(/Select Goblin/i)).toBeTruthy();
    const executeBtn = screen.getByRole('button', { name: /Execute Task/i });
    expect(executeBtn.getAttribute('disabled')).toBeNull();

    fireEvent.click(executeBtn);
    expect(props.startStreamingTask).toHaveBeenCalled();

    // Clear output should call clearOutput
    const clearBtn = screen.getByRole('button', { name: /Clear Output/i });
    fireEvent.click(clearBtn);
    expect(props.clearOutput).toHaveBeenCalled();
  });

  test('shows cancel button when streaming', () => {
    const props = makeProps({ isStreaming: true });
    render(<TaskControls {...props} />);

    expect(screen.getByRole('button', { name: /Cancel Task/i })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Cancel Task/i }));
    expect(props.cancelTask).toHaveBeenCalled();
  });
});
