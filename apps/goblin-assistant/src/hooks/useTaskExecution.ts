import { useState, useRef, useEffect } from 'react';
import { apiClient } from '../api/client-axios';

export interface StreamChunk {
  content?: string;
  token_count?: number;
  cost_delta?: number;
  done?: boolean;
  result?: string;
  cost?: number;
  tokens?: number;
}

export const useTaskExecution = () => {
  const [goblins, setGoblins] = useState<any[]>([]);
  const [selectedGoblin, setSelectedGoblin] = useState('');
  const [task, setTask] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamId, setStreamId] = useState<string | null>(null);
  const [streamOutput, setStreamOutput] = useState<StreamChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollTimer = useRef<number | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const loadGoblins = async () => {
      try {
        const goblinsData = await apiClient.getGoblins();
        if (!isMounted.current) return;
        setGoblins(goblinsData);
        if (goblinsData.length > 0) {
          setSelectedGoblin(goblinsData[0].id);
        }
      } catch (err) {
        if (!isMounted.current) return;
        setError('Failed to load goblins');
        console.error('Load goblins error:', err);
      }
    };

    loadGoblins();

    return () => {
      isMounted.current = false;
      if (pollTimer.current) {
        window.clearTimeout(pollTimer.current);
      }
    };
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
        setStreamOutput((prev) => [...prev, ...response.chunks]);
      }

      if (!response.done) {
        // Continue polling
        pollTimer.current = window.setTimeout(() => pollStream(id), 1000);
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
      setStreamOutput((prev) => [...prev, { content: '\n[Task cancelled]', done: true }]);
      if (pollTimer.current) {
        window.clearTimeout(pollTimer.current);
        pollTimer.current = null;
      }
    } catch (err) {
      setError('Failed to cancel task');
      console.error('Cancel task error:', err);
    }
  };

  const clearOutput = () => {
    setStreamOutput([]);
    setError(null);
  };

  return {
    goblins,
    selectedGoblin,
    setSelectedGoblin,
    task,
    setTask,
    isStreaming,
    streamOutput,
    loading,
    error,
    startStreamingTask,
    cancelTask,
    clearOutput,
    clearError: () => setError(null),
  };
};
