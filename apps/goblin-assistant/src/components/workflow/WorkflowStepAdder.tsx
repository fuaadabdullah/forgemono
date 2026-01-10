import React from 'react';
import { AVAILABLE_GOBLINS } from '../../utils/workflowUtils';

interface WorkflowStepAdderProps {
  selectedGoblin: string;
  setSelectedGoblin: (goblin: string) => void;
  taskInput: string;
  setTaskInput: (task: string) => void;
  onAddStep: () => void;
}

export const WorkflowStepAdder: React.FC<WorkflowStepAdderProps> = ({
  selectedGoblin,
  setSelectedGoblin,
  taskInput,
  setTaskInput,
  onAddStep,
}) => {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onAddStep();
    }
  };

  return (
    <div className="step-adder">
      <select
        value={selectedGoblin}
        onChange={(e) => setSelectedGoblin(e.target.value)}
        className="goblin-select"
        aria-label="Select goblin for workflow step"
      >
        <option value="">Select Goblin</option>
        {AVAILABLE_GOBLINS.map((goblin) => (
          <option key={goblin.id} value={goblin.id}>
            {goblin.name}
          </option>
        ))}
      </select>

      <input
        type="text"
        value={taskInput}
        onChange={(e) => setTaskInput(e.target.value)}
        placeholder="Enter task description..."
        className="task-input"
        onKeyPress={handleKeyPress}
      />

      <button
        onClick={onAddStep}
        className="add-step-btn"
        disabled={!selectedGoblin || !taskInput.trim()}
      >
        Add Step
      </button>
    </div>
  );
};
