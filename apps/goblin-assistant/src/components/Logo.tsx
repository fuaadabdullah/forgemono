import { useEffect, useState } from 'react';
import { Bot } from 'lucide-react';

interface LogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'full' | 'simple' | 'emoji';
  className?: string;
  animated?: boolean;
}

const sizeMap = {
  xs: 16,
  sm: 24,
  md: 32,
  lg: 48,
  xl: 64,
};

/**
 * Theme-adaptive logo component with multiple variants and sizes
 *
 * @param size - xs(16px), sm(24px), md(32px), lg(48px), xl(64px)
 * @param variant - full (detailed), simple (minimal), emoji (fallback)
 * @param animated - Add subtle animation on hover
 */
export default function Logo({
  size = 'md',
  variant = 'full',
  className = '',
  animated = true,
}: LogoProps) {
  const [logoError, setLogoError] = useState(false);
  const pixelSize = sizeMap[size];

  // Fallback to emoji if SVG fails to load
  useEffect(() => {
    setLogoError(false);
  }, [variant]);

  if (variant === 'emoji' || logoError) {
    return (
      <span
        className={`inline-block ${animated ? 'logo-animated' : ''} ${className}`}
        role="img"
        aria-label="Goblin Assistant"
      >
        <Bot className={`w-${Math.round(pixelSize / 4)} h-${Math.round(pixelSize / 4)} text-primary`} />
      </span>
    );
  }
  const logoSrc = variant === 'simple' ? '/goblin-logo.png' : '/goblin-logo.png';

  return (
    <img
      src={logoSrc}
      alt="Goblin Assistant Logo"
      width={pixelSize}
      height={pixelSize}
      className={`inline-block ${animated ? 'logo-transition' : ''} ${className}`}
      onError={() => setLogoError(true)}
    />
  );
}
