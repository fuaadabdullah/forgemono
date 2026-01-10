import React from 'react';
import { WorkflowStep, AVAILABLE_GOBLINS, CONDITION_TYPES } from '../../utils/workflowUtils';

interface WorkflowStepListProps {
  steps: WorkflowStep[];
  onRemoveStep: (stepId: string) => void;
  onUpdateCondition: (stepId: string, condition: WorkflowStep['condition']) => void;
  onMoveStep: (fromIndex: number, toIndex: number) => void;
}

export const WorkflowStepList: React.FC<WorkflowStepListProps> = ({
  steps,
  onRemoveStep,
  onUpdateCondition,
  onMoveStep,
}) => {
  if (steps.length === 0) {
    return (
      <div className="empty-state">
        <p>No steps added yet. Select a goblin and enter a task to get started.</p>
      </div>
    );
  }

  return (
    <div className="steps-list">
      {steps.map((step, index) => (
        <div key={step.id} className="step-item">
          <div className="step-controls">
            <button
              onClick={() => onRemoveStep(step.id)}
              className="remove-step-btn"
              title="Remove step"
            >
              ×
            </button>

            {index > 0 && (
              <>
                <button
                  onClick={() => onMoveStep(index, index - 1)}
                  className="move-step-btn"
                  title="Move up"
                  disabled={index === 0}
                >
                  ↑
                </button>
                <button
                  onClick={() => onMoveStep(index, index + 1)}
                  className="move-step-btn"
                  title="Move down"
                  disabled={index === steps.length - 1}
                >
                  ↓
                </button>
              </>
            )}
          </div>

          <div className="step-content">
            {index > 0 && (
              <select
                value={step.condition || 'THEN'}
                onChange={(e) =>
                  onUpdateCondition(step.id, e.target.value as WorkflowStep['condition'])
                }
                className="condition-select"
                aria-label={`Select condition for step ${index + 1}`}
              >
                {CONDITION_TYPES.map((condition) => (
                  <option key={condition.value} value={condition.value}>
                    {condition.label}
                  </option>
                ))}
              </select>
            )}

            <div className="step-details">
              <strong>
                {AVAILABLE_GOBLINS.find((g) => g.id === step.goblin)?.name || step.goblin}
              </strong>
              <span className="step-task">{step.task}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
