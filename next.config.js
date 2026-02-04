/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/api/agent/:path*", destination: "http://localhost:8000/api/:path*" },
      // Do not rewrite /api/auth/* — NextAuth handles those in Next.js (session, providers, callback).
      // FastAPI is called from lib/auth.ts (login) and app/api/auth/register/route.ts (register).
    ];
  },
};

module.exports = nextConfig;
