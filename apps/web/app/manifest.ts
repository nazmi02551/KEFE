/**
 * Next.js Web App Manifest — KEFE Web
 *
 * Enables PWA installation prompt on mobile browsers.
 * Dark-first KEFE identity: gold (#c9a227) + dark canvas (#0a0a0d).
 */

import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "KEFE",
    short_name: "KEFE",
    description:
      "Kolektif ses. Kurumsal etki. Methodology-qualified civic deliberation.",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0d",
    theme_color: "#c9a227",
    lang: "tr",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
    categories: ["news", "social", "utilities"],
    orientation: "portrait",
  };
}