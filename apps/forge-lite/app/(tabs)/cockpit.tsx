import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Link, useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { Button } from '../../src/ui/Button';
import { Muted } from '../../src/ui/Text';
import { useTheme } from '../../src/theme';
import { Header } from '../../src/ui/Header';
import { Watchlist } from '../../src/components/Watchlist';
import ChartDemo from '../../src/components/ChartDemo';
import { Card } from '../../src/ui/Card';
import { GlassCard } from '../../src/ui/GlassCard';
import { useWatchlistStore } from '../../src/store/watchlist';

const privacyUrl = process.env.EXPO_PUBLIC_PRIVACY_URL ?? 'https://example.com/privacy';
const termsUrl = process.env.EXPO_PUBLIC_TERMS_URL ?? 'https://example.com/terms';

export default function Cockpit() {
  const { colors } = useTheme();
  const router = useRouter();
  const { watchlist, addSymbol, removeSymbol } = useWatchlistStore();
  const [timeframe, setTimeframe] = useState<'1D'|'1W'|'1M'>('1D');
  const chartSymbol = useMemo(() => watchlist[0]?.symbol || 'SPY', [watchlist]);

  const handleAddSymbol = (symbol: string) => addSymbol(symbol);

  const handleRemoveSymbol = (symbol: string) => removeSymbol(symbol);
  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <Header title="Trading Cockpit" subtitle="Watchlist • Risk Management • Performance" />

      {/* Watchlist */}
      <Card padded={false} variant="surface" style={{ marginHorizontal: 16, marginBottom: 12 }}>
        <Watchlist
          watchlist={watchlist}
          onAddSymbol={handleAddSymbol}
          onRemoveSymbol={handleRemoveSymbol}
        />
      </Card>

      {/* Market chart + timeframe chips */}
      <Card style={{ marginHorizontal: 16, marginBottom: 12 }}>
        <View style={{ flexDirection: 'row', marginBottom: 8 }}>
          {(['1D','1W','1M'] as const).map(tf => (
            <Button key={tf} title={tf} size="sm" variant={timeframe===tf?'primary':'secondary'} onPress={() => setTimeframe(tf)} style={{ marginRight: 8 }} />
          ))}
        </View>
        <ChartDemo symbol={chartSymbol} timeframe={timeframe} />
      </Card>

      {/* Primary CTA */}
      <View style={styles.ctaContainer}>
        <Muted style={{ marginBottom: 6 }}>Educational only · No execution</Muted>
        <Button
          title="Plan Trade"
          variant="ghost"
          onPress={async () => { try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}; router.push('/(tabs)/plan'); }}
        />
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Link href="/about" style={[styles.link, { color: colors.tint }]}>About</Link>
        <Text style={{ color: colors.muted }}> • </Text>
        <Link href={privacyUrl} style={[styles.link, { color: colors.tint }]}>Privacy</Link>
        <Text style={{ color: colors.muted }}> • </Text>
        <Link href={termsUrl} style={[styles.link, { color: colors.tint }]}>Terms</Link>
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
