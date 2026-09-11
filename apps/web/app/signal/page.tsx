import type { Metadata } from "next";

import { listSignalConsensusCards } from "@/src/lib/kefe-api";
import { SignalFilter } from "@/src/components/signal-filter";
import styles from "@/app/signal/page.module.css";

export const metadata: Metadata = {
  title: "Sinyal Kartları",
  description:
    "Methodology-qualified civic signal consensus cards — KEFE.",
};

export default async function SignalPage() {
  let cards = null;
  let error: string | null = null;

  try {
    // Load up to 100 signals — client-side filter handles the rest
    cards = await listSignalConsensusCards(100, 0);
  } catch (err) {
    error = err instanceof Error ? err.message : "Sinyaller yüklenemedi.";
  }

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1 className={styles.title}>Sinyal Kartları</h1>
        <p className={styles.subtitle}>
          Methodology-qualified kolektif ses sinyalleri
        </p>
      </div>

      {error && (
        <div className={styles.errorBanner} role="alert">
          <strong>Hata:</strong> {error}
        </div>
      )}

      {cards !== null && cards.length === 0 && (
        <div className={styles.emptyState}>
          <p>Henüz yayımlanmış sinyal kartı bulunmuyor.</p>
        </div>
      )}

      {cards !== null && cards.length > 0 && (
        <SignalFilter cards={cards} />
      )}
    </main>
  );
}