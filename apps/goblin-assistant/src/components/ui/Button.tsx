import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  icon?: ReactNode;
  loading?: boolean;
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-text-inverse hover:brightness-110 shadow-glow-primary',
  secondary: 'bg-surface-hover text-text border border-border hover:bg-surface-active',
  danger: 'bg-danger text-text-inverse hover:brightness-110 shadow-glow-cta',
  success: 'bg-success text-text-inverse hover:brightness-110',
  ghost: 'bg-surface text-text border border-border hover:bg-surface-hover',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

/**
 * Button — unified button component with variants and sizes.
 * Replaces duplicate button styles across the app.
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  icon,
  loading = false,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const baseStyles = 'rounded-lg font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed';
  const widthStyles = fullWidth ? 'w-full' : '';
  const flexStyles = icon ? 'flex items-center justify-center gap-2' : '';

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${widthStyles} ${flexStyles} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="animate-spin">⟳</span>}
      {!loading && icon && <span>{icon}</span>}
      {children}
    </button>
  );
}
