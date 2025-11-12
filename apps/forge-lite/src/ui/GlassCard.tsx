import React, { PropsWithChildren } from 'react';
import { Platform, View, ViewStyle } from 'react-native';
import { BlurView } from 'expo-blur';
import { useTokens } from './tokens';

type Props = PropsWithChildren<{
  style?: ViewStyle;
  intensity?: number;
  padded?: boolean;
}>;

export function GlassCard({ children, style, intensity = 24, padded = true }: Props) {
  const { colors, radius, spacing } = useTokens();
  const padding = padded ? spacing.lg : 0;

  if (Platform.OS === 'ios') {
    return (
      <BlurView tint="dark" intensity={intensity} style={[{ borderRadius: radius.md, overflow: 'hidden' }, style] as any}>
        <View style={{ padding }}>{children}</View>
      </BlurView>
    );
  }

  // Android/web fallback: semi-transparent card
  return (
    <View
      style={[
        {
          backgroundColor: 'rgba(255,255,255,0.04)',
          borderColor: colors.border,
          borderWidth: 1,
          borderRadius: radius.md,
          padding,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

export default GlassCard;

