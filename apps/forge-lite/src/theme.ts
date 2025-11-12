import { palettes, useTokens } from './ui/tokens';

export const colors = palettes;

export function useTheme() {
  return useTokens();
}
