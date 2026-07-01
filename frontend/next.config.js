/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ["http://10.27.15.169:3001", "http://10.27.15.169"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8002/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
