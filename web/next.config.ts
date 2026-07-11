import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so the app can be served from Butterbase's static hosting.
  output: "export",
  // Emit each route as <route>/index.html so direct navigation works on a
  // plain static host.
  trailingSlash: true,
};

export default nextConfig;
