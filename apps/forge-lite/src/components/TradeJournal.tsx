import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { useTheme } from '../theme';
import { Trade } from '../types';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Muted } from '../ui/Text';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { db } from '../services/supabase';
import { Database } from '../services/supabase';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Mock data for demonstration
const mockTrades: Trade[] = [
  {
    id: '1',
    symbol: 'AAPL',
    direction: 'long',
    entry: 150.25,
    stop: 145.00,
    target: 160.00,
    riskAmount: 250.00,
    positionSize: 250,
    status: 'closed',
    pnl: 487.50,
    rMultiple: 2.35,
    notes: 'Breakout above resistance',
    setup: 'Momentum',
    createdAt: new Date('2024-11-01'),
    closedAt: new Date('2024-11-03'),
  },
  {
    id: '2',
    symbol: 'TSLA',
    direction: 'short',
    entry: 220.50,
    stop: 235.00,
    target: 200.00,
    riskAmount: 200.00,
    positionSize: 200,
    status: 'active',
    notes: 'Overbought on daily chart',
    setup: 'Reversal',
    createdAt: new Date('2024-11-05'),
  },
  {
    id: '3',
    symbol: 'SPY',
    direction: 'long',
    entry: 420.75,
    stop: 415.00,
    riskAmount: 150.00,
    positionSize: 150,
    status: 'planned',
    notes: 'Dip buying opportunity',
    setup: 'Support',
    createdAt: new Date('2024-11-07'),
  },
];

const mapDbRowToTrade = (row: Database['public']['Tables']['trades']['Row']): Trade => ({
  id: row.id,
  symbol: row.ticker,
  direction: row.side,
  entry: row.entry_price,
  stop: row.stop_loss ?? 0,
  target: row.target_price ?? undefined,
  riskAmount: row.risk_percent ? (row.risk_percent / 100) * (row.entry_price * (row.quantity || 0)) : 0,
  positionSize: row.quantity || 0,
  status: (row.status || 'planned') as Trade['status'],
  pnl: row.pnl_dollars ?? undefined,
  rMultiple: row.pnl_r_multiple ?? undefined,
  notes: row.notes ?? undefined,
  setup: row.tags?.[0] ?? undefined,
  createdAt: new Date(row.created_at),
  closedAt: row.exit_date ? new Date(row.exit_date) : undefined,
});

interface TradeJournalProps {
  trades?: Trade[];
}

export function TradeJournal({ trades = mockTrades }: TradeJournalProps) {
  const { colors } = useTheme();
  const router = useRouter();
  const [filterStatus, setFilterStatus] = useState<Trade['status'] | 'ALL'>('ALL');
  const [filterSymbol, setFilterSymbol] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'pnl' | 'symbol'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const queryClient = useQueryClient();

  const tradesQuery = useQuery({
    queryKey: ['trades'],
    queryFn: async () => {
      const rows = await db.trades.getAll();
      return rows.map(mapDbRowToTrade);
    },
    initialData: trades,
  });

  const entries: Trade[] = tradesQuery.data ?? [];
  const loading = tradesQuery.isPending && entries.length === 0;
  const refreshing = tradesQuery.isRefetching;

  const startMutation = useMutation({
    mutationFn: (id: string) => db.trades.update(id, { status: 'active', entry_date: new Date().toISOString() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trades'] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => db.trades.update(id, { status: 'closed', exit_date: new Date().toISOString() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trades'] }),
  });

  const filteredAndSortedTrades = useMemo(() => {
    let filtered = entries.filter(trade => {
      const matchesStatus = filterStatus === 'ALL' || trade.status === filterStatus;
      const matchesSymbol = !filterSymbol ||
        trade.symbol.toLowerCase().includes(filterSymbol.toLowerCase());
      return matchesStatus && matchesSymbol;
    });

    filtered.sort((a, b) => {
      let aValue: string | number, bValue: string | number;

      switch (sortBy) {
        case 'date':
          aValue = a.createdAt.getTime();
          bValue = b.createdAt.getTime();
          break;
        case 'pnl':
          aValue = a.pnl || 0;
          bValue = b.pnl || 0;
          break;
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [entries, filterStatus, filterSymbol, sortBy, sortOrder]);

  const handleStart = async (id: string) => {
    try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    startMutation.mutate(id);
  };
  const handleClose = async (id: string) => {
    try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    closeMutation.mutate(id);
  };

  const getStatusColor = (status: Trade['status']) => {
    switch (status) {
      case 'planned': return '#FFD60A';
      case 'active': return '#30D158';
      case 'closed': return '#6b7280';
      default: return colors.muted;
    }
  };

  const getPnlColor = (pnl?: number) => {
    if (!pnl) return colors.muted;
    return pnl >= 0 ? '#30D158' : '#FF3B30';
  };

  const renderTradeItem = ({ item }: { item: Trade }) => (
    <Card style={styles.tradeItem}>
      <View style={styles.tradeHeader}>
        <View style={styles.symbolSection}>
          <Text style={[styles.symbol, { color: colors.text }]}>{item.symbol}</Text>
          <Text style={[styles.direction, {
            color: item.direction === 'long' ? '#10b981' : '#ef4444'
          }]}>
            {item.direction.toUpperCase()}
          </Text>
        </View>
        <View style={styles.statusSection}>
          <Text style={[styles.status, { backgroundColor: getStatusColor(item.status) }]}>
            {item.status}
          </Text>
        </View>
      </View>

      <View style={styles.tradeDetails}>
        <View style={styles.detailRow}>
          <Text style={[styles.detailLabel, { color: colors.muted }]}>Entry:</Text>
          <Text style={[styles.detailValue, { color: colors.text }]}>${item.entry.toFixed(2)}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={[styles.detailLabel, { color: colors.muted }]}>Stop:</Text>
          <Text style={[styles.detailValue, { color: colors.text }]}>${item.stop.toFixed(2)}</Text>
        </View>

        {item.target && (
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: colors.muted }]}>Target:</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>${item.target.toFixed(2)}</Text>
          </View>
        )}

        <View style={styles.detailRow}>
          <Text style={[styles.detailLabel, { color: colors.muted }]}>Size:</Text>
          <Text style={[styles.detailValue, { color: colors.text }]}>{item.positionSize} shares</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={[styles.detailLabel, { color: colors.muted }]}>Risk:</Text>
          <Text style={[styles.detailValue, { color: colors.text }]}>${item.riskAmount.toFixed(2)}</Text>
        </View>

        {item.pnl !== undefined && (
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: colors.muted }]}>P&L:</Text>
            <Text style={[styles.detailValue, { color: getPnlColor(item.pnl) }]}>
              ${item.pnl.toFixed(2)}
            </Text>
          </View>
        )}

        {item.rMultiple !== undefined && (
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: colors.muted }]}>R Multiple:</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>
              {item.rMultiple.toFixed(2)}R
            </Text>
          </View>
        )}
      </View>

      {item.notes && (
        <View style={styles.notesSection}>
          <Text style={[styles.notes, { color: colors.muted }]}>{item.notes}</Text>
        </View>
      )}

      <View style={styles.tradeFooter}>
        <Text style={[styles.date, { color: colors.muted }]}>
          {item.createdAt.toLocaleDateString()}
        </Text>
        {item.setup && (
          <Text style={[styles.setup, { color: colors.tint }]}>{item.setup}</Text>
        )}
      </View>
      {/* Actions */}
      <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
        <Button
          title="Edit"
          size="sm"
          variant="secondary"
          onPress={async () => {
            try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); } catch {}
            const q = new URLSearchParams({
              entry: String(item.entry ?? ''),
              stop: String(item.stop ?? ''),
              target: item.target ? String(item.target) : '',
              equity: '',
              riskPercent: '',
              direction: item.direction,
            }).toString();
            router.push(`/(tabs)/plan?${q}`);
          }}
        />
        {item.status !== 'closed' && (
          <Button
            title={item.status === 'planned' ? 'Start' : 'Close Trade'}
            size="sm"
            variant="ghost"
            onPress={() => (item.status === 'planned' ? handleStart(item.id) : handleClose(item.id))}
          />
        )}
      </View>
    </Card>
  );

  const SortButton = ({ title, field }: { title: string; field: typeof sortBy }) => (
    <Button
      title={`${title}${sortBy === field ? (sortOrder === 'asc' ? ' ↑' : ' ↓') : ''}`}
      variant="ghost"
      size="sm"
      onPress={() => {
        if (sortBy === field) {
          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
          setSortBy(field);
          setSortOrder('desc');
        }
      }}
      style={styles.sortButton}
    />
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Trade Journal</Text>
        <Text style={[styles.subtitle, { color: colors.muted }]}>
          Track your trading performance and learn from your decisions
        </Text>
      </View>

      {/* Filters */}
      <Card style={styles.filters}>
        <View style={styles.filterRow}>
          <TextInput
            style={[styles.searchInput, { color: colors.text, borderColor: colors.border }]}
            placeholder="Filter by symbol..."
            placeholderTextColor={colors.muted}
            value={filterSymbol}
            onChangeText={setFilterSymbol}
          />
        </View>

        <View style={styles.statusFilters}>
          {(['ALL', 'planned', 'active', 'closed'] as const).map(status => (
            <Button
              key={status}
              title={status}
              size="sm"
              variant={filterStatus === status ? 'primary' : 'secondary'}
              onPress={() => setFilterStatus(status)}
              style={styles.statusFilter}
            />
          ))}
        </View>

        <View style={styles.sortRow}>
          <Text style={[styles.sortLabel, { color: colors.muted }]}>Sort by:</Text>
          <SortButton title="Date" field="date" />
          <SortButton title="P&L" field="pnl" />
          <SortButton title="Symbol" field="symbol" />
        </View>
      </Card>

      {/* Trade List */}
      <FlatList
        data={filteredAndSortedTrades}
        keyExtractor={(item) => item.id}
        renderItem={renderTradeItem}
        style={styles.list}
        showsVerticalScrollIndicator={false}
        refreshing={refreshing}
        onRefresh={() => tradesQuery.refetch()}
        ListEmptyComponent={
          loading ? null : (
            <Card style={styles.emptyContainer}>
              <Muted style={styles.emptyText}>No trades yet. Your plans and trades will appear here.</Muted>
              <View style={{ height: 8 }} />
              <Button
                title="Plan a Trade"
                onPress={async () => { try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}; router.push('/(tabs)/plan'); }}
              />
            </Card>
          )
        }
      />

      {/* Summary Stats */}
      <Card style={styles.summary}>
        <Text style={[styles.summaryTitle, { color: colors.text }]}>Summary</Text>
        <View style={styles.summaryStats}>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: colors.text }]}>
              {filteredAndSortedTrades.length}
            </Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Total Trades</Text>
          </View>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: '#30D158' }]}>
              {filteredAndSortedTrades.filter(t => t.pnl && t.pnl > 0).length}
            </Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Winners</Text>
          </View>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: '#FF3B30' }]}>
              {filteredAndSortedTrades.filter(t => t.pnl && t.pnl < 0).length}
            </Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Losers</Text>
          </View>
        </View>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    marginBottom: 16,
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
  filters: {
    margin: 16,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  filterRow: {
    marginBottom: 16,
  },
  searchInput: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  statusFilters: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 8,
  },
  statusFilter: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  statusFilterText: {
    fontSize: 14,
    fontWeight: '500',
  },
  sortRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  sortLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  sortButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  sortButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  list: {
    flex: 1,
    paddingHorizontal: 16,
  },
  tradeItem: {
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  symbolSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  symbol: {
    fontSize: 20,
    fontWeight: '700',
  },
  direction: {
    fontSize: 14,
    fontWeight: '600',
    paddingVertical: 2,
    paddingHorizontal: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  statusSection: {
    alignItems: 'flex-end',
  },
  status: {
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  tradeDetails: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  detailLabel: {
    fontSize: 14,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  notesSection: {
    marginBottom: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  notes: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  tradeFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  date: {
    fontSize: 12,
  },
  setup: {
    fontSize: 12,
    fontWeight: '500',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 64,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
  summary: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
  },
});
