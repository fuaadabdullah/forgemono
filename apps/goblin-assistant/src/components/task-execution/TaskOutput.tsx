import React from 'react';
import { StreamChunk } from '../../hooks/useTaskExecution';

interface Props {
  streamOutput: StreamChunk[];
  isStreaming: boolean;
}

export const TaskOutput: React.FC<Props> = ({ streamOutput, isStreaming }) => {
  if (streamOutput.length === 0) return null;

  return (
    <div className="bg-surface rounded-lg p-6 border border-border">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-text">Task Output</h2>
        {isStreaming && (
          <div className="flex items-center text-primary">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2" />
            Streaming...
          </div>
        )}
      </div>

      <div className="bg-bg rounded-lg p-4 font-mono text-sm text-text max-h-96 overflow-y-auto border border-border">
        {streamOutput.map((chunk, index) => (
          <div key={index} className="whitespace-pre-wrap">
            {chunk.content || ''}
            {chunk.done && (
              <div className="mt-2 pt-2 border-t border-border text-muted">
                <div>Tokens: {chunk.tokens}</div>
                <div>Cost: ${chunk.cost?.toFixed(4)}</div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
