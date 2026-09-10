import type { Metadata } from "next";
import Link from "next/link";

import { listPublicCases } from "@/src/lib/kefe-api";
import styles from "@/app/cases/page.module.css";

export const metadata: Metadata = {
  title: "Meseleler",
  description:
    "KEFE — Aktif meseleler. Commit First, Blind First ile kolektif sesinizi oluşturun.",
};

const DOMAIN_LABELS: Record<string, string> = {
  GOVERNANCE: "Yönetim",
  ENVIRONMENT: "Çevre",
  SOCIAL: "Sosyal",
  ECONOMY: "Ekonomi",
  HEALTH: "Sağlık",
  EDUCATION: "Eğitim",
  TECHNOLOGY: "Teknoloji",
  CULTURE: "Kültür",
};

function domainLabel(code: string): string {
  return DOMAIN_LABELS[code] ?? code;
}

export default async function CasesPage() {
  let cases = null;
  let error: string | null = null;

  try {
    cases = await listPublicCases(20, 0);
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
        <div className={styles.grid}>
          {cases.map((c) => (
            <article key={c.case_version_id} className={styles.card}>
              <span className={styles.domainBadge}>
                {domainLabel(c.primary_domain_code)}
              </span>
              <h2 className={styles.cardTitle}>{c.title}</h2>
              <p className={styles.cardSummary}>{c.summary}</p>
              <div className={styles.cardFooter}>
                <Link
                  href={`/cases/${encodeURIComponent(c.case_id)}`}
                  className={styles.cardLink}
                >
                  İncele →
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}