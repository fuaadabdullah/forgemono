import { useState, useEffect } from 'react';
import { apiClient } from '../api/client-axios';
import { Button, Alert } from './ui';

interface StreamChunk {
  content?: string;
  token_count?: number;
  cost_delta?: number;
  done?: boolean;
  result?: string;
  cost?: number;
  tokens?: number;
}

const TaskExecution = () => {
  const [goblins, setGoblins] = useState<any[]>([]);
  const [selectedGoblin, setSelectedGoblin] = useState('');
  const [task, setTask] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamId, setStreamId] = useState<string | null>(null);
  const [streamOutput, setStreamOutput] = useState<StreamChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadGoblins = async () => {
      try {
        const goblinsData = await apiClient.getGoblins();
        setGoblins(goblinsData);
        if (goblinsData.length > 0) {
          setSelectedGoblin(goblinsData[0].id);
        }
      } catch (err) {
        setError('Failed to load goblins');
        console.error('Load goblins error:', err);
      }
    };

    loadGoblins();
  }, []);

  const startStreamingTask = async () => {
    if (!selectedGoblin || !task.trim()) {
      setError('Please select a goblin and enter a task');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setStreamOutput([]);
      setIsStreaming(true);

      const response = await apiClient.startStreamingTask({
        goblin: selectedGoblin,
        task: task.trim(),
      });

      setStreamId(response.stream_id);

      // Start polling for updates
      pollStream(response.stream_id);
    } catch (err) {
      setError('Failed to start task');
      setIsStreaming(false);
      console.error('Start task error:', err);
    } finally {
      setLoading(false);
    }
  };

  const pollStream = async (id: string) => {
    try {
      const response = await apiClient.pollStreamingTask(id);

      if (response.chunks && response.chunks.length > 0) {
        setStreamOutput(prev => [...prev, ...response.chunks]);
      }

      if (!response.done) {
        // Continue polling
        setTimeout(() => pollStream(id), 1000);
      } else {
        setIsStreaming(false);
        setStreamId(null);
      }
    } catch (err) {
      setError('Failed to poll stream');
      setIsStreaming(false);
      console.error('Poll stream error:', err);
    }
  };

  const cancelTask = async () => {
    if (!streamId) return;

    try {
      await apiClient.cancelStreamingTask(streamId);
      setIsStreaming(false);
      setStreamId(null);
      setStreamOutput(prev => [...prev, { content: '\n[Task cancelled]', done: true }]);
    } catch (err) {
      setError('Failed to cancel task');
      console.error('Cancel task error:', err);
    }
  };

  const clearOutput = () => {
    setStreamOutput([]);
    setError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text mb-2">Task Execution</h1>
        <p className="text-muted">Execute tasks with real-time streaming output</p>
      </div>

      {/* Live region for streaming updates */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="false">
        {isStreaming && streamOutput.length > 0 && `Received ${streamOutput.length} update${streamOutput.length !== 1 ? 's' : ''}`}
        {!isStreaming && streamOutput.length > 0 && streamOutput[streamOutput.length - 1]?.done && 'Task completed'}
      </div>

      {/* Task Input Form */}
      <div className="bg-surface rounded-lg p-6 border border-border">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Select Goblin
            </label>
            <select
              value={selectedGoblin}
              onChange={(e) => setSelectedGoblin(e.target.value)}
              className="w-full px-3 py-2 bg-surface-hover border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={isStreaming}
            >
              {goblins.map((goblin) => (
                <option key={goblin.id} value={goblin.id}>
                  {goblin.title} ({goblin.guild})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Task Description
            </label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Describe the task you want to execute..."
              className="w-full px-3 py-2 bg-surface-hover border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-primary h-32 resize-none placeholder-muted"
              disabled={isStreaming}
            />
          </div>

          <div className="flex space-x-4">
            <Button
              variant="primary"
              onClick={startStreamingTask}
              disabled={isStreaming || loading || !selectedGoblin || !task.trim()}
              loading={loading}
            >
              Execute Task
            </Button>

            {isStreaming && (
              <Button
                variant="danger"
                onClick={cancelTask}
              >
                Cancel Task
              </Button>
            )}

            <Button
              variant="secondary"
              onClick={clearOutput}
            >
              Clear Output
            </Button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert
          variant="danger"
          title="Error"
          message={error}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}

      {/* Streaming Output */}
      {streamOutput.length > 0 && (
        <div className="bg-surface rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-text">Task Output</h2>
            {isStreaming && (
              <div className="flex items-center text-primary">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
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
      )}
    </div>
  );
};

export default TaskExecution;
