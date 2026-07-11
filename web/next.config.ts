import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so the app can be served from Butterbase's static hosting.
  output: "export",
  // Emit each route as <route>/index.html — client-side navigation on plain
  // static hosts breaks without this (the router's ?_rsc= fetch gets HTML).
  trailingSlash: true,
  experimental: {
    // Next 16's client segment cache issues dynamic ?_rsc= requests for
    // dynamic-param routes, which a static host answers with HTML — client
    // navigation then stalls silently. Disable it for the static export.
    clientSegmentCache: false,
  },
};

export default nextConfig;
