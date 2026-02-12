import type { ReactNode } from 'react';
import Navigation from '../components/Navigation';

interface AdminLayoutProps {
  children: ReactNode;
  fullWidth?: boolean;
}

export default function AdminLayout({ children, fullWidth = false }: AdminLayoutProps) {
  return (
    <div className="min-h-screen bg-bg">
      <Navigation showLogout={true} variant="admin" />
      <div className={fullWidth ? 'px-6' : 'max-w-7xl mx-auto p-6'}>{children}</div>
    </div>
  );
}
