/**
 * Next.js dynamic sitemap — KEFE Web
 *
 * Includes static pages + dynamically fetched case pages.
 * Cases are fetched at build/ISR time. On error, static pages only.
 */

import type { MetadataRoute } from "next";

import { listPublicCases } from "@/src/lib/kefe-api";

const BASE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${BASE_URL}/cases`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/signal`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.85,
    },
    {
      url: `${BASE_URL}/impact`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
  ];

  let dynamicCaseRoutes: MetadataRoute.Sitemap = [];
  try {
    const cases = await listPublicCases(100, 0);
    dynamicCaseRoutes = cases.map((c) => ({
      url: `${BASE_URL}/cases/${encodeURIComponent(c.case_id)}`,
      lastModified: new Date(),
      changeFrequency: "weekly" as const,
      priority: 0.6,
    }));
  } catch {
    // Fail open — static pages only if API unavailable
  }

  return [...staticRoutes, ...dynamicCaseRoutes];
}