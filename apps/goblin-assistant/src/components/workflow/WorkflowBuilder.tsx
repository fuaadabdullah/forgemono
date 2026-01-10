import { useWorkflowState } from '../../hooks/useWorkflowState';
import { WorkflowModeToggle } from './WorkflowModeToggle';
import { WorkflowVisualBuilder } from './WorkflowVisualBuilder';
import { WorkflowTextMode } from './WorkflowTextMode';
import { WorkflowOutput } from './WorkflowOutput';
import './WorkflowBuilder.css';

interface WorkflowBuilderProps {
  onOrchestrationChange: (orchestration: string) => void;
  initialOrchestration?: string;
}

export default function WorkflowBuilder({
  onOrchestrationChange,
  initialOrchestration = '',
}: WorkflowBuilderProps) {
  const {
    steps,
    selectedGoblin,
    setSelectedGoblin,
    taskInput,
    setTaskInput,
    isBuilderMode,
    addStep,
    removeStep,
    updateStepCondition,
    moveStep,
    toggleBuilderMode,
    getCurrentOrchestration,
  } = useWorkflowState({
    onOrchestrationChange,
    initialOrchestration,
  });

  return (
    <div className="workflow-builder">
      <WorkflowModeToggle isBuilderMode={isBuilderMode} onToggle={toggleBuilderMode} />

      {isBuilderMode ? (
        <WorkflowVisualBuilder
          steps={steps}
          selectedGoblin={selectedGoblin}
          setSelectedGoblin={setSelectedGoblin}
          taskInput={taskInput}
          setTaskInput={setTaskInput}
          onAddStep={addStep}
          onRemoveStep={removeStep}
          onUpdateCondition={updateStepCondition}
          onMoveStep={moveStep}
        />
      ) : (
        <WorkflowTextMode />
      )}

      <WorkflowOutput orchestration={getCurrentOrchestration()} />
    </div>
  );
}
