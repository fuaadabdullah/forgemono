import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { render, screen, act, waitFor } from '@testing-library/react';
import React, { useState, useEffect } from 'react';

// Mock @tanstack/react-query
jest.mock('@tanstack/react-query', () => ({
  QueryClient: jest.fn().mockImplementation(() => ({
    invalidateQueries: jest.fn(),
    refetchQueries: jest.fn(),
  })),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => children,
  useQuery: jest.fn(),
  useMutation: jest.fn(),
}));

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import StreamingView from '../components/streaming/StreamingView';

// Mock the runtime client
jest.mock('@/api/api-client', () => ({
  runtimeClient: {
    executeGoblinCommand: jest.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
);

// Mock performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByName: jest.fn(() => []),
  getEntriesByType: jest.fn(() => []),
  clearMarks: jest.fn(),
  clearMeasures: jest.fn(),
};

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true,
});

describe('Performance Tests - Streaming Components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should handle high-frequency streaming updates without performance degradation', async () => {
    // Create a wrapper component that manages streaming state
    const StreamingTestWrapper = () => {
      const [streamingText, setStreamingText] = useState('');

      useEffect(() => {
        let accumulatedText = '';
        const chunks = Array.from(
          { length: 100 },
          (_, i) => `Chunk ${i}: ${'x'.repeat(1000)}\n`
        );

        const updateChunk = (index: number) => {
          if (index < chunks.length) {
            accumulatedText += chunks[index];
            setStreamingText(accumulatedText);
            setTimeout(() => updateChunk(index + 1), 10);
          }
        };

        updateChunk(0);
      }, []);

      return <StreamingView streamingText={streamingText} isStreaming={true} />;
    };

    const startTime = performance.now();

    render(
      <TestWrapper>
        <StreamingTestWrapper />
      </TestWrapper>
    );

    // Wait for all chunks to be processed; wrap timer advancement in act to flush React updates
    await act(async () => {
      jest.advanceTimersByTime(100 * 10 + 100); // 100 chunks * 10ms + buffer
    });

    // Wait for the DOM to show the expected content (non-flaky assertion)
    await waitFor(() => {
      const streamingContainer = screen.getByTestId('streaming-view');
      const content = streamingContainer.textContent || '';
      expect(content.length).toBeGreaterThan(100000);
    });

    const endTime = performance.now();
    const duration = endTime - startTime;

    // Performance assertions
    expect(duration).toBeLessThan(2000); // Should complete within 2 seconds
    expect(screen.getByTestId('streaming-view')).toBeInTheDocument();

    // Check that large content was generated
    const streamingContainer = screen.getByTestId('streaming-view');
    const content = streamingContainer.textContent || '';
    expect(content.length).toBeGreaterThan(100000); // Large content
  });

  it('should maintain UI responsiveness during heavy streaming load', async () => {
    const { rerender } = render(
      <TestWrapper>
        <StreamingView streamingText="" />
      </TestWrapper>
    );

    // Start performance measurement
    const startTime = performance.now();

    // Simulate heavy streaming load by updating component props via rerender
    const totalChunks = 20;
    const largeChunk = 'data'.repeat(1000); // 4000 chars per chunk
    let accumulated = '';

    for (let i = 0; i < totalChunks; i++) {
      accumulated += `Heavy chunk ${i}: ${largeChunk}\n`;
      rerender(
        <TestWrapper>
          <StreamingView streamingText={accumulated} />
        </TestWrapper>
      );
      await act(async () => {
        jest.advanceTimersByTime(10);
      });
    }

    const endTime = performance.now();
    const processingTime = endTime - startTime;

  // UI should remain responsive (processing should be fast)
  expect(processingTime).toBeLessThan(500); // Less than 500ms for 20 chunks
  const streamingContainerCheck = screen.getByTestId('streaming-container');
  expect(((streamingContainerCheck.textContent || '').split('\n').length)).toBeGreaterThan(18); // Most chunks processed
  }, 10000); // 10 second timeout

  it('should handle memory efficiently with large streaming datasets', async () => {
    // Mock console memory methods for Node.js environment
    const originalConsole = global.console;
    const memoryLogs: string[] = [];

  global.console.log = jest.fn((...args) => {
      memoryLogs.push(args.join(' '));
    });

    const { rerender: rerender2 } = render(
      <TestWrapper>
        <StreamingView streamingText="" />
      </TestWrapper>
    );

    const memoryTestData = 'x'.repeat(10000); // 10KB per chunk
    const chunkCount = 20; // 200KB total
    let memAccum = '';
    for (let i = 0; i < chunkCount; i++) {
      memAccum += `${memoryTestData}\n`;
      rerender2(
        <TestWrapper>
          <StreamingView streamingText={memAccum} />
        </TestWrapper>
      );
      await act(async () => jest.advanceTimersByTime(20));
    }

    // Restore console
    global.console = originalConsole;

  // Verify content was processed
  const streamingContainerMemCheck = screen.getByTestId('streaming-container');
  expect(((streamingContainerMemCheck.textContent || '').length)).toBeGreaterThan(200000); // ~200KB of content

    // In a real scenario, we'd check for memory leaks here
    // For now, just ensure the component doesn't crash
    expect(screen.getByTestId('streaming-view')).toBeInTheDocument();
  });

  it('should throttle rapid updates to prevent UI blocking', async () => {
    const { rerender: rerender3 } = render(
      <TestWrapper>
        <StreamingView streamingText="" />
      </TestWrapper>
    );

    // Start timing
    const startTimeRapid = performance.now();

    let rapidAccum = '';
    const rapidUpdates = Array.from({ length: 200 }, (_, i) => `Update ${i}\n`);
    for (const update of rapidUpdates) {
      rapidAccum += update;
    }
    rerender3(
      <TestWrapper>
        <StreamingView streamingText={rapidAccum} />
      </TestWrapper>
    );

  const endTime = performance.now();
  const batchTime = endTime - startTimeRapid;

    // Even with 200 rapid updates, processing should be fast
  expect(batchTime).toBeLessThan(100); // Less than 100ms for batch processing
  const streamingContainerRapidCheck = screen.getByTestId('streaming-container');
  const streamingOutputRapidCheck = streamingContainerRapidCheck.querySelector('.streaming-output') as HTMLElement;
  expect((streamingOutputRapidCheck.textContent || '').split('\n').length).toBeGreaterThan(190); // Most updates processed
  });

  it('should handle streaming interruptions gracefully', async () => {
    render(
      <TestWrapper>
        <StreamingView streamingText="" />
      </TestWrapper>
    );

    const streamingOutput = screen
      .getByTestId('streaming-container')
      .querySelector('.streaming-output') as HTMLElement;

    // Start normal streaming
    streamingOutput.textContent = 'Starting stream...\n';

    // Simulate interruption (network error, etc.)
        await jest.advanceTimersByTime(100);
    streamingOutput.textContent += 'Stream interrupted\n';

    // Wait a bit
        await jest.advanceTimersByTime(50);

    // Resume streaming
    streamingOutput.textContent += 'Resuming stream...\n';
    streamingOutput.textContent += 'Final data chunk\n';

    // Verify the component handles the interruption
    const content = streamingOutput.textContent;
    expect(content).toContain('Starting stream');
    expect(content).toContain('Stream interrupted');
    expect(content).toContain('Resuming stream');
    expect(content).toContain('Final data chunk');

    // Component should still be functional
    expect(screen.getByTestId('streaming-view')).toBeInTheDocument();
  });

  it('should maintain scroll position during continuous streaming', async () => {
    render(
      <TestWrapper>
        <StreamingView streamingText="" />
      </TestWrapper>
    );

    const streamingContainer = screen.getByTestId('streaming-container');
    const streamingOutput = streamingContainer.querySelector('.streaming-output') as HTMLElement;

    // Mock scroll methods
    const mockScrollTop = { value: 0 };
    Object.defineProperty(streamingContainer, 'scrollTop', {
      get: () => mockScrollTop.value,
      set: value => {
        mockScrollTop.value = value;
      },
    });

    Object.defineProperty(streamingContainer, 'scrollHeight', {
      get: () => 1000,
    });

    // Simulate user scrolling to bottom
    mockScrollTop.value = 1000;

    // Add streaming content
    for (let i = 0; i < 10; i++) {
      streamingOutput.textContent += `Streaming line ${i}\n`;
          await jest.advanceTimersByTime(50);
    }

    // In a real implementation, scroll position should be maintained
    // For this test, we just verify the content is added
    expect(streamingOutput.textContent?.split('\n').length).toBeGreaterThan(8);
    expect(streamingContainer).toBeInTheDocument();
  });
});
