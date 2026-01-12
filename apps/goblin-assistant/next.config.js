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
  // API proxy to Fly.io backend
  async rewrites() {
    return [
      {
        source: '/chat/:path*',
        destination: 'https://goblin-backend.fly.dev/chat/:path*',
      },
      {
        source: '/api/:path*',
        destination: 'https://goblin-backend.fly.dev/api/:path*',
      },
      {
        source: '/health',
        destination: 'https://goblin-backend.fly.dev/health',
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
