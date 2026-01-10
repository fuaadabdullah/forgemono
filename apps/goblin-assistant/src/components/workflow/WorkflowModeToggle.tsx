import React from 'react';

interface WorkflowModeToggleProps {
  isBuilderMode: boolean;
  onToggle: () => void;
}

export const WorkflowModeToggle: React.FC<WorkflowModeToggleProps> = ({
  isBuilderMode,
  onToggle,
}) => {
  return (
    <div className="builder-header">
      <h3>Workflow Builder</h3>
      <button onClick={onToggle} className={`mode-toggle ${isBuilderMode ? 'active' : ''}`}>
        {isBuilderMode ? 'Text Mode' : 'Visual Builder'}
      </button>
    </div>
  );
};
