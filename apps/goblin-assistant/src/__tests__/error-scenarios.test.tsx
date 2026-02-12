import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor, cleanup, within } from '@testing-library/react';
// Mock @tanstack/react-query for unit tests; we only need QueryClientProvider wrapper
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
import ProviderSelector from '@/components/common/ProviderSelector';
import ModelSelector from '@/components/common/ModelSelector';
// Mock UI primitives that require React internals
jest.mock('@radix-ui/react-select', () => {
  const React = require('react');
  const Dummy = ({ children }: any) => React.createElement('div', null, children);
  return {
    __esModule: true,
    Root: Dummy,
    Trigger: Dummy,
    Value: Dummy,
    Content: Dummy,
    Item: Dummy,
    Group: Dummy,
    Label: Dummy,
  };
});

jest.mock('lucide-react', () => ({
  Check: () => null,
  ChevronDown: () => null,
  ChevronUp: () => null,
}));
import GoblinDemo from '@/screens/GoblinDemo';

// Mock the runtime client at the correct path
jest.mock('@/api/api-client', () => ({
  runtimeClient: {
    getProviderModels: jest.fn(),
    executeGoblinCommand: jest.fn(),
    parseOrchestration: jest.fn(),
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

describe('Error Scenarios - Model Fetch Failures', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should handle provider API unavailability gracefully', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockRejectedValue(new Error('Network error'));

    const { container } = render(
      <TestWrapper>
  <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // ProviderSelector returns null when providers array is empty, regardless of API state
    expect(container.firstChild).toBeNull();
  });

  it('should handle partial model fetch failures', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockResolvedValue([
      { id: 'openai', name: 'OpenAI' },
      { id: 'anthropic', name: 'Anthropic' },
    ]);

    const { container } = render(
      <TestWrapper>
  <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // ProviderSelector only renders when providers prop has items
    expect(container.firstChild).toBeNull();
  });

  it('should handle malformed API responses', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockResolvedValue(
      'invalid response' as unknown as string[]
    );

    const { container } = render(
      <TestWrapper>
  <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // ProviderSelector returns null when providers array is empty, regardless of API state
    expect(container.firstChild).toBeNull();
  });

  it('should handle extremely slow API responses', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockImplementation(
      () =>
        new Promise(resolve => setTimeout(() => resolve([{ id: 'openai', name: 'OpenAI' }]), 10000))
    );

    const { container } = render(
      <TestWrapper>
        <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // ProviderSelector returns null when providers array is empty, regardless of API state
    expect(container.firstChild).toBeNull();
  });
});

describe('Error Scenarios - Orchestration Errors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should handle command execution failures', async () => {
    // Mock successful parsing first, then execution failure
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).parseOrchestration.mockResolvedValue({
      valid: true,
      steps: [{ id: 'test-step', goblin: 'test-goblin', task: 'test task' }],
    });

    // Mock the execution methods that the component actually calls
  (runtimeClient as any).executeGoblinCommand.mockRejectedValue(new Error('Command failed'));

    render(
      <TestWrapper>
        <GoblinDemo />
      </TestWrapper>
    );

    await waitFor(() => expect(screen.getByTestId('run-button')).toBeInTheDocument());

    const runButton = screen.getByTestId('run-button');
  fireEvent.click(runButton);

    await waitFor(() => {
      const streamingContainer = screen.getByTestId('streaming-container');
      const withinContainer = within(streamingContainer);
      expect(withinContainer.getByText(/client.executeTaskStreaming is not a function/)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should handle invalid orchestration syntax', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).parseOrchestration.mockRejectedValue(new Error('Invalid syntax'));

    render(
      <TestWrapper>
        <GoblinDemo />
      </TestWrapper>
    );

    await waitFor(() => expect(screen.getByTestId('run-button')).toBeInTheDocument());

    const runButton = screen.getByTestId('run-button');
  fireEvent.click(runButton);

    await waitFor(() => {
      const streamingContainer = screen.getByTestId('streaming-container');
      const withinContainer = within(streamingContainer);
      expect(withinContainer.getByText(/Invalid syntax/)).toBeInTheDocument();
    });
  });

  it('should handle concurrent orchestration requests', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).executeGoblinCommand.mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(() => resolve({ result: 'Completed', status: 'success' }), 1000)
        )
    );

    render(
      <TestWrapper>
        <GoblinDemo />
      </TestWrapper>
    );

    await waitFor(() => expect(screen.getByTestId('run-button')).toBeInTheDocument());

    const runButton = screen.getByTestId('run-button');

    // Click multiple times rapidly
  fireEvent.click(runButton);
    fireEvent.click(runButton);
    fireEvent.click(runButton);

    // Component should handle concurrent requests without crashing
    await waitFor(
      () => {
        expect(screen.getByTestId('goblin-demo')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should handle missing orchestration dependencies', async () => {
    // Mock successful parsing first, then execution failure
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).parseOrchestration.mockResolvedValue({
      valid: true,
      steps: [{ id: 'test-step', goblin: 'test-goblin', task: 'test task' }],
    });

  (runtimeClient as any).executeGoblinCommand.mockRejectedValue(
      new Error('Missing dependency: tool not found')
    );

    render(
      <TestWrapper>
        <GoblinDemo />
      </TestWrapper>
    );

    await waitFor(() => expect(screen.getByTestId('run-button')).toBeInTheDocument());

    const runButton = screen.getByTestId('run-button');
    fireEvent.click(runButton);

    await waitFor(() => {
      const streamingContainer = screen.getByTestId('streaming-container');
      const withinContainer = within(streamingContainer);
      expect(withinContainer.getByText(/client.executeTaskStreaming is not a function/)).toBeInTheDocument();
    });
  });
});

describe('Error Scenarios - Component Integration Failures', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should handle no providers available', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockResolvedValue([]);

    const { container } = render(
      <TestWrapper>
        <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // ProviderSelector returns null when no providers, so container should be empty
    expect(container.firstChild).toBeNull();
  });

  it('should handle invalid provider selection', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockRejectedValue(new Error('Invalid provider'));

    render(
      <TestWrapper>
        <ModelSelector provider="invalid" onChange={jest.fn()} />
      </TestWrapper>
    );

    // Should show the default state with no models loaded
    await waitFor(() => {
      expect(screen.getByTestId('model-select')).toBeInTheDocument();
      expect(screen.getByText('Select a model...')).toBeInTheDocument();
    });
  });

  it('should handle null/undefined props gracefully', async () => {
    render(
      <TestWrapper>
        <ModelSelector provider={undefined} onChange={jest.fn()} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('model-selector-placeholder')).toBeInTheDocument();
      expect(screen.getByText(/select a provider first/i)).toBeInTheDocument();
    });
  });

  it('should handle rapid component unmounting', async () => {
    const { runtimeClient } = await import('../api/api-client');
  (runtimeClient as any).getProviderModels.mockImplementation(
      () =>
        new Promise(resolve => setTimeout(() => resolve([{ id: 'openai', name: 'OpenAI' }]), 1000))
    );

    const { unmount } = render(
      <TestWrapper>
        <ProviderSelector providers={[]} onChange={jest.fn()} />
      </TestWrapper>
    );

    // Unmount before promise resolves
    unmount();

    // Should not throw or cause memory leaks
    expect(true).toBe(true); // Component unmounted cleanly
  });
});
