import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Link, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../src/theme';
import { Header } from '../../src/ui/Header';
import { RiskPlanner } from '../../src/components/RiskPlanner';
import { RiskCalcParams, RiskCalcResult } from '../../src/types';

export default function Plan() {
  const { colors } = useTheme();
  const params = useLocalSearchParams<{ entry?: string; stop?: string; equity?: string; riskPercent?: string; target?: string; direction?: string }>();

  const handleTradePlanned = (params: RiskCalcParams, result: RiskCalcResult) => {
    // TODO: Save to journal or navigate to journal with trade details
    console.log('Trade planned:', { params, result });
  };
  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <Header title="Trade Planning" subtitle="Calculate position size and risk" />

      {/* Risk Calculator */}
      <RiskPlanner
        onTradePlanned={handleTradePlanned}
        initial={{
          entry: params.entry || '',
          stop: params.stop || '',
          equity: params.equity || '',
          riskPercent: params.riskPercent || '',
          target: params.target || '',
          direction: (params.direction as any) || 'long',
        }}
      />

      {/* Primary CTA hint */}
      <View style={styles.ctaContainer}>
        <Text style={[styles.disclaimer, { color: colors.muted }]}>One action: Calculate Position</Text>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Link href="/(tabs)/cockpit" style={[styles.link, { color: colors.tint }]}>← Back to Cockpit</Link>
        <Text style={{ color: colors.muted }}> • </Text>
        <Link href="/(tabs)/journal" style={[styles.link, { color: colors.tint }]}>View Journal →</Link>
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
  disclaimer: {
    fontSize: 12,
  },
  link: {
    fontSize: 14,
    textDecorationLine: 'underline',
  },
});
