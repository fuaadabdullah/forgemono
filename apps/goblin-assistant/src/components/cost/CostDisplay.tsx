import React from 'react';
import { CostEstimate, formatCost, getCostColor } from '../../utils/costUtils';

interface CostDisplayProps {
  estimate: CostEstimate;
}

export const CostDisplay: React.FC<CostDisplayProps> = ({ estimate }) => {
  return (
    <div className="estimate-results">
      <div className="total-cost">
        <span className="label">Total Estimated Cost:</span>
        <span className={`value ${getCostColor(estimate.totalCost)}`}>
          {formatCost(estimate.totalCost)}
        </span>
      </div>

      <div className="cost-breakdown">
        <h5>Step-by-Step Breakdown</h5>
        <div className="step-costs">
          {estimate.stepCosts.map((step, index) => (
            <div key={step.stepId} className="step-cost-item">
              <div className="step-info">
                <span className="step-number">{index + 1}.</span>
                <span className="step-goblin">{step.goblin}</span>
                <span className="step-task" title={step.task}>
                  {step.task.length > 30 ? `${step.task.substring(0, 30)}...` : step.task}
                </span>
              </div>
              <div className="step-cost-details">
                <span className="tokens">~{step.tokenEstimate} tokens</span>
                <span className={`cost ${getCostColor(step.estimatedCost)}`}>
                  {formatCost(step.estimatedCost)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="estimate-disclaimer">
        <small>
          * Estimates are approximate and based on typical token usage. Actual costs may vary based
          on actual response lengths and provider rates.
        </small>
      </div>
    </div>
  );
};
