// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Simple JWT verification without external dependencies
function verifyJWT(token: string, secret: string): { isValid: boolean; payload?: any } {
  try {
    // Basic JWT structure validation
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { isValid: false };
    }

    // Decode payload (base64url)
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));

    // Check expiration
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      return { isValid: false };
    }

    return { isValid: true, payload };
  } catch (error) {
    return { isValid: false };
  }
}

// Routes that require authentication
const protectedRoutes = [
  '/api/analytics',
  '/api/chat',
  '/settings',
];

// Routes that require admin role
const adminRoutes = [
  '/admin',
];

// Routes that are public (exact matches or prefixes)
const publicRoutes = [
  '/login',
  '/register',
  '/api/auth',
  '/',
  '/chat', // Allow direct access to chat for demo purposes
  '/dashboard', // Dashboard now redirects to chat
  '/api/health', // Health check should be public
];

// Routes that should never require auth (even for sub-paths)
const alwaysPublicRoutes = [
  '/_next/static',
  '/_next/image',
  '/favicon.ico',
  '/public',
  '/api/health',
];

function isAdminRoute(pathname: string): boolean {
  const normalizedPath = pathname.replace(/\/+/g, '/').replace(/\/$/, '');
  return adminRoutes.some(route => normalizedPath.startsWith(route));
}

function isProtectedRoute(pathname: string): boolean {
  // Normalize pathname to prevent bypass attempts
  const normalizedPath = pathname.replace(/\/+/g, '/').replace(/\/$/, '');

  // Always allow certain routes
  if (alwaysPublicRoutes.some(route => normalizedPath.startsWith(route))) {
    return false;
  }

  // Check exact public route matches
  if (publicRoutes.includes(normalizedPath)) {
    return false;
  }

  // Check public route prefixes
  if (publicRoutes.some(route => normalizedPath.startsWith(route + '/'))) {
    return false;
  }

  // Check if it's a protected route or admin route
  return protectedRoutes.some(route => normalizedPath.startsWith(route)) || isAdminRoute(normalizedPath);
}

// JWT Configuration - don't throw during initialization
const JWT_SECRET = process.env.JWT_SECRET_KEY;
const JWT_ALGORITHM = 'HS256';

function verifyToken(token: string): { isValid: boolean; payload?: any } {
  // If no JWT secret is configured, skip authentication
  if (!JWT_SECRET) {
    return { isValid: true }; // Allow all requests if no JWT secret is set
  }

  try {
    const validation = verifyJWT(token, JWT_SECRET);

    if (!validation.isValid) {
      return { isValid: false };
    }

    const payload = validation.payload;

    // Additional validation checks
    if (typeof payload !== 'object' || payload === null) {
      return { isValid: false };
    }

    // Check if token has required fields
    if (!payload.sub || !payload.exp) {
      return { isValid: false };
    }

    // Check if token is expired (with 5 minute buffer)
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp < (now - 300)) { // 5 minute buffer for clock skew
      return { isValid: false };
    }

    return { isValid: true, payload };
  } catch (error) {
    return { isValid: false };
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the route requires authentication using the secure function
  const requiresAuth = isProtectedRoute(pathname);

  // Allow public routes
  if (!requiresAuth) {
    return NextResponse.next();
  }

  // For protected routes, check authentication
  const authToken = request.cookies.get('auth-token')?.value ||
                   request.headers.get('authorization')?.replace('Bearer ', '');

  if (!authToken) {
    // Redirect to login for browser requests
    if (request.headers.get('accept')?.includes('text/html')) {
      return NextResponse.redirect(new URL('/login', request.url));
    }

    // Return 401 for API requests
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    );
  }

  // Validate the JWT token
  const tokenValidation = verifyToken(authToken);
  if (!tokenValidation.isValid) {
    // Redirect to login for browser requests
    if (request.headers.get('accept')?.includes('text/html')) {
      return NextResponse.redirect(new URL('/login', request.url));
    }

    // Return 401 for API requests
    return NextResponse.json(
      { error: 'Invalid or expired authentication token' },
      { status: 401 }
    );
  }

  // Check admin role for admin routes
  if (isAdminRoute(pathname)) {
    const payload = tokenValidation.payload;
    const userRole = payload?.role || payload?.user_role || 'user';
    const isAdmin = userRole === 'admin' || userRole === 'superadmin' || payload?.is_admin === true;
    
    if (!isAdmin) {
      // Redirect non-admins to chat (forbidden from admin area)
      if (request.headers.get('accept')?.includes('text/html')) {
        return NextResponse.redirect(new URL('/chat?error=admin_required', request.url));
      }
      
      // Return 403 for API requests
      return NextResponse.json(
        { error: 'Admin access required' },
        { status: 403 }
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files with extensions
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.).*)',
  ],
};
