import React from 'react';
import { WorkflowStep } from '../../utils/workflowUtils';
import { WorkflowStepAdder } from './WorkflowStepAdder';
import { WorkflowStepList } from './WorkflowStepList';

interface WorkflowVisualBuilderProps {
  steps: WorkflowStep[];
  selectedGoblin: string;
  setSelectedGoblin: (goblin: string) => void;
  taskInput: string;
  setTaskInput: (task: string) => void;
  onAddStep: () => void;
  onRemoveStep: (stepId: string) => void;
  onUpdateCondition: (stepId: string, condition: WorkflowStep['condition']) => void;
  onMoveStep: (fromIndex: number, toIndex: number) => void;
}

export const WorkflowVisualBuilder: React.FC<WorkflowVisualBuilderProps> = ({
  steps,
  selectedGoblin,
  setSelectedGoblin,
  taskInput,
  setTaskInput,
  onAddStep,
  onRemoveStep,
  onUpdateCondition,
  onMoveStep,
}) => {
  return (
    <div className="visual-builder">
      <WorkflowStepAdder
        selectedGoblin={selectedGoblin}
        setSelectedGoblin={setSelectedGoblin}
        taskInput={taskInput}
        setTaskInput={setTaskInput}
        onAddStep={onAddStep}
      />

      <WorkflowStepList
        steps={steps}
        onRemoveStep={onRemoveStep}
        onUpdateCondition={onUpdateCondition}
        onMoveStep={onMoveStep}
      />
    </div>
  );
};
