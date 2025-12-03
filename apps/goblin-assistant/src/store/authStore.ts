import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  email: string;
  id?: string;
}

interface AuthState {
  // State
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  // eslint-disable-next-line no-unused-vars
  setAuth: (token: string, user?: User) => void;
  clearAuth: () => void;
  // eslint-disable-next-line no-unused-vars
  setUser: (user: User) => void;
}

/**
 * Zustand store for authentication state
 * Persists token to localStorage automatically
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      token: null,
      user: null,
      isAuthenticated: false,

      // Actions
      setAuth: (token: string, user?: User) => {
        set({
          token,
          user: user || null,
          isAuthenticated: true,
        });
      },

      clearAuth: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        });
      },

      setUser: (user: User) => {
        set({ user });
      },
    }),
    {
      name: 'goblin-auth-storage', // localStorage key
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);
