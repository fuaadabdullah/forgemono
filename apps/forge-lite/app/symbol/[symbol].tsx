import React, { useEffect, useMemo, useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useTheme } from '../../src/theme';
import { Header } from '../../src/ui/Header';
import { Card } from '../../src/ui/Card';
import { ChartContainer } from '../../src/ui/ChartContainer';
import PriceChip from '../../src/ui/PriceChip';
import { Button } from '../../src/ui/Button';
import { marketDataService } from '../../src/services/marketData';
import type { Candle } from '../../src/types';
import { useQuery } from '@tanstack/react-query';
import { CartesianChart, Line } from 'victory-native';
import { Muted } from '../../src/ui/Text';
import { useWatchlistStore } from '../../src/store/watchlist';

export default function SymbolDetail() {
  const { colors, spacing } = useTheme();
  const { symbol = '' } = useLocalSearchParams<{ symbol?: string }>();
  const router = useRouter();
  const { watchlist, addSymbol } = useWatchlistStore();
  const [timeframe, setTimeframe] = useState<'1D'|'1W'|'1M'>('1D');
  const [price, setPrice] = useState(0);
  const [change, setChange] = useState(0);
  const [changePercent, setChangePercent] = useState(0);
  const [chartWidth, setChartWidth] = useState(0);
  const inWatchlist = watchlist.some(item => item.symbol === symbol);

  const { data: candles = [], isPending } = useQuery({
    queryKey: ['ohlc', symbol, timeframe],
    queryFn: () => marketDataService.getOHLC(String(symbol), timeframe),
    staleTime: 60_000,
    enabled: Boolean(symbol),
  });

  useEffect(() => {
    if (!candles.length) return;
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2] ?? last;
    setPrice(last.c);
    const delta = last.c - prev.c;
    setChange(delta);
    setChangePercent(prev.c ? (delta / prev.c) * 100 : 0);
  }, [candles]);

  const chartData: Array<{ date: number; close: number; open: number; high: number; low: number }> = useMemo(() => candles.map((c: Candle) => ({
    date: new Date(c.t).getTime(),
    close: c.c,
    open: c.o,
    high: c.h,
    low: c.l
  })), [candles]);

  const formatTime = (date: Date) =>
    timeframe === '1D'
      ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : date.toLocaleDateString([], { month: 'short', day: 'numeric' });

  const sessionStats = [
    { label: 'Prev Close', value: candles.length ? `$${candles[Math.max(0, candles.length - 2)].c.toFixed(2)}` : '--' },
    { label: 'Open', value: candles.length ? `$${candles[candles.length - 1].o.toFixed(2)}` : '--' },
    { label: 'High', value: candles.length ? `$${Math.max(...candles.map(c => c.h)).toFixed(2)}` : '--' },
    { label: 'Low', value: candles.length ? `$${Math.min(...candles.map(c => c.l)).toFixed(2)}` : '--' },
    { label: 'Vol', value: candles.length ? `${Math.round(candles[candles.length - 1].v).toLocaleString()}` : '--' },
    { label: 'Change', value: `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)` },
  ];

  const handlePlanTrade = () => {
    router.push(`/(tabs)/plan?entry=${price.toFixed(2)}&direction=${change >= 0 ? 'long' : 'short'}&symbol=${symbol}`);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title={String(symbol).toUpperCase()} right={<PriceChip price={price} change={change} changePercent={changePercent} />} />

      <Card style={[styles.heroCard, { marginHorizontal: 16, marginBottom: spacing.lg }]}>
        <Text style={[styles.heroLabel, { color: colors.muted }]}>Last Price</Text>
        <Text style={[styles.heroPrice, { color: colors.text }]}>${price.toFixed(2)}</Text>
        <Text style={[styles.heroDelta, { color: change >= 0 ? colors.positive : colors.negative }]}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
        </Text>
        {candles.length ? (
          <View style={styles.rangeBar}>
            <Text style={[styles.rangeLabel, { color: colors.muted }]}>Low ${Math.min(...candles.map(c => c.l)).toFixed(2)}</Text>
            <View style={styles.rangeTrack}>
              <View
                style={[styles.rangeFill, {
                  backgroundColor: change >= 0 ? colors.positive : colors.negative,
                  left: `${((price - Math.min(...candles.map(c => c.l))) / (Math.max(...candles.map(c => c.h)) - Math.min(...candles.map(c => c.l)) || 1)) * 100}%`,
                }]}
              />
            </View>
            <Text style={[styles.rangeLabel, { color: colors.muted }]}>High ${Math.max(...candles.map(c => c.h)).toFixed(2)}</Text>
          </View>
        ) : null}
      </Card>

      <View style={styles.section}>
        <View style={styles.timeframes}>
          {(['1D','1W','1M'] as const).map(tf => (
            <Button
              key={tf}
              title={tf}
              size="sm"
              variant={timeframe === tf ? 'primary' : 'secondary'}
              onPress={() => setTimeframe(tf)}
              style={{ marginRight: 8 }}
            />
          ))}
        </View>
        <ChartContainer height={300}>
          <View style={{ flex: 1 }} onLayout={(e) => setChartWidth(e.nativeEvent.layout.width)}>
            {chartData.length && chartWidth ? (
              <CartesianChart
                data={chartData}
                xKey="date"
                yKeys={["close"] as const}
                padding={{ top: 20, bottom: 40, left: 60, right: 24 }}
                domainPadding={12}
              >
                {({ points, chartBounds, canvasSize }) => (
                  <>
                    <Line
                      points={points.close}
                      color={colors.tint}
                      strokeWidth={1}
                      curveType="monotoneX"
                    />
                  </>
                )}
              </CartesianChart>
            ) : (
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                {isPending ? <Muted>Loading chart…</Muted> : <Muted>No market data</Muted>}
              </View>
            )}
          </View>
        </ChartContainer>
      </View>

      <Card style={styles.section}>
        <Text style={[styles.h2, { color: colors.text }]}>Session stats</Text>
        <View style={styles.grid}>
          {sessionStats.map(stat => (
            <View key={stat.label} style={styles.gridItem}>
              <Text style={{ color: colors.muted }}>{stat.label}</Text>
              <Text style={{ color: colors.text }}>{stat.value}</Text>
            </View>
          ))}
        </View>
      </Card>

      <Card style={styles.section}>
        <Text style={[styles.h2, { color: colors.text }]}>Actions</Text>
        <View style={styles.actionsRow}>
          <Button
            title={inWatchlist ? 'In Watchlist' : 'Add to Watchlist'}
            variant={inWatchlist ? 'secondary' : 'primary'}
            onPress={() => { if (!inWatchlist) addSymbol(String(symbol)); }}
            disabled={inWatchlist}
            style={{ flex: 1 }}
          />
          <Button title="Plan Trade" variant="ghost" onPress={handlePlanTrade} style={{ flex: 1 }} />
        </View>
        <Muted style={{ marginTop: 8 }}>Educational only · No execution. Use planner before journaling.</Muted>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  section: { marginHorizontal: 16, marginBottom: 16 },
  heroCard: {
    padding: 20,
    borderRadius: 16,
  },
  heroLabel: { fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 },
  heroPrice: { fontSize: 42, fontWeight: '700' },
  heroDelta: { fontSize: 16, fontWeight: '600', marginBottom: 12 },
  rangeBar: { marginTop: 12 },
  rangeTrack: { height: 6, backgroundColor: '#1f2535', borderRadius: 999, marginVertical: 8, position: 'relative' },
  rangeFill: { width: 2, height: 14, position: 'absolute', top: -4, borderRadius: 999 },
  rangeLabel: { fontSize: 12 },
  h2: { fontSize: 18, fontWeight: '600', marginBottom: 12 },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    columnGap: 16,
  },
  gridItem: { width: '48%', marginBottom: 12 },
  timeframes: { flexDirection: 'row', marginBottom: 8 },
  actionsRow: { flexDirection: 'row', gap: 12, marginTop: 8 },
});
