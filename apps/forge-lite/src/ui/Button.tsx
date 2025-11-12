import React from 'react';
import { ActivityIndicator, GestureResponderEvent, StyleSheet, Text, TouchableOpacity, ViewStyle } from 'react-native';
import { useTokens } from './tokens';

type Variant = 'primary' | 'secondary' | 'ghost';
type Size = 'sm' | 'md' | 'lg';

type Props = {
  title: string;
  onPress?: (e: GestureResponderEvent) => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: Variant;
  size?: Size;
  style?: ViewStyle;
};

export function Button({
  title,
  onPress,
  disabled,
  loading,
  variant = 'primary',
  size = 'md',
  style,
}: Props) {
  const { colors, spacing, radius } = useTokens();

  const sizes: Record<Size, { padV: number; padH: number; font: number }> = {
    sm: { padV: spacing.sm + 4, padH: spacing.lg, font: 14 },
    md: { padV: spacing.lg, padH: spacing.xl, font: 16 },
    lg: { padV: spacing.xl, padH: spacing.xxl, font: 18 },
  };

  const base: ViewStyle = {
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: sizes[size].padV,
    paddingHorizontal: sizes[size].padH,
    opacity: disabled ? 0.6 : 1,
  };

  const variants: Record<Variant, ViewStyle> = {
    primary: { backgroundColor: colors.tint },
    secondary: { backgroundColor: colors.card, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
    ghost: { backgroundColor: 'transparent' },
  };

  const textColor = variant === 'primary' ? '#fff' : colors.text;

  return (
    <TouchableOpacity
      accessibilityRole="button"
      activeOpacity={0.85}
      onPress={onPress}
      disabled={disabled || loading}
      style={[base, variants[variant], style]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={{ color: textColor, fontSize: sizes[size].font, fontWeight: '600' }}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

export default Button;

