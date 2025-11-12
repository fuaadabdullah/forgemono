import React, { PropsWithChildren } from 'react';
import { View, ViewStyle } from 'react-native';
import { useTokens } from './tokens';

type Props = PropsWithChildren<{
  height?: number;
  style?: ViewStyle;
  padded?: boolean;
}>;

// A neutral, dark surface for chart content (SVG/Canvas). Handles padding and rounding.
export function ChartContainer({ height = 220, padded = true, style, children }: Props) {
  const { colors, radius, spacing } = useTokens();
  return (
    <View
      style={{
        height,
        backgroundColor: colors.card,
        borderColor: colors.border,
        borderWidth: 1,
        borderRadius: radius.md,
        overflow: 'hidden',
        padding: padded ? spacing.lg : 0,
        ...style,
      }}
    >
      {children}
    </View>
  );
}

export default ChartContainer;

