import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_COOKIE_NAMES = ['goblin_auth', 'session_token', 'auth_token'];
const ADMIN_COOKIE_NAME = 'goblin_admin';

const isPublicFile = (pathname: string): boolean => /\.[^/]+$/.test(pathname);

const isGuestOnlyRoute = (pathname: string): boolean =>
  pathname === '/login' || pathname === '/register';

const isAuthRoute = (pathname: string): boolean =>
  pathname === '/chat' || pathname === '/account' || pathname === '/search';

const isSandboxRoute = (pathname: string): boolean => pathname === '/sandbox';

const isAdminRoute = (pathname: string): boolean => pathname === '/admin' || pathname.startsWith('/admin/');

const hasAuthCookie = (req: NextRequest): boolean =>
  AUTH_COOKIE_NAMES.some(name => {
    const value = req.cookies.get(name)?.value;
    return Boolean(value);
  });

const hasAdminCookie = (req: NextRequest): boolean =>
  req.cookies.get(ADMIN_COOKIE_NAME)?.value === '1';

const redirectToLogin = (req: NextRequest): NextResponse => {
  const url = req.nextUrl.clone();
  url.pathname = '/login';
  url.searchParams.set('from', `${req.nextUrl.pathname}${req.nextUrl.search}`);
  return NextResponse.redirect(url);
};

const redirectToHome = (req: NextRequest): NextResponse => {
  const url = req.nextUrl.clone();
  url.pathname = '/';
  url.search = '';
  return NextResponse.redirect(url);
};

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/auth') ||
    pathname.startsWith('/v1') ||
    pathname === '/favicon.ico' ||
    pathname === '/robots.txt' ||
    pathname === '/sitemap.xml' ||
    isPublicFile(pathname)
  ) {
    return NextResponse.next();
  }

  const isAuthenticated = hasAuthCookie(req);
  const isAdmin = hasAdminCookie(req);
  const guestParam = req.nextUrl.searchParams.get('guest');
  const isGuestSandbox =
    isSandboxRoute(pathname) && (guestParam === '1' || guestParam === 'true');

  if (isGuestOnlyRoute(pathname) && isAuthenticated) {
    return redirectToHome(req);
  }

  if (isAdminRoute(pathname)) {
    if (!isAuthenticated) return redirectToLogin(req);
    if (!isAdmin) return redirectToHome(req);
    return NextResponse.next();
  }

  if (isSandboxRoute(pathname) && !isAuthenticated && !isGuestSandbox) {
    return redirectToLogin(req);
  }

  if (isAuthRoute(pathname) && !isAuthenticated) {
    return redirectToLogin(req);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)'],
};
