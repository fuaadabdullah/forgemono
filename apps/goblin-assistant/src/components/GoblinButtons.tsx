/**
 * GoblinOS Button Components
 *
 * Accessible, neon-styled buttons that maintain WCAG AA contrast
 * while delivering the signature GoblinOS cyberpunk aesthetic.
 */

import React from 'react';
import { devLog } from '../utils/dev-log';

type BaseButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  className?: string;
};

type GhostVariant = 'primary' | 'accent' | 'danger';

/* ============================================================================
   PRIMARY CTA BUTTON - Goblin Green with Glow
   Use for primary actions: Deploy, Submit, Confirm
   ============================================================================ */
export function GoblinButton({
  children,
  onClick,
  disabled = false,
  className = '',
  ...props
}: BaseButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
  px-4 py-2 rounded-md text-sm font-semibold tracking-wide
  bg-primary text-text-inverse
  shadow-goblin-glow
        hover:scale-[1.02] hover:bg-primary-hover
        active:scale-[0.98]
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

/* ============================================================================
   CTA BUTTON - Burnt Orange for Calls-to-Action
   Use for secondary important actions: Deploy, Execute, Start
   ============================================================================ */
export function CtaButton({
  children,
  onClick,
  disabled = false,
  className = '',
  ...props
}: BaseButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
  px-4 py-2 rounded-md text-sm font-semibold tracking-wide
  bg-cta text-text-inverse
  shadow-glow-cta
        hover:scale-[1.02] hover:bg-cta-hover
        active:scale-[0.98]
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

/* ============================================================================
   GHOST BUTTON - Primary Color Outline
   Use for secondary actions: Cancel, Reset, Run Scan
   ============================================================================ */
export function GhostButton({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  className = '',
  ...props
}: BaseButtonProps & { variant?: GhostVariant }) {
  const variantClasses: Record<GhostVariant, string> = {
    primary: 'border-primary text-primary hover:bg-primary/10',
    accent: 'border-accent text-accent hover:bg-accent/10',
    danger: 'border-danger text-danger hover:bg-danger/10'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
  px-3 py-2 rounded-md text-sm font-medium tracking-wide
        border bg-transparent
        ${variantClasses[variant]}
        hover:scale-[1.01]
        active:scale-[0.99]
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

/* ============================================================================
   DANGER BUTTON - For Destructive Actions
   Use for: Delete, Remove, Terminate
   ============================================================================ */
export function DangerButton({
  children,
  onClick,
  disabled = false,
  className = '',
  ...props
}: BaseButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
  px-4 py-2 rounded-md text-sm font-semibold tracking-wide
  bg-danger text-text-inverse
  shadow-[0_6px_24px_rgba(255,71,87,0.18)]
        hover:scale-[1.02] hover:bg-danger/90
        active:scale-[0.98]
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

/* ============================================================================
   ICON BUTTON - Small, Icon-Only
   Use for: Close, Edit, Delete icons
   ============================================================================ */
type IconVariant = 'ghost' | 'primary' | 'danger';

export function IconButton({
  children,
  onClick,
  disabled = false,
  variant = 'ghost',
  className = '',
  'aria-label': ariaLabel,
  ...props
}: BaseButtonProps & { variant?: IconVariant; 'aria-label': string }) {
  const variantClasses: Record<IconVariant, string> = {
    ghost: 'text-muted hover:text-primary hover:bg-surface-hover/60',
    primary: 'text-primary hover:bg-primary/15',
    danger: 'text-danger hover:bg-danger/15'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={`
        p-2 rounded-md
        ${variantClasses[variant]}
        hover:scale-110
        active:scale-95
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

/* ============================================================================
   USAGE EXAMPLES
   ============================================================================ */

export function ButtonExamples() {
  return (
    <div className="space-y-6 p-6">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Primary Actions
        </h3>
        <div className="flex gap-3 flex-wrap">
          <GoblinButton onClick={() => devLog('Deploy!')}>
            Deploy Goblin
          </GoblinButton>
          <GoblinButton disabled>
            Deploying...
          </GoblinButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Call-to-Action
        </h3>
        <div className="flex gap-3 flex-wrap">
          <CtaButton onClick={() => devLog('Execute!')}>
            Execute Task
          </CtaButton>
          <CtaButton disabled>
            Processing...
          </CtaButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Secondary Actions (Ghost)
        </h3>
        <div className="flex gap-3 flex-wrap">
          <GhostButton variant="primary">
            Run Scan
          </GhostButton>
          <GhostButton variant="accent">
            View Details
          </GhostButton>
          <GhostButton variant="danger">
            Cancel
          </GhostButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Destructive Actions
        </h3>
        <div className="flex gap-3 flex-wrap">
          <DangerButton onClick={() => devLog('Delete!')}>
            Delete Resource
          </DangerButton>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">
          Icon Buttons
        </h3>
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
