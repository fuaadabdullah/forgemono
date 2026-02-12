import { isAdminUser, type AccessUser } from './access';

const AUTH_FLAG_COOKIE = 'goblin_auth';
const ADMIN_COOKIE = 'goblin_admin';
const LEGACY_TOKEN_COOKIES = ['session_token', 'auth_token'];
const DEFAULT_MAX_AGE_SECONDS = 60 * 60 * 24 * 30;

const cookieBase = (maxAge?: number): string => {
  const parts = ['Path=/', 'SameSite=Lax'];
  if (typeof maxAge === 'number' && Number.isFinite(maxAge)) {
    parts.push(`Max-Age=${Math.max(0, Math.floor(maxAge))}`);
  }
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    parts.push('Secure');
  }
  return parts.join('; ');
};

const setCookie = (name: string, value: string, maxAge?: number): void => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=${encodeURIComponent(value)}; ${cookieBase(maxAge)}`;
};

const clearCookie = (name: string): void => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; Path=/; Max-Age=0`;
};

interface PersistAuthInput {
  token?: string | null;
  user?: AccessUser | null;
  expiresIn?: number | null;
}

export const persistAuthSession = ({ token, user, expiresIn }: PersistAuthInput): void => {
  if (typeof window === 'undefined') return;

  if (token) {
    localStorage.setItem('auth_token', token);
  }

  if (user) {
    localStorage.setItem('user_data', JSON.stringify(user));
  }

  const resolvedToken = token ?? localStorage.getItem('auth_token');
  const shouldMarkAuth = Boolean(resolvedToken || user);
  const maxAge =
    typeof expiresIn === 'number' && Number.isFinite(expiresIn)
      ? Math.max(0, expiresIn)
      : shouldMarkAuth
        ? DEFAULT_MAX_AGE_SECONDS
        : undefined;

  if (shouldMarkAuth) {
    setCookie(AUTH_FLAG_COOKIE, '1', maxAge);
  }

  if (user) {
    setCookie(ADMIN_COOKIE, isAdminUser(user) ? '1' : '0', maxAge);
  }
};

export const clearAuthSession = (): void => {
  if (typeof window === 'undefined') return;

  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_data');

  clearCookie(AUTH_FLAG_COOKIE);
  clearCookie(ADMIN_COOKIE);
  LEGACY_TOKEN_COOKIES.forEach(clearCookie);
};
