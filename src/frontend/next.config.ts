import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "localhost:3000",
    "10.255.250.60:3000",
    "*.ngrok-free.dev",
    "*.ngrok-free.app",
    "*.trycloudflare.com",
  ],

};

export default nextConfig;
