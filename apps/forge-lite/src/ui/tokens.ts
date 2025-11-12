import { useColorScheme } from 'react-native';

export type Palette = {
  background: string;
  text: string;
  muted: string;
  tint: string;
  card: string;
  border: string;
  positive: string;
  negative: string;
};

export const palettes: Record<'light' | 'dark', Palette> = {
  light: {
    background: '#ffffff',
    text: '#111827',
    muted: '#6b7280',
    tint: '#0A84FF',
    card: '#f3f4f6',
    border: '#e5e7eb',
    positive: '#30D158',
    negative: '#FF3B30',
  },
  dark: {
    background: '#0b0f19',
    text: '#e5e7eb',
    muted: '#9ca3af',
    tint: '#0A84FF',
    card: '#0f1422',
    border: '#1b2132',
    positive: '#30D158',
    negative: '#FF3B30',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 999,
} as const;

export const typography = {
  title: { fontSize: 28, lineHeight: 34, fontWeight: '700' as const },
  subtitle: { fontSize: 16, lineHeight: 22, fontWeight: '400' as const },
  h2: { fontSize: 20, lineHeight: 26, fontWeight: '600' as const },
  body: { fontSize: 16, lineHeight: 22, fontWeight: '400' as const },
  caption: { fontSize: 12, lineHeight: 16, fontWeight: '400' as const },
} as const;

export const shadow = {
  sm: {
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  none: {},
} as const;

export const surfaces = {
  surface1: (p: Palette) => ({ backgroundColor: p.card, borderColor: p.border }),
  surface2: (p: Palette) => ({ backgroundColor: '#0e1220', borderColor: p.border }),
} as const;

export function useTokens() {
  const scheme = useColorScheme() === 'dark' ? 'dark' : 'light';
  const colors = palettes[scheme];
  return { scheme, colors, spacing, radius, typography, shadow, surfaces } as const;
}
