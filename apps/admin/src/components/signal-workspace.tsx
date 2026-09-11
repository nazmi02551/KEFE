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

import { useCallback, useEffect, useState } from "react";
import styles from "@/src/components/signal-workspace.module.css";
import type {
  SignalConsensusCard,
  SignalHealthReport,
  SignalQualificationReport,
} from "@/src/lib/signal-api";
import {
  getSignalHealthReport,
  getSignalQualificationReport,
  getSignalTargetRegistry,
  listSignalConsensusCards,
} from "@/src/lib/signal-api";
import type { SignalTargetRegistryReport } from "@/src/lib/signal-api";

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

interface SignalDetailPanelProps {
  card: SignalConsensusCard;
  baseUrl: string;
  onClose: () => void;
}

function SignalDetailPanel({ card, baseUrl, onClose }: SignalDetailPanelProps) {
  const [health, setHealth] = useState<SignalHealthReport | null>(null);
  const [qualification, setQualification] = useState<SignalQualificationReport | null>(null);
  const [targets, setTargets] = useState<SignalTargetRegistryReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [h, q, t] = await Promise.allSettled([
          getSignalHealthReport(baseUrl, card.signal_id),
          getSignalQualificationReport(baseUrl, card.signal_id),
          getSignalTargetRegistry(baseUrl, card.signal_id),
        ]);
        if (cancelled) return;
        if (h.status === "fulfilled") setHealth(h.value);
        if (q.status === "fulfilled") setQualification(q.value);
        if (t.status === "fulfilled") setTargets(t.value);
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [baseUrl, card.signal_id]);

  return (
    <div className={styles.detailOverlay} role="dialog" aria-modal="true" aria-label="Sinyal Detayı">
      <div className={styles.detailPanel}>
        <div className={styles.detailHeader}>
          <div>
            <span className={`${styles.tierBadge} ${TIER_CLASS[card.qualification_tier] ?? ""}`}>
              {TIER_LABELS[card.qualification_tier] ?? card.qualification_tier}
            </span>
            <h2 className={styles.detailTitle}>{card.case_title}</h2>
            <p className={styles.detailStatement}>{card.consensus_statement}</p>
          </div>
          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Kapat"
            type="button"
          >
            ✕
          </button>
        </div>

        <dl className={styles.detailMeta}>
          <dt>Uzlaşı Oranı</dt>
          <dd className={styles.agreementValue}>%{card.agreement_percentage.toFixed(1)}</dd>
          <dt>Katılımcı</dt>
          <dd>{card.sample_size.toLocaleString("tr-TR")}</dd>
          <dt>Sertifikalandırma</dt>
          <dd>{new Date(card.certified_at).toLocaleDateString("tr-TR")}</dd>
          <dt>Sinyal ID</dt>
          <dd className={styles.monospaceValue}>{card.signal_id}</dd>
        </dl>

        {loading && (
          <p className={styles.loadingText} role="status" aria-live="polite">
            Detaylar yükleniyor…
          </p>
        )}
        {error && (
          <p className={styles.errorText} role="alert">{error}</p>
        )}

        {!loading && health && (
          <section className={styles.detailSection}>
            <h3 className={styles.detailSectionTitle}>
              Sinyal Sağlık Raporu
              <span className={styles.detailSectionScore}>
                {(health.overall_health_score * 100).toFixed(0)}%
              </span>
            </h3>
            <ul className={styles.dimensionList}>
              {health.dimensions.map((d) => (
                <li key={d.dimension_id} className={styles.dimensionItem}>
                  <span className={d.is_passed ? styles.passIcon : styles.failIcon}>
                    {d.is_passed ? "✓" : "✗"}
                  </span>
                  <span className={styles.dimensionTitle}>{d.title_tr}</span>
                  <span className={styles.dimensionScore}>
                    {(d.score * 100).toFixed(0)}% / {(d.threshold * 100).toFixed(0)}%
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {!loading && qualification && (
          <section className={styles.detailSection}>
            <h3 className={styles.detailSectionTitle}>
              Yeterlilik Kriterleri
              <span className={styles.detailSectionScore}>
                {qualification.qualification_tier}
              </span>
            </h3>
            <ul className={styles.dimensionList}>
              {qualification.criteria.map((c) => (
                <li key={c.criterion_id} className={styles.dimensionItem}>
                  <span className={c.is_passed ? styles.passIcon : styles.failIcon}>
                    {c.is_passed ? "✓" : "✗"}
                  </span>
                  <span className={styles.dimensionTitle}>{c.name_tr}</span>
                  <span className={styles.dimensionScore}>
                    {(c.score * 100).toFixed(0)}% / {(c.threshold * 100).toFixed(0)}%
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {!loading && targets && targets.targets.length > 0 && (
          <section className={styles.detailSection}>
            <h3 className={styles.detailSectionTitle}>Hedef Kurumlar</h3>
            <ul className={styles.targetList}>
              {targets.targets.map((t) => (
                <li key={t.target_id} className={styles.targetItem}>
                  <span className={styles.targetName}>{t.target_name}</span>
                  <span className={styles.targetStatus}>{t.dispatch_status}</span>
                  <span className={styles.targetType}>{t.target_type}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}

interface SignalWorkspaceProps {
  baseUrl: string;
}

export function SignalWorkspace({ baseUrl }: SignalWorkspaceProps) {
  const [cards, setCards] = useState<SignalConsensusCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCard, setSelectedCard] = useState<SignalConsensusCard | null>(null);

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

  const handleClose = useCallback(() => setSelectedCard(null), []);

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

      {selectedCard && (
        <SignalDetailPanel
          card={selectedCard}
          baseUrl={baseUrl}
          onClose={handleClose}
        />
      )}

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

              <button
                type="button"
                className={styles.detailButton}
                onClick={() => setSelectedCard(card)}
              >
                Detayları Görüntüle →
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}