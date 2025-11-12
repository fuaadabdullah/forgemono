import React, { PropsWithChildren } from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { useTokens } from './tokens';

type Variant = 'surface' | 'elevated' | 'outline';

type Props = PropsWithChildren<{
  style?: ViewStyle | ViewStyle[];
  variant?: Variant;
  padded?: boolean;
}>;

export function Card({ children, style, variant = 'surface', padded = true }: Props) {
  const { colors, radius, shadow, spacing } = useTokens();
  const base: ViewStyle = {
    borderRadius: radius.md,
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    overflow: 'hidden',
    padding: padded ? spacing.lg : 0,
  };

  const variants: Record<Variant, ViewStyle> = {
    surface: {},
    elevated: { ...(shadow.sm as any) },
    outline: { backgroundColor: 'transparent' },
  };

  return <View style={[base, variants[variant], style]}>{children}</View>;
}

export default Card;

