import type { Metadata } from "next";

import { listPublicCases } from "@/src/lib/kefe-api";
import { CasesFilter } from "@/src/components/cases-filter";
import styles from "@/app/cases/page.module.css";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export const metadata: Metadata = {
  title: "Meseleler",
  description:
    "KEFE — Aktif meseleler. Commit First, Blind First ile kolektif sesinizi oluşturun.",
  openGraph: {
    title: "Meseleler · KEFE",
    description: "Aktif meseleler — Commit First, Blind First ile kolektif sesinizi oluşturun.",
    url: `${_siteUrl}/cases`,
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Meseleler · KEFE",
    description: "Aktif meseleler — Commit First, Blind First.",
  },
};

export default async function CasesPage() {
  let cases = null;
  let error: string | null = null;

  try {
    // Load up to 100 cases — client-side filter handles the rest
    cases = await listPublicCases(100, 0);
  } catch (err) {
    error = err instanceof Error ? err.message : "Meseleler yüklenemedi.";
  }

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1 className={styles.title}>Meseleler</h1>
        <p className={styles.subtitle}>
          Aktif meseleler — Commit First, Blind First
        </p>
      </div>

      {error && (
        <div className={styles.errorBanner} role="alert">
          <strong>Hata:</strong> {error}
        </div>
      )}

      {cases !== null && cases.length === 0 && (
        <div className={styles.emptyState}>
          <p>Henüz yayımlanmış mesele bulunmuyor.</p>
        </div>
      )}

      {cases !== null && cases.length > 0 && (
        <CasesFilter cases={cases} />
      )}
    </main>
  );
}