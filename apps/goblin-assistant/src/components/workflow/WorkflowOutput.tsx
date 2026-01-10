import React from 'react';

interface WorkflowOutputProps {
  orchestration: string;
}

export const WorkflowOutput: React.FC<WorkflowOutputProps> = ({ orchestration }) => {
  return (
    <div className="orchestration-output">
      <label>Generated Orchestration:</label>
      <code className="orchestration-text">{orchestration || 'No steps configured'}</code>
    </div>
  );
};
