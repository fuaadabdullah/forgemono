import { useState, useEffect } from 'react';
import {
  WorkflowStep,
  parseOrchestrationToSteps,
  buildOrchestrationFromSteps,
} from '../utils/workflowUtils';

interface UseWorkflowStateProps {
  onOrchestrationChange: (orchestration: string) => void;
  initialOrchestration?: string;
}

export const useWorkflowState = ({
  onOrchestrationChange,
  initialOrchestration = '',
}: UseWorkflowStateProps) => {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [selectedGoblin, setSelectedGoblin] = useState<string>('');
  const [taskInput, setTaskInput] = useState<string>('');
  const [isBuilderMode, setIsBuilderMode] = useState<boolean>(false);

  // Parse initial orchestration if provided
  useEffect(() => {
    if (initialOrchestration && !isBuilderMode) {
      const parsedSteps = parseOrchestrationToSteps(initialOrchestration);
      setSteps(parsedSteps);
    }
  }, [initialOrchestration]);

  // Update orchestration string when steps change
  useEffect(() => {
    const orchestration = buildOrchestrationFromSteps(steps);
    onOrchestrationChange(orchestration);
  }, [steps, onOrchestrationChange]);

  const addStep = () => {
    if (!selectedGoblin || !taskInput.trim()) return;

    const newStep: WorkflowStep = {
      id: `step-${Date.now()}`,
      goblin: selectedGoblin,
      task: taskInput.trim(),
      condition: steps.length > 0 ? 'THEN' : undefined,
    };

    setSteps([...steps, newStep]);
    setTaskInput('');
  };

  const removeStep = (stepId: string) => {
    setSteps(steps.filter((step) => step.id !== stepId));
  };

  const updateStepCondition = (stepId: string, condition: WorkflowStep['condition']) => {
    setSteps(steps.map((step) => (step.id === stepId ? { ...step, condition } : step)));
  };

  const moveStep = (fromIndex: number, toIndex: number) => {
    const newSteps = [...steps];
    const [movedStep] = newSteps.splice(fromIndex, 1);
    newSteps.splice(toIndex, 0, movedStep);
    setSteps(newSteps);
  };

  const toggleBuilderMode = () => {
    setIsBuilderMode(!isBuilderMode);
    if (!isBuilderMode) {
      // Switching to builder mode - parse current orchestration
      const parsedSteps = parseOrchestrationToSteps(initialOrchestration);
      setSteps(parsedSteps);
    }
  };

  const getCurrentOrchestration = () => buildOrchestrationFromSteps(steps);

  return {
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
  };
};
