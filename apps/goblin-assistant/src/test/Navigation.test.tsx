import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { ContrastModeProvider } from '../hooks/useContrastMode';

describe('Navigation', () => {
  it('renders navigation with core links', () => {
    const { getByText } = render(
      <ContrastModeProvider>
        <BrowserRouter>
          <Navigation showLogout={false} />
        </BrowserRouter>
      </ContrastModeProvider>
    );

    // Check for main navigation items
    expect(getByText('Goblin Assistant')).toBeInTheDocument();
    expect(getByText('Dashboard')).toBeInTheDocument();
    expect(getByText('Chat')).toBeInTheDocument();
    expect(getByText('Search')).toBeInTheDocument();
    expect(getByText('Providers')).toBeInTheDocument();
    expect(getByText('Sandbox')).toBeInTheDocument();
    expect(getByText('Logs')).toBeInTheDocument();
    expect(getByText('Settings')).toBeInTheDocument();
  });

  it('displays logout button when showLogout is true', () => {
    const { getByText } = render(
      <ContrastModeProvider>
        <BrowserRouter>
          <Navigation showLogout={true} />
        </BrowserRouter>
      </ContrastModeProvider>
    );

    expect(getByText('Logout')).toBeInTheDocument();
  });

  it('does not display logout button when showLogout is false', () => {
    const { queryByText } = render(
      <ContrastModeProvider>
        <BrowserRouter>
          <Navigation showLogout={false} />
        </BrowserRouter>
      </ContrastModeProvider>
    );

    expect(queryByText('Logout')).not.toBeInTheDocument();
  });
});
