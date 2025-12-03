import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect, lazy, Suspense } from 'react';
import EnhancedDashboard from './components/EnhancedDashboard';
import Navigation from './components/Navigation';
import LoginPage from './pages/LoginPage';
import { apiClient } from './api/client-axios';
import { useAuthStore } from './store/authStore';
import { ContrastModeProvider } from './hooks/useContrastMode';
import { initializeTheme } from './theme/theme';
import { applyThemePreset, enableHighContrast, getHighContrastPreference } from './theme/theme';
import { useKeyboardShortcuts, SHORTCUTS } from './hooks/useKeyboardShortcuts';
import './theme/index.css';

// Code-split all secondary/heavier routes to shrink initial bundle (index.*.js)
// Keep core shell (Dashboard, Navigation, Login) eagerly loaded for fast first paint.
const SandboxPage = lazy(() => import('./pages/SandboxPage'));
const LogsPage = lazy(() => import('./pages/LogsPage'));
const Chat = lazy(() => import('./pages/ChatPage'));
const Search = lazy(() => import('./pages/SearchPage'));
const Settings = lazy(() => import('./pages/SettingsPage'));
const EnhancedProvidersPage = lazy(() => import('./pages/EnhancedProvidersPage'));
// Components (not pages) that are only needed on specific routes
const TaskExecution = lazy(() => import('./components/TaskExecution'));
const Orchestration = lazy(() => import('./components/Orchestration'));

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const { token, clearAuth } = useAuthStore();
  const isAuthenticated = !!token;
  const location = useLocation();

  // Initialize theme system on mount
  useEffect(() => {
    initializeTheme();
  }, []);

  // Setup keyboard shortcuts for theme control
  useKeyboardShortcuts([
    {
      ...SHORTCUTS.TOGGLE_HIGH_CONTRAST,
      callback: () => {
        const current = getHighContrastPreference();
        enableHighContrast(!current);
      }
    },
    {
      ...SHORTCUTS.THEME_DEFAULT,
      callback: () => applyThemePreset('default')
    },
    {
      ...SHORTCUTS.THEME_NOCTURNE,
      callback: () => applyThemePreset('nocturne')
    },
    {
      ...SHORTCUTS.THEME_EMBER,
      callback: () => applyThemePreset('ember')
    }
  ]);

  // Health check after mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiClient.getHealth();
      } catch (error) {
        console.error('Failed to connect to backend:', error);
      } finally {
        setIsLoading(false);
      }
    };
    checkHealth();
  }, []);

  // Move keyboard focus to main content on route changes for better accessibility
  useEffect(() => {
    const main = document.getElementById('main-content');
    if (main) {
      main.focus();
    }
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await apiClient.logout();
    } catch (e) {
      console.warn('Logout request failed, clearing token locally');
    }
    clearAuth();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg text-text flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-sm tracking-wide text-muted">Initializing environment...</p>
        </div>
      </div>
    );
  }

  return (
    <ContrastModeProvider>
      <Router>
          {/* Visually hidden live region to announce page title changes */}
          <div aria-live="polite" aria-atomic="true" className="sr-only" id="aria-page-title">
            {typeof document !== 'undefined' ? document.title : 'Goblin Assistant'}
          </div>
          {!isAuthenticated ? (
            <main>
              <LoginPage />
            </main>
          ) : (
        <div className="min-h-screen bg-bg">
          <Navigation onLogout={handleLogout} showLogout={true} />
          {/* Skip to content link for keyboard users */}
          <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 bg-surface text-text px-3 py-2 rounded-md">Skip to main content</a>
          <div className="max-w-[1200px] mx-auto p-6">
            <main role="main" id="main-content" tabIndex={-1}>
              <Suspense fallback={
                <div className="min-h-screen flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-sm text-muted">Loading page...</p>
                  </div>
                </div>
              }>
                <Routes>
                  {/* Root dashboard */}
                  <Route path="/" element={<EnhancedDashboard />} />
                  {/* Legacy alias if deep links existed */}
                  <Route path="/dashboard" element={<EnhancedDashboard />} />
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/search" element={<Search />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/providers" element={<EnhancedProvidersPage />} />
                  {/* Code-split routes for better initial bundle size */}
                  <Route path="/sandbox" element={<SandboxPage />} />
                  <Route path="/logs" element={<LogsPage />} />
                  <Route path="/execute" element={<TaskExecution />} />
                  <Route path="/orchestrate" element={<Orchestration />} />
                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </main>
          </div>
        </div>
          )}
      </Router>
    </ContrastModeProvider>
  );
}

export default App;
