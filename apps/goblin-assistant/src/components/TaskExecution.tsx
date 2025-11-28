import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

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
        <h1 className="text-3xl font-bold text-white mb-2">Task Execution</h1>
        <p className="text-gray-400">Execute tasks with real-time streaming output</p>
      </div>

      {/* Task Input Form */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Select Goblin
            </label>
            <select
              value={selectedGoblin}
              onChange={(e) => setSelectedGoblin(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Task Description
            </label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Describe the task you want to execute..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none"
              disabled={isStreaming}
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={startStreamingTask}
              disabled={isStreaming || loading || !selectedGoblin || !task.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
            >
              {loading ? 'Starting...' : 'Execute Task'}
            </button>

            {isStreaming && (
              <button
                onClick={cancelTask}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
              >
                Cancel Task
              </button>
            )}

            <button
              onClick={clearOutput}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
            >
              Clear Output
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4">
          <h3 className="text-red-400 font-semibold">Error</h3>
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {/* Streaming Output */}
      {streamOutput.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Task Output</h2>
            {isStreaming && (
              <div className="flex items-center text-blue-400">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400 mr-2"></div>
                Streaming...
              </div>
            )}
          </div>

          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-300 max-h-96 overflow-y-auto">
            {streamOutput.map((chunk, index) => (
              <div key={index} className="whitespace-pre-wrap">
                {chunk.content || ''}
                {chunk.done && (
                  <div className="mt-2 pt-2 border-t border-gray-700 text-gray-500">
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
