import type { Metadata } from "next";
import Link from "next/link";

import { listSignalConsensusCards } from "@/src/lib/kefe-api";
import styles from "@/app/signal/page.module.css";

export const metadata: Metadata = {
  title: "Sinyal Kartları",
  description:
    "Methodology-qualified civic signal consensus cards — KEFE.",
};

function tierLabel(tier: string): string {
  switch (tier) {
    case "GOLD_STANDARD":
      return "Altın Standart";
    case "SILVER_VALIDATED":
      return "Gümüş Doğrulanmış";
    case "BRONZE_OBSERVED":
      return "Bronz Gözlemlendi";
    default:
      return tier;
  }
}

function tierColorVar(tier: string): string {
  switch (tier) {
    case "GOLD_STANDARD":
      return "var(--kefe-signal-tier-gold-standard)";
    case "SILVER_VALIDATED":
      return "var(--kefe-signal-tier-silver-validated)";
    case "BRONZE_OBSERVED":
      return "var(--kefe-signal-tier-bronze-observed)";
    default:
      return "var(--kefe-color-muted)";
  }
}

export default async function SignalPage() {
  let cards = null;
  let error: string | null = null;

  try {
    cards = await listSignalConsensusCards(20, 0);
  } catch (err) {
    error = err instanceof Error ? err.message : "Sinyal kartları yüklenemedi.";
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
        <div className={styles.grid}>
          {cards.map((card) => (
            <article key={card.signal_id} className={styles.card}>
              <header className={styles.cardHeader}>
                <span
                  className={styles.tierBadge}
                  style={{ color: tierColorVar(card.qualification_tier) }}
                >
                  {tierLabel(card.qualification_tier)}
                </span>
                <span className={styles.agreementPct}>
                  %{Math.round(card.agreement_percentage)}
                </span>
              </header>
              <h2 className={styles.cardTitle}>{card.case_title}</h2>
              <p className={styles.cardStatement}>{card.consensus_statement}</p>
              <footer className={styles.cardFooter}>
                <span className={styles.sampleSize}>
                  {card.sample_size.toLocaleString("tr-TR")} katılımcı
                </span>
                <time
                  className={styles.certifiedAt}
                  dateTime={card.certified_at}
                >
                  {new Date(card.certified_at).toLocaleDateString("tr-TR", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </time>
              </footer>
              <Link
                href={`/signal/${encodeURIComponent(card.signal_id)}`}
                className={styles.detailLink}
              >
                Sinyal Detayı →
              </Link>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}