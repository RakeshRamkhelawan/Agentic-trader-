import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: "/api/ws",
        destination: "http://api-server:8001/ws",
      },
      {
        source: "/api/v1/:path*",
        destination: "http://api-server:8001/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
