import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, afterEach } from '@jest/globals';

// mock the api client module used by the hook
jest.mock('../../api/client-axios', () => ({
  apiClient: {
    getGoblins: jest.fn(),
    startStreamingTask: jest.fn(),
    pollStreamingTask: jest.fn(),
    cancelStreamingTask: jest.fn(),
  },
}));

import { apiClient } from '../../api/client-axios';
import { useTaskExecution } from '../useTaskExecution';

describe('useTaskExecution', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    (apiClient.getGoblins as any).mockResolvedValue([
      { id: 'g1', title: 'Goblin 1', guild: 'Test' },
    ]);
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.resetAllMocks();
    jest.useRealTimers();
  });

  test('loads goblins on mount and sets selected goblin', async () => {
    const { result } = renderHook(() => useTaskExecution());

    await waitFor(() => {
      expect(result.current.goblins.length).toBe(1);
      expect(result.current.selectedGoblin).toBe('g1');
    });
  });

  test('starts stream and polls for updates', async () => {
    // Arrange: mock the streaming calls
    (apiClient.startStreamingTask as any).mockResolvedValue({ stream_id: 's1' });
    // first poll returns a chunk but not done; second poll returns a final chunk
    (apiClient.pollStreamingTask as any)
      .mockResolvedValueOnce({ chunks: [{ content: 'hello', token_count: 2 }], done: false })
      .mockResolvedValueOnce({
        chunks: [{ content: ' world', token_count: 2, done: true }],
        done: true,
      });

    const { result } = renderHook(() => useTaskExecution());

    // set inputs and start
    act(() => {
      result.current.setSelectedGoblin('g1');
      result.current.setTask('Perform something');
    });

    await act(async () => {
      await result.current.startStreamingTask();
      // Advance timers to trigger polling loop
      jest.advanceTimersByTime(1000);
      // Allow promises to resolve
      await Promise.resolve();
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    await waitFor(() => expect(result.current.streamOutput.length).toBeGreaterThanOrEqual(2));
    expect(result.current.streamOutput[0].content).toContain('hello');
    expect(result.current.streamOutput[1].content).toContain(' world');
    // After done, isStreaming should be false and streamId reset
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.streamOutput.some((c) => c.done)).toBeTruthy();
  });
});
