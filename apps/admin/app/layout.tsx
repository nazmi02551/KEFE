import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/app/globals.css";
import { AdminStudioHeader } from "@/src/components/admin-studio-header";

export const metadata: Metadata = {
  title: "KEFE Admin Studio",
  description: "Secured editorial operations workspace for KEFE",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr" data-theme="dark">
      <body>
        <AdminStudioHeader />
        {children}
      </body>
    </html>
  );
}
