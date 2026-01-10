// Workflow utility functions and types
export interface WorkflowStep {
  id: string;
  goblin: string;
  task: string;
  condition?: 'THEN' | 'AND' | 'IF_SUCCESS' | 'IF_FAILURE';
}

export interface WorkflowGoblin {
  id: string;
  name: string;
  description: string;
}

export interface WorkflowCondition {
  value: 'THEN' | 'AND' | 'IF_SUCCESS' | 'IF_FAILURE';
  label: string;
  description: string;
}

export const AVAILABLE_GOBLINS: WorkflowGoblin[] = [
  {
    id: 'docs-writer',
    name: 'Documentation Writer',
    description: 'Documents code and writes comments',
  },
  { id: 'code-writer', name: 'Code Writer', description: 'Writes and refactors code' },
  { id: 'analyze', name: 'Analyzer', description: 'Analyzes code quality and patterns' },
  { id: 'chat', name: 'Chat Assistant', description: 'General conversation and Q&A' },
  { id: 'translate', name: 'Translator', description: 'Language translation tasks' },
  { id: 'summarize', name: 'Summarizer', description: 'Text summarization and condensation' },
];

export const CONDITION_TYPES: WorkflowCondition[] = [
  {
    value: 'THEN',
    label: 'Then (Sequential)',
    description: 'Execute next step after this completes',
  },
  {
    value: 'AND',
    label: 'And (Parallel)',
    description: 'Execute simultaneously with previous step',
  },
  {
    value: 'IF_SUCCESS',
    label: 'If Success',
    description: 'Execute only if previous step succeeds',
  },
  { value: 'IF_FAILURE', label: 'If Failure', description: 'Execute only if previous step fails' },
];

export const parseOrchestrationToSteps = (orchestration: string): WorkflowStep[] => {
  // Simple parser for existing orchestration syntax
  const parts = orchestration.split(/\s+(THEN|AND|IF_SUCCESS|IF_FAILURE)\s+/i);
  const parsedSteps: WorkflowStep[] = [];

  for (let i = 0; i < parts.length; i += 2) {
    const taskPart = parts[i].trim();
    const condition = i > 0 ? (parts[i - 1] as WorkflowStep['condition']) : undefined;

    // Parse goblin:task format
    const goblinMatch = taskPart.match(/^(\w+):\s*(.+)$/);
    if (goblinMatch) {
      parsedSteps.push({
        id: `step-${parsedSteps.length + 1}`,
        goblin: goblinMatch[1],
        task: goblinMatch[2],
        condition,
      });
    } else {
      // Default goblin for tasks without explicit goblin
      parsedSteps.push({
        id: `step-${parsedSteps.length + 1}`,
        goblin: 'code-writer',
        task: taskPart,
        condition,
      });
    }
  }

  return parsedSteps;
};

export const buildOrchestrationFromSteps = (steps: WorkflowStep[]): string => {
  if (steps.length === 0) return '';

  let result = '';
  steps.forEach((step, index) => {
    if (index > 0 && step.condition) {
      result += ` ${step.condition} `;
    }
    result += `${step.goblin}: ${step.task}`;
  });

  return result;
};
