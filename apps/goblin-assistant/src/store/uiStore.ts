import { create } from 'zustand';
import { enableHighContrast, getHighContrastPreference } from '../theme/theme';

interface UIState {
  // Theme state
  highContrast: boolean;
  currentTheme: 'default' | 'nocturne' | 'ember';

  // UI state
  sidebarOpen: boolean;
  activeModal: string | null;
  notifications: NotificationItem[];

  // Actions
  setHighContrast: (enabled: boolean) => void;
  setTheme: (theme: 'default' | 'nocturne' | 'ember') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  addNotification: (notification: Omit<NotificationItem, 'id'>) => void;
  removeNotification: (id: string) => void;
}

interface NotificationItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

/**
 * Zustand store for UI state management
 * Handles theme preferences, modals, notifications, and other UI concerns
 */
export const useUIStore = create<UIState>((set, get) => ({
  // Initial state
  highContrast: getHighContrastPreference(),
  currentTheme: 'default',
  sidebarOpen: true,
  activeModal: null,
  notifications: [],

  // Theme actions
  setHighContrast: (enabled: boolean) => {
    enableHighContrast(enabled);
    set({ highContrast: enabled });
  },

  setTheme: (theme: 'default' | 'nocturne' | 'ember') => {
    set({ currentTheme: theme });
    // TODO: Implement theme switching logic
  },

  // Sidebar actions
  toggleSidebar: () => {
    set(state => ({ sidebarOpen: !state.sidebarOpen }));
  },

  setSidebarOpen: (open: boolean) => {
    set({ sidebarOpen: open });
  },

  // Modal actions
  openModal: (modalId: string) => {
    set({ activeModal: modalId });
  },

  closeModal: () => {
    set({ activeModal: null });
  },

  // Notification actions
  addNotification: notification => {
    const id = Date.now().toString();
    const newNotification: NotificationItem = {
      id,
      duration: 5000, // Default 5 seconds
      ...notification,
    };

    set(state => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remove after duration
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }
  },

  removeNotification: (id: string) => {
    set(state => ({
      notifications: state.notifications.filter(n => n.id !== id),
    }));
  },
}));
