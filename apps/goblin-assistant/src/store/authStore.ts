import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, UserSession } from '../types/api';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  sessions: UserSession[];
  isLoading: boolean;
  lastRefresh: Date | null;

  // Actions
  setAuth: (user: User) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
  setSessions: (sessions: UserSession[]) => void;
  addSession: (session: UserSession) => void;
  removeSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  updateLastRefresh: () => void;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

/**
 * Enhanced Zustand store for authentication state
 * Includes session management, role-based access, and persistence
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      sessions: [],
      isLoading: false,
      lastRefresh: null,

      // Actions
      setAuth: (user: User) => {
        set({
          user,
          isAuthenticated: true,
          lastRefresh: new Date(),
        });
      },

      clearAuth: () => {
        set({
          user: null,
          isAuthenticated: false,
          sessions: [],
          lastRefresh: null,
        });
      },

      setUser: (user: User) => {
        set({ user });
      },

      setSessions: (sessions: UserSession[]) => {
        set({ sessions });
      },

      addSession: (session: UserSession) => {
        set((state) => ({
          sessions: [...state.sessions, session],
        }));
      },

      removeSession: (sessionId: string) => {
        set((state) => ({
          sessions: state.sessions.filter(s => s.id !== sessionId),
        }));
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      updateLastRefresh: () => {
        set({ lastRefresh: new Date() });
      },

      hasRole: (role: string) => {
        const { user } = get();
        if (!user) return false;
        return user.role === role || (user.roles && user.roles.includes(role));
      },

      hasAnyRole: (roles: string[]) => {
        const { user } = get();
        if (!user) return false;
        return roles.some(role => user.role === role || (user.roles && user.roles.includes(role)));
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        sessions: state.sessions,
        lastRefresh: state.lastRefresh,
      }),
    }
  )
);
