import React, { PropsWithChildren } from 'react';
import { Text as RNText, TextProps } from 'react-native';
import { useTokens } from './tokens';

export function Title(props: TextProps) {
  const { colors, typography } = useTokens();
  return <RNText {...props} style={[typography.title as any, { color: colors.text }, props.style]} />;
}

export function Subtitle(props: TextProps) {
  const { colors, typography } = useTokens();
  return <RNText {...props} style={[typography.subtitle as any, { color: colors.muted }, props.style]} />;
}

export function Body(props: TextProps) {
  const { colors, typography } = useTokens();
  return <RNText {...props} style={[typography.body as any, { color: colors.text }, props.style]} />;
}

export function Muted(props: TextProps) {
  const { colors, typography } = useTokens();
  return <RNText {...props} style={[typography.body as any, { color: colors.muted }, props.style]} />;
}

export default { Title, Subtitle, Body, Muted };

