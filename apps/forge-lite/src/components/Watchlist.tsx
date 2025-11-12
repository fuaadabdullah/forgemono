import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { useTheme } from '../theme';
import { marketDataService } from '../services/marketData';
import { WatchlistItem } from '../types';
import * as Haptics from 'expo-haptics';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Muted } from '../ui/Text';
import { PriceChip } from '../ui/PriceChip';
import { GlassCard } from '../ui/GlassCard';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';

interface WatchlistProps {
  watchlist: WatchlistItem[];
  onAddSymbol: (symbol: string) => void;
  onRemoveSymbol: (symbol: string) => void;
}

export function Watchlist({ watchlist, onAddSymbol, onRemoveSymbol }: WatchlistProps) {
  const { colors } = useTheme();
  const router = useRouter();
  const [searchText, setSearchText] = useState('');

  const symbolList = useMemo(() => watchlist.map(item => item.symbol), [watchlist]);

  const quotesQuery = useQuery({
    queryKey: ['quotes', symbolList],
    queryFn: () => marketDataService.getQuotes(symbolList),
    enabled: symbolList.length > 0,
    refetchInterval: symbolList.length > 0 ? 25_000 : false,
    staleTime: 15_000,
  });

  const quotes = quotesQuery.data ?? {};

  const handleAddSymbol = async () => {
    const symbol = searchText.trim().toUpperCase();
    if (!symbol) return;

    if (watchlist.some(item => item.symbol === symbol)) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Already Added', `${symbol} is already in your watchlist.`);
      return;
    }

    try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); } catch {}
    onAddSymbol(symbol);
    setSearchText('');
  };

  const renderWatchlistItem = ({ item }: { item: WatchlistItem }) => {
    const quote = quotes[item.symbol];

    return (
      <Card padded style={styles.itemCard}>
        <TouchableOpacity style={styles.itemLeft} onPress={() => router.push(`/symbol/${item.symbol}`)}>
          <Text style={[styles.symbol, { color: colors.text }]}>{item.symbol}</Text>
          {quote && (
            <View style={styles.quoteContainer}>
              <PriceChip price={quote.price} change={quote.change} changePercent={quote.changePercent} />
            </View>
          )}
        </TouchableOpacity>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <Button
            title="View Detail"
            variant="secondary"
            size="sm"
            onPress={() => router.push(`/symbol/${item.symbol}`)}
          />
          <Button
            title="Remove"
            variant="ghost"
            size="sm"
            onPress={async () => { try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); } catch {}; onRemoveSymbol(item.symbol); }}
          />
        </View>
      </Card>
    );
  };

  const isInitialLoading = quotesQuery.isPending && symbolList.length > 0;
  const isRefetching = quotesQuery.isRefetching;

  return (
    <View style={styles.container}>
      {/* Search/Add Section */}
      {Platform.OS === 'ios' ? (
        <GlassCard style={styles.searchContainer}>
          <TextInput
            style={[styles.searchInput, { color: colors.text, borderColor: colors.border }]}
            placeholder="Add symbol (e.g., AAPL)"
            placeholderTextColor={colors.muted}
            value={searchText}
            onChangeText={setSearchText}
            autoCapitalize="characters"
            autoCorrect={false}
          />
          <Button title="Add" onPress={handleAddSymbol} size="md" style={{ marginLeft: 12 }} />
        </GlassCard>
      ) : (
        <Card style={styles.searchContainer}>
          <TextInput
            style={[styles.searchInput, { color: colors.text, borderColor: colors.border }]}
            placeholder="Add symbol (e.g., AAPL)"
            placeholderTextColor={colors.muted}
            value={searchText}
            onChangeText={setSearchText}
            autoCapitalize="characters"
            autoCorrect={false}
          />
          <Button title="Add" onPress={handleAddSymbol} size="md" style={{ marginLeft: 12 }} />
        </Card>
      )}

      {/* Watchlist */}
      {watchlist.length === 0 ? (
        <Card style={styles.emptyContainer}>
          <Muted style={styles.emptyText}>Your watchlist is empty. Add some symbols to get started.</Muted>
        </Card>
      ) : (
        <FlatList
          data={watchlist}
          keyExtractor={(item) => item.symbol}
          renderItem={renderWatchlistItem}
          style={styles.list}
          showsVerticalScrollIndicator={false}
          refreshing={isRefetching}
          onRefresh={() => quotesQuery.refetch()}
        />
      )}

      {isInitialLoading && (
        <Card style={styles.loadingContainer}>
          <Muted style={styles.loadingText}>Updating quotes…</Muted>
        </Card>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    margin: 16,
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderRadius: 8,
    marginRight: 12,
  },
  
  list: { flex: 1 },
  itemCard: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginHorizontal: 0,
    marginVertical: 4,
  },
  itemLeft: {
    flex: 1,
  },
  symbol: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  quoteContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  price: {
    fontSize: 16,
    fontWeight: '500',
    marginRight: 12,
  },
  change: {
    fontSize: 14,
  },
  removeButton: { paddingHorizontal: 8, paddingVertical: 6, borderRadius: 6 },
  
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
  loadingContainer: {
    padding: 16,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
  },
});
