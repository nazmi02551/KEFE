/**
 * Next.js robots.txt — KEFE Web
 *
 * Admin and internal paths are disallowed.
 * Share preview pages are allowed for Open Graph crawlers.
 */

import type { MetadataRoute } from "next";

const BASE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/cases", "/signal", "/impact", "/share/"],
        disallow: [
          "/api/",
          "/_next/",
          "/internal/",
        ],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}