import { Link, useLocation } from 'react-router-dom';
import HealthHeader from './HealthHeader';
import ContrastModeToggle from './ContrastModeToggle';
import Logo from './Logo';

interface NavigationProps {
  onLogout?: () => void;
  showLogout?: boolean;
}

const Navigation = ({ onLogout, showLogout = false }: NavigationProps) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '🏠' },
    { path: '/chat', label: 'Chat', icon: '💬' },
    { path: '/search', label: 'Search', icon: '🔍' },
    { path: '/providers', label: 'Providers', icon: '🧩' },
    { path: '/sandbox', label: 'Sandbox', icon: '🧪' },
    { path: '/logs', label: 'Logs', icon: '📜' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <nav className="bg-surface border-b border-border" role="navigation" aria-label="Primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-2">
              <Logo size="sm" variant="simple" animated />
              <span className="text-lg font-semibold text-primary">Goblin Assistant</span>
            </Link>
            {/* Inline health status pill */}
            <div className="hidden md:block">
              <HealthHeader compact />
            </div>
          </div>
          {/* Primary Nav */}
          <div className="flex items-center space-x-3">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 px-4 py-3 min-h-[44px] text-sm font-medium rounded-lg transition-colors outline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
                  location.pathname === item.path
                    ? 'text-text bg-surface-active shadow-glow-primary border border-border'
                    : 'text-muted hover:text-text hover:bg-surface-hover'
                }`}
                title={item.label}
                aria-current={location.pathname === item.path ? 'page' : undefined}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="leading-none">{item.label}</span>
              </Link>
            ))}
            {/* Utility area: contrast + logout */}
            <div className="flex items-center gap-2 pl-3 ml-3 border-l border-border">
              <div className="hidden sm:flex">
                <ContrastModeToggle />
              </div>
              {showLogout && (
                <button
                  onClick={onLogout}
                  className="flex items-center space-x-2 px-4 py-3 min-h-[44px] text-sm font-medium text-cta hover:bg-surface-hover rounded-lg transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                  title="Logout"
                  aria-label="Logout"
                >
                  <span className="text-xl">🚪</span>
                  <span className="leading-none">Logout</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
