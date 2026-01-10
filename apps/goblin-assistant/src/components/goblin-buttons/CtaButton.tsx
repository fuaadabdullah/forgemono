/* React 17+ automatic JSX runtime (no default import required) */
import { getButtonClasses } from './buttonStyles';

type BaseButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { className?: string };

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
      className={`${getButtonClasses('cta', className)}`}
      {...props}
    >
      {children}
    </button>
  );
}
