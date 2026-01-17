/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' }, // External images
    ],
  },
  typescript: {
    ignoreBuildErrors: false,     // Keep TypeScript checking
  },
  eslint: {
    ignoreDuringBuilds: true,    // Temporarily disable ESLint in builds
  },
  // API proxy to backend - ONLY proxy /api routes, NOT page routes
  // NOTE: Using Fly.io until Kamatera backend is configured
  async rewrites() {
    return [
      {
        // Proxy API chat endpoint (not the /chat page)
        source: '/api/chat/:path*',
        destination: 'https://goblin-backend.fly.dev/chat/:path*',
      },
      {
        // Proxy all other API routes
        source: '/api/:path*',
        destination: 'https://goblin-backend.fly.dev/api/:path*',
      },
      {
        source: '/health',
        destination: 'https://goblin-backend.fly.dev/health',
      },
      {
        // V1 sandbox API
        source: '/v1/:path*',
        destination: 'https://goblin-backend.fly.dev/v1/:path*',
      },
      {
        // Legacy execute endpoint
        source: '/execute/:path*',
        destination: 'https://goblin-backend.fly.dev/execute/:path*',
      },
    ];
  },
  // Security headers
  async headers() {
    return [
      {
        // Apply to all routes
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
}

export default nextConfig
