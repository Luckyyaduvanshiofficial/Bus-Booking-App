/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
      },
    ],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_BACKEND_API: process.env.NEXT_PUBLIC_BACKEND_API || 'http://localhost:8000',
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },

  // PWA support
  headers: async () => [
    {
      source: '/:path*',
      headers: [
        {
          key: 'X-UA-Compatible',
          value: 'IE=edge',
        },
      ],
    },
  ],

  // Rewrites for API
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_BACKEND_API}/api/:path*`,
        },
      ],
    };
  },
};

module.exports = nextConfig;
