import { useTaskExecution } from '../hooks/useTaskExecution';
import { TaskControls } from './task-execution/TaskControls';
import { TaskOutput } from './task-execution/TaskOutput';
import Alert from './ui/Alert';

const TaskExecution = () => {
  const {
    goblins,
    selectedGoblin,
    setSelectedGoblin,
    task,
    setTask,
    isStreaming,
    streamOutput,
    loading,
    error,
    clearError,
    startStreamingTask,
    cancelTask,
    clearOutput,
  } = useTaskExecution();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text mb-2">Task Execution</h1>
        <p className="text-muted">Execute tasks with real-time streaming output</p>
      </div>

      {/* Live region for streaming updates */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="false">
        {isStreaming &&
          streamOutput.length > 0 &&
          `Received ${streamOutput.length} update${streamOutput.length !== 1 ? 's' : ''}`}
        {!isStreaming &&
          streamOutput.length > 0 &&
          streamOutput[streamOutput.length - 1]?.done &&
          'Task completed'}
      </div>

      {/* Task Input Form */}
      <TaskControls
        goblins={goblins}
        selectedGoblin={selectedGoblin}
        setSelectedGoblin={setSelectedGoblin}
        task={task}
        setTask={setTask}
        isStreaming={isStreaming}
        loading={loading}
        startStreamingTask={startStreamingTask}
        cancelTask={cancelTask}
        clearOutput={clearOutput}
      />

      {/* Error Display */}
      {error && (
        <Alert
          variant="danger"
          title="Error"
          message={error}
          dismissible
          onDismiss={() => clearError()}
        />
      )}

      <TaskOutput streamOutput={streamOutput} isStreaming={isStreaming} />
    </div>
  );
};

export default TaskExecution;
