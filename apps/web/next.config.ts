import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), geolocation=(), microphone=()",
  },
];

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

  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },

  // All web output routes are server-rendered or static.
  // No edge runtime is used until provider/CDN is confirmed.
  output: undefined,
};

export default nextConfig;
