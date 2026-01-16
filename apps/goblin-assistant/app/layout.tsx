"use client";

import React, { useEffect } from 'react';
import './globals.css'
import ErrorBoundary from '../src/components/ErrorBoundary'
import { ThemeProvider } from '../src/theme/components/ThemeProvider';
import { TooltipProvider } from '../src/components/ui/Tooltip';
import { initializeTheme } from '../src/theme/index';
import { I18nProvider } from '../src/i18n';

function AppProviders({ children }: { children: React.ReactNode }) {
  // Initialize theme system on mount
  useEffect(() => {
    initializeTheme();
  }, []);

  return (
    <I18nProvider>
      <TooltipProvider>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </TooltipProvider>
    </I18nProvider>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="bg-bg-primary">
      <body className="font-mono text-text-primary bg-bg-primary">
        <ErrorBoundary>
          <AppProviders>
            {children}
          </AppProviders>
        </ErrorBoundary>
      </body>
    </html>
  )
}
