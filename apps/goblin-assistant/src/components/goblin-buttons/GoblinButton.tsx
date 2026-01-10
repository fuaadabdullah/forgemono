/* React 17+ automatic JSX runtime (no default import required) */
import { getButtonClasses } from './buttonStyles';
// optional logging can be used by callers via devLog from utils

type BaseButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  className?: string;
};

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
      className={`${getButtonClasses('primary', className)}`}
      {...props}
    >
      {children}
    </button>
  );
}
