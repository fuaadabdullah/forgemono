import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type ContrastMode = 'standard' | 'high';

interface ContrastModeContextValue {
  mode: ContrastMode;
  toggleMode: () => void;
  setMode: (newMode: ContrastMode) => void;
}

const ContrastModeContext = createContext<ContrastModeContextValue | undefined>(undefined);

const STORAGE_KEY = 'goblin-assistant-contrast-mode';

export function ContrastModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ContrastMode>(() => {
    // Initialize from localStorage or default to 'standard'
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'high' ? 'high' : 'standard';
  });

  useEffect(() => {
    // Apply contrast mode to document
    const root = document.documentElement;
    if (mode === 'high') {
      root.classList.add('goblinos-high-contrast');
    } else {
      root.classList.remove('goblinos-high-contrast');
    }

    // Persist to localStorage
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const setMode = (newMode: ContrastMode) => {
    setModeState(newMode);
  };

  const toggleMode = () => {
    setModeState((prev) => (prev === 'standard' ? 'high' : 'standard'));
  };

  return (
    <ContrastModeContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </ContrastModeContext.Provider>
  );
}

export function useContrastMode() {
  const context = useContext(ContrastModeContext);
  if (context === undefined) {
    throw new Error('useContrastMode must be used within a ContrastModeProvider');
  }
  return context;
}
