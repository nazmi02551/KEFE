"use client";

/**
 * Signal Workspace — Admin Studio
 *
 * Read-only dashboard for qualified signals.
 * Signals are computed from the live decision pipeline; they cannot be
 * created or edited manually in Admin Studio.
 *
 * Design system: dark-first, gold accent, semantic surfaces.
 */

import { useEffect, useState } from "react";
import styles from "@/src/components/signal-workspace.module.css";
import type { SignalConsensusCard } from "@/src/lib/signal-api";
import { listSignalConsensusCards } from "@/src/lib/signal-api";

const TIER_LABELS: Record<string, string> = {
  GOLD_STANDARD: "Altın Standart",
  SILVER_VALIDATED: "Gümüş Doğrulanmış",
  BRONZE_OBSERVED: "Bronz Gözlemlenmiş",
  UNQUALIFIED: "Nitelenmemiş",
};

const TIER_CLASS: Record<string, string> = {
  GOLD_STANDARD: styles.tierGold,
  SILVER_VALIDATED: styles.tierSilver,
  BRONZE_OBSERVED: styles.tierBronze,
  UNQUALIFIED: styles.tierUnqualified,
};

interface SignalWorkspaceProps {
  baseUrl: string;
}

export function SignalWorkspace({ baseUrl }: SignalWorkspaceProps) {
  const [cards, setCards] = useState<SignalConsensusCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const result = await listSignalConsensusCards(baseUrl, { limit: 50 });
        if (!cancelled) setCards(result);
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [baseUrl]);

  if (loading) {
    return (
      <div className={styles.workspace}>
        <p className={styles.loadingText} role="status" aria-live="polite">
          Sinyaller yükleniyor…
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.workspace}>
        <p className={styles.errorText} role="alert">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className={styles.workspace}>
      <header className={styles.workspaceHeader}>
        <h1 className={styles.title}>Sinyal Panosu</h1>
        <p className={styles.subtitle}>
          Nitelikli sinyaller, yalnızca Taahhüt İlk (Commit-First) ön-sonuç katılımlarından
          hesaplanır. Kolektif sonuç otomatik olarak sinyal sayılmaz.
        </p>
      </header>

      {cards.length === 0 ? (
        <div className={styles.emptyState}>
          <p>Henüz nitelikli bir sinyal bulunmuyor.</p>
          <p className={styles.emptyHint}>
            Sinyaller, bir dava için yeterli sayıda Taahhüt İlk katılım sağlandığında
            otomatik olarak hesaplanır.
          </p>
        </div>
      ) : (
        <ul className={styles.cardList} aria-label="Sinyal listesi">
          {cards.map((card) => (
            <li key={card.signal_id} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={`${styles.tierBadge} ${TIER_CLASS[card.qualification_tier] ?? ""}`}>
                  {TIER_LABELS[card.qualification_tier] ?? card.qualification_tier}
                </span>
                <time className={styles.certifiedAt} dateTime={card.certified_at}>
                  {new Date(card.certified_at).toLocaleDateString("tr-TR")}
                </time>
              </div>

              <h2 className={styles.caseTitle}>{card.case_title}</h2>
              <p className={styles.consensusStatement}>{card.consensus_statement}</p>

              <dl className={styles.metaGrid}>
                <dt>Uzlaşı Oranı</dt>
                <dd className={styles.agreementValue}>
                  %{card.agreement_percentage.toFixed(1)}
                </dd>
                <dt>Katılımcı</dt>
                <dd>{card.sample_size.toLocaleString("tr-TR")}</dd>
              </dl>

              <div className={styles.signalLinks}>
                <a
                  href={`/signal/${card.signal_id}/health`}
                  className={styles.signalLink}
                >
                  Sağlık Raporu →
                </a>
                <a
                  href={`/signal/${card.signal_id}/qualification`}
                  className={styles.signalLink}
                >
                  Yeterlilik Raporu →
                </a>
                <a
                  href={`/signal/${card.signal_id}/scope-alignment`}
                  className={styles.signalLink}
                >
                  Kapsam Uyumu →
                </a>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}