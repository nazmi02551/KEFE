import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import "@/app/globals.css";
import { SiteFooter } from "@/src/components/site-footer";
import { SiteHeader } from "@/src/components/site-header";

export const metadata: Metadata = {
  title: {
    default: "KEFE",
    template: "%s · KEFE",
  },
  description:
    "KEFE — Kolektif ses, kurumsal etki. Methodology-qualified civic deliberation platform.",
  applicationName: "KEFE",
  keywords: ["kefe", "deliberation", "civic", "signal", "impact"],
  openGraph: {
    type: "website",
    locale: "tr_TR",
    alternateLocale: "en_US",
    siteName: "KEFE",
    url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app",
    title: "KEFE — Kolektif ses, kurumsal etki",
    description:
      "Methodology-qualified civic deliberation. Commit First, Blind First — sesiniz nitelendiriliyor.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "KEFE — Kolektif ses, kurumsal etki",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "KEFE",
    description:
      "Methodology-qualified civic deliberation platform.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
    },
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0A0A0F" },
    { media: "(prefers-color-scheme: light)", color: "#F5F4EF" },
  ],
  colorScheme: "dark light",
  width: "device-width",
  initialScale: 1,
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="tr" data-theme="dark" suppressHydrationWarning>
      <body>
        {/* Theme script: applies saved theme before paint to prevent flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
(function(){
  try {
    var t = localStorage.getItem('kefe-theme');
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  } catch(e){}
})();
`.trim(),
          }}
        />
        <SiteHeader />
        <div id="app-root">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}