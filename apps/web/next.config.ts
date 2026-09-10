import type { NextConfig } from "next";

/**
 * KEFE Web — Next.js configuration
 *
 * This is the public consumer-facing web application.
 * It shares the KEFE API backend with the Admin Studio but serves
 * end-user-facing deep-link, share and public signal/case surfaces.
 *
 * Environment variables:
 *   NEXT_PUBLIC_KEFE_API_BASE_URL — public API base URL (browser-visible)
 *   KEFE_API_BASE_URL             — server-side API base URL (SSR/ISR)
 */

const nextConfig: NextConfig = {
  // Strict mode enabled for React concurrent mode compliance.
  reactStrictMode: true,

  // No external image domains configured yet; add when media CDN is confirmed.
  images: {
    remotePatterns: [],
  },

  // Disable x-powered-by header.
  poweredByHeader: false,

  // All web output routes are server-rendered or static.
  // No edge runtime is used until provider/CDN is confirmed.
  output: undefined,
};

export default nextConfig;