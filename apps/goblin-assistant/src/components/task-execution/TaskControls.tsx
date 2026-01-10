import React from 'react';
import { Button } from '../ui';

interface Props {
  goblins: any[];
  selectedGoblin: string;
  setSelectedGoblin: (id: string) => void;
  task: string;
  setTask: (t: string) => void;
  isStreaming: boolean;
  loading: boolean;
  startStreamingTask: () => void;
  cancelTask: () => void;
  clearOutput: () => void;
}

export const TaskControls: React.FC<Props> = ({
  goblins,
  selectedGoblin,
  setSelectedGoblin,
  task,
  setTask,
  isStreaming,
  loading,
  startStreamingTask,
  cancelTask,
  clearOutput,
}) => {
  return (
    <div className="bg-surface rounded-lg p-6 border border-border">
      <div className="space-y-4">
        <div>
          <label htmlFor="goblin-select" className="block text-sm font-medium text-text mb-2">
            Select Goblin
          </label>
          <select
            value={selectedGoblin}
            onChange={(e) => setSelectedGoblin(e.target.value)}
            id="goblin-select"
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
          <label className="block text-sm font-medium text-text mb-2">Task Description</label>
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
            <Button variant="danger" onClick={cancelTask}>
              Cancel Task
            </Button>
          )}

          <Button variant="secondary" onClick={clearOutput}>
            Clear Output
          </Button>
        </div>
      </div>
    </div>
  );
};
