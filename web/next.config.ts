import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so the app can be served from Butterbase's static hosting.
  output: "export",
};

export default nextConfig;
