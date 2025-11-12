import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Link, useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../src/theme';
import { Header } from '../../src/ui/Header';
import { TradeJournal } from '../../src/components/TradeJournal';

export default function Journal() {
  const { colors } = useTheme();
  const router = useRouter();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <Header title="Trade Journal" subtitle="Track performance and learn from trades" />

      {/* Trade Journal */}
      <TradeJournal />

      {/* Primary CTA */}
      <View style={styles.ctaContainer}>
        <Text style={[styles.disclaimer, { color: colors.muted }]}>Educational only · No execution</Text>
        <Text
          onPress={async () => {
            try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
            router.push('/(tabs)/plan');
          }}
          style={[styles.ctaLink, { color: colors.tint }]}
        >
          New Journal Entry →
        </Text>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Link href="/(tabs)/plan" style={[styles.link, { color: colors.tint }]}>← Back to Plan</Link>
        <Text style={{ color: colors.muted }}> • </Text>
        <Link href="/(tabs)/cockpit" style={[styles.link, { color: colors.tint }]}>View Cockpit →</Link>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  testText: {
    fontSize: 18,
    marginBottom: 24,
    textAlign: 'center',
  },
  ctaButton: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  ctaText: {
    fontSize: 18,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
  },
  ctaContainer: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  ctaLink: {
    fontSize: 18,
    fontWeight: '600',
    textDecorationLine: 'none',
  },
  disclaimer: {
    fontSize: 12,
    marginBottom: 4,
  },
  link: {
    fontSize: 14,
    textDecorationLine: 'underline',
  },
});
