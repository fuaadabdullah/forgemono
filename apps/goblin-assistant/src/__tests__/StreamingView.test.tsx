/// <reference types="@testing-library/jest-dom" />
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from '@jest/globals';
import StreamingView from '@/components/streaming/StreamingView';

// Re-import jest-dom to ensure types are available
import '@testing-library/jest-dom';

describe('StreamingView', () => {
  it('renders streaming text when streaming is active', () => {
    render(<StreamingView streamingText={'hello'} isStreaming={true} />);

    expect(screen.getByText('hello')).toBeInTheDocument();
    expect(screen.getByText('Streaming Output')).toBeInTheDocument();
  });

  it('renders complete text when not streaming', () => {
    render(<StreamingView streamingText={'hello'} isStreaming={false} />);

    expect(screen.getByText('hello')).toBeInTheDocument();
    expect(screen.getByText('Generated Content')).toBeInTheDocument();
  });
});
