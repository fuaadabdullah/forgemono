import React from 'react';
import { StyleSheet, Text, View, ViewStyle } from 'react-native';
import { useTokens } from './tokens';

type Props = {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  style?: ViewStyle;
};

export function Header({ title, subtitle, right, style }: Props) {
  const { colors, typography, spacing } = useTokens();
  return (
    <View style={[styles.container, style]}>      
      <View style={styles.left}>
        <Text style={[typography.title as any, { color: colors.text }]}>{title}</Text>
        {!!subtitle && (
          <Text style={[typography.subtitle as any, { color: colors.muted, marginTop: spacing.sm }]}>{subtitle}</Text>
        )}
      </View>
      {right ? <View style={styles.right}>{right}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  left: { flex: 1 },
  right: { marginLeft: 12 },
});

export default Header;

