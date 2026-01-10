/* React 17+ automatic JSX runtime (no default import required) */
import { getButtonClasses } from './buttonStyles';

type BaseButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { className?: string };

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
      className={`${getButtonClasses('danger', className)}`}
      {...props}
    >
      {children}
    </button>
  );
}
