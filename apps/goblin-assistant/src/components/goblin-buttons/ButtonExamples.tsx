/* React 17+ automatic JSX runtime (no default import required) */
import { GoblinButton } from './GoblinButton';
import { CtaButton } from './CtaButton';
import { GhostButton } from './GhostButton';
import { DangerButton } from './DangerButton';
import { IconButton } from './IconButton';
import { devLog } from '../../utils/dev-log';

export function ButtonExamples() {
  return (
    <div className="space-y-6 p-6">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Primary Actions
        </h3>
        <div className="flex gap-3 flex-wrap">
          <GoblinButton onClick={() => devLog('Deploy!')}>Deploy Goblin</GoblinButton>
          <GoblinButton disabled>Deploying...</GoblinButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">Call-to-Action</h3>
        <div className="flex gap-3 flex-wrap">
          <CtaButton onClick={() => devLog('Execute!')}>Execute Task</CtaButton>
          <CtaButton disabled>Processing...</CtaButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Secondary Actions (Ghost)
        </h3>
        <div className="flex gap-3 flex-wrap">
          <GhostButton variant="primary">Run Scan</GhostButton>
          <GhostButton variant="accent">View Details</GhostButton>
          <GhostButton variant="danger">Cancel</GhostButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Destructive Actions
        </h3>
        <div className="flex gap-3 flex-wrap">
          <DangerButton onClick={() => devLog('Delete!')}>Delete Resource</DangerButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">Icon Buttons</h3>
        <div className="flex gap-3 flex-wrap">
          <IconButton variant="ghost" aria-label="Close">
            ✕
          </IconButton>
          <IconButton variant="primary" aria-label="Edit">
            ✎
          </IconButton>
          <IconButton variant="danger" aria-label="Delete">
            🗑
          </IconButton>
        </div>
      </div>
    </div>
  );
}
