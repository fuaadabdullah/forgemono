import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

// Get Supabase URL and anon key from environment variables
const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    'Missing Supabase environment variables. Using mock client for development. Please check your .env.local file and ensure EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY are set.'
  );
}

// Create Supabase client with AsyncStorage for persistence
// If credentials are missing, create a mock client that won't crash
export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        storage: AsyncStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false, // Disable for mobile apps
      },
    })
  : {
      // Mock client for development
      auth: {
        getUser: () => Promise.resolve({ data: { user: null }, error: null }),
        signInWithPassword: () => Promise.resolve({ data: {}, error: { message: 'Supabase not configured' } }),
        signOut: () => Promise.resolve({ error: null }),
      },
      from: () => ({
        select: () => ({ data: [], error: null }),
        insert: () => ({ data: null, error: { message: 'Supabase not configured' } }),
        update: () => ({ data: null, error: { message: 'Supabase not configured' } }),
        delete: () => ({ data: null, error: { message: 'Supabase not configured' } }),
      }),
    } as any; // eslint-disable-line @typescript-eslint/no-explicit-any

// Database types (generated from our schema)
export interface Database {
  public: {
    Tables: {
      trades: {
        Row: {
          id: string;
          user_id: string;
          ticker: string;
          status: 'planned' | 'active' | 'closed' | 'cancelled';
          side: 'long' | 'short';
          quantity: number;
          entry_price: number;
          stop_loss: number | null;
          target_price: number | null;
          exit_price: number | null;
          entry_date: string | null;
          exit_date: string | null;
          risk_percent: number;
          fees: number;
          pnl_dollars: number | null;
          pnl_r_multiple: number | null;
          notes: string | null;
          tags: string[];
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          ticker: string;
          status?: 'planned' | 'active' | 'closed' | 'cancelled';
          side: 'long' | 'short';
          quantity: number;
          entry_price: number;
          stop_loss?: number | null;
          target_price?: number | null;
          exit_price?: number | null;
          entry_date?: string | null;
          exit_date?: string | null;
          risk_percent?: number;
          fees?: number;
          pnl_dollars?: number | null;
          pnl_r_multiple?: number | null;
          notes?: string | null;
          tags?: string[];
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          ticker?: string;
          status?: 'planned' | 'active' | 'closed' | 'cancelled';
          side?: 'long' | 'short';
          quantity?: number;
          entry_price?: number;
          stop_loss?: number | null;
          target_price?: number | null;
          exit_price?: number | null;
          entry_date?: string | null;
          exit_date?: string | null;
          risk_percent?: number;
          fees?: number;
          pnl_dollars?: number | null;
          pnl_r_multiple?: number | null;
          notes?: string | null;
          tags?: string[];
          created_at?: string;
          updated_at?: string;
        };
      };
      watchlists: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          description: string | null;
          tickers: string[];
          is_default: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          description?: string | null;
          tickers?: string[];
          is_default?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          name?: string;
          description?: string | null;
          tickers?: string[];
          is_default?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
      journal_entries: {
        Row: {
          id: string;
          user_id: string;
          trade_id: string | null;
          date: string;
          market_conditions: string | null;
          entry_reasoning: string | null;
          exit_reasoning: string | null;
          emotional_state: string | null;
          mistakes: string | null;
          lessons_learned: string | null;
          improvements: string | null;
          sentiment: 'bullish' | 'bearish' | 'neutral' | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          trade_id?: string | null;
          date?: string;
          market_conditions?: string | null;
          entry_reasoning?: string | null;
          exit_reasoning?: string | null;
          emotional_state?: string | null;
          mistakes?: string | null;
          lessons_learned?: string | null;
          improvements?: string | null;
          sentiment?: 'bullish' | 'bearish' | 'neutral' | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          trade_id?: string | null;
          date?: string;
          market_conditions?: string | null;
          entry_reasoning?: string | null;
          exit_reasoning?: string | null;
          emotional_state?: string | null;
          mistakes?: string | null;
          lessons_learned?: string | null;
          improvements?: string | null;
          sentiment?: 'bullish' | 'bearish' | 'neutral' | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      user_preferences: {
        Row: {
          id: string;
          user_id: string;
          theme: string;
          default_risk_percent: number;
          notifications_enabled: boolean;
          data_export_frequency: string;
          privacy_analytics: boolean;
          privacy_crash_reports: boolean;
          privacy_marketing: boolean;
          trading_default_broker: string;
          trading_calculation_method: string;
          trading_journal_required: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          theme?: string;
          default_risk_percent?: number;
          notifications_enabled?: boolean;
          data_export_frequency?: string;
          privacy_analytics?: boolean;
          privacy_crash_reports?: boolean;
          privacy_marketing?: boolean;
          trading_default_broker?: string;
          trading_calculation_method?: string;
          trading_journal_required?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          theme?: string;
          default_risk_percent?: number;
          notifications_enabled?: boolean;
          data_export_frequency?: string;
          privacy_analytics?: boolean;
          privacy_crash_reports?: boolean;
          privacy_marketing?: boolean;
          trading_default_broker?: string;
          trading_calculation_method?: string;
          trading_journal_required?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
      feedback: {
        Row: {
          id: string;
          user_id: string | null;
          type: string;
          title: string | null;
          description: string | null;
          rating: number | null;
          platform: string | null;
          app_version: string | null;
          status: string;
          priority: string;
          votes: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id?: string | null;
          type: string;
          title?: string | null;
          description?: string | null;
          rating?: number | null;
          platform?: string | null;
          app_version?: string | null;
          status?: string;
          priority?: string;
          votes?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string | null;
          type?: string;
          title?: string | null;
          description?: string | null;
          rating?: number | null;
          platform?: string | null;
          app_version?: string | null;
          status?: string;
          priority?: string;
          votes?: number;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      trade_status: 'planned' | 'active' | 'closed' | 'cancelled';
      trade_side: 'long' | 'short';
      journal_sentiment: 'bullish' | 'bearish' | 'neutral';
    };
  };
}

// Auth helper functions
export const auth = {
  // Sign up with email and password
  signUp: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    if (error) throw error;
    return data;
  },

  // Sign in with email and password
  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    return data;
  },

  // Sign in with Apple (iOS only)
  signInWithApple: async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: 'forge-lite://auth/callback',
      },
    });
    if (error) throw error;
    return data;
  },

  // Sign out
  signOut: async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  // Get current user
  getCurrentUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error) throw error;
    return user;
  },

  // Get current session
  getCurrentSession: async () => {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    return session;
  },

  // Listen to auth state changes
  onAuthStateChange: (callback: (event: string, session: any) => void) => {
    return supabase.auth.onAuthStateChange(callback);
  },
};

// Database helper functions
export const db = {
  // Trades
  trades: {
    // Get all trades for current user
    getAll: async () => {
      const { data, error } = await supabase
        .from('trades')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    },

    // Get trade by ID
    getById: async (id: string) => {
      const { data, error } = await supabase
        .from('trades')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data;
    },

    // Create new trade
    create: async (trade: Database['public']['Tables']['trades']['Insert']) => {
      const { data, error } = await supabase
        .from('trades')
        .insert(trade)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Update trade
    update: async (id: string, updates: Database['public']['Tables']['trades']['Update']) => {
      const { data, error } = await supabase
        .from('trades')
        .update(updates)
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Delete trade
    delete: async (id: string) => {
      const { error } = await supabase
        .from('trades')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },
  },

  // Watchlists
  watchlists: {
    // Get all watchlists for current user
    getAll: async () => {
      const { data, error } = await supabase
        .from('watchlists')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    },

    // Get watchlist by ID
    getById: async (id: string) => {
      const { data, error } = await supabase
        .from('watchlists')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data;
    },

    // Create new watchlist
    create: async (watchlist: Database['public']['Tables']['watchlists']['Insert']) => {
      const { data, error } = await supabase
        .from('watchlists')
        .insert(watchlist)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Update watchlist
    update: async (id: string, updates: Database['public']['Tables']['watchlists']['Update']) => {
      const { data, error } = await supabase
        .from('watchlists')
        .update(updates)
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Delete watchlist
    delete: async (id: string) => {
      const { error } = await supabase
        .from('watchlists')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },
  },

  // Journal entries
  journal: {
    // Get all journal entries for current user
    getAll: async () => {
      const { data, error } = await supabase
        .from('journal_entries')
        .select('*')
        .order('date', { ascending: false });
      if (error) throw error;
      return data;
    },

    // Get journal entry by ID
    getById: async (id: string) => {
      const { data, error } = await supabase
        .from('journal_entries')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data;
    },

    // Create new journal entry
    create: async (entry: Database['public']['Tables']['journal_entries']['Insert']) => {
      const { data, error } = await supabase
        .from('journal_entries')
        .insert(entry)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Update journal entry
    update: async (id: string, updates: Database['public']['Tables']['journal_entries']['Update']) => {
      const { data, error } = await supabase
        .from('journal_entries')
        .update(updates)
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Delete journal entry
    delete: async (id: string) => {
      const { error } = await supabase
        .from('journal_entries')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },
  },

  // User preferences
  preferences: {
    // Get user preferences
    get: async () => {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .single();
      if (error) throw error;
      return data;
    },

    // Create or update preferences
    upsert: async (preferences: Database['public']['Tables']['user_preferences']['Insert']) => {
      const { data, error } = await supabase
        .from('user_preferences')
        .upsert(preferences)
        .select()
        .single();
      if (error) throw error;
      return data;
    },
  },

  // Feedback
  feedback: {
    // Submit feedback
    submit: async (feedback: Database['public']['Tables']['feedback']['Insert']) => {
      const { data, error } = await supabase
        .from('feedback')
        .insert(feedback)
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    // Get all feedback (admin only)
    getAll: async () => {
      const { data, error } = await supabase
        .from('feedback')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    },
  },
};

// Real-time subscriptions
export const realtime = {
  // Subscribe to trades changes
  subscribeToTrades: (callback: (payload: any) => void) => {
    return supabase
      .channel('trades')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'trades' }, callback)
      .subscribe();
  },

  // Subscribe to watchlists changes
  subscribeToWatchlists: (callback: (payload: any) => void) => {
    return supabase
      .channel('watchlists')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'watchlists' }, callback)
      .subscribe();
  },

  // Subscribe to journal changes
  subscribeToJournal: (callback: (payload: any) => void) => {
    return supabase
      .channel('journal')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'journal_entries' }, callback)
      .subscribe();
  },
};
