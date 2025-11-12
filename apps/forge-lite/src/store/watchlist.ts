import { create } from 'zustand';
import { WatchlistItem } from '../types';

export type WatchlistStore = {
  watchlist: WatchlistItem[];
  addSymbol: (symbol: string) => void;
  removeSymbol: (symbol: string) => void;
  setWatchlist: (items: WatchlistItem[]) => void;
};

const defaultList: WatchlistItem[] = [
  { symbol: 'SPY' },
  { symbol: 'AAPL' },
  { symbol: 'TSLA' },
];

export const useWatchlistStore = create<WatchlistStore>()((set) => ({
  watchlist: defaultList,
  addSymbol: (symbol: string) =>
    set((state) =>
      state.watchlist.some((w) => w.symbol === symbol)
        ? state
        : { watchlist: [...state.watchlist, { symbol }] }
    ),
  removeSymbol: (symbol: string) =>
    set((state) => ({ watchlist: state.watchlist.filter((w) => w.symbol !== symbol) })),
  setWatchlist: (items: WatchlistItem[]) => set({ watchlist: items }),
}));
