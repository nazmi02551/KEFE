import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  getSignalHealth,
  getSignalQualification,
  listSignalConsensusCards,
  KefApiError,
} from "@/src/lib/kefe-api";
import styles from "@/app/signal/[signalId]/page.module.css";

interface SignalDetailPageProps {
  params: Promise<{ signalId: string }>;
}

const TIER_LABELS: Record<string, string> = {
  GOLD_STANDARD: "Altın Standart",
  SILVER_VALIDATED: "Gümüş Doğrulanmış",
  BRONZE_OBSERVED: "Bronz Gözlemlendi",
  UNQUALIFIED: "Nitelenmemiş",
};

export async function generateMetadata(
  { params }: SignalDetailPageProps,
): Promise<Metadata> {
  const { signalId } = await params;
  try {
    const q = await getSignalQualification(signalId);
    if (!q) return { title: "Sinyal bulunamadı" };
    return {
      title: `Sinyal — ${q.case_title}`,
      description: `${TIER_LABELS[q.qualification_tier] ?? q.qualification_tier} · %${(q.overall_score * 100).toFixed(0)} · ${q.sample_size} katılımcı`,
    };
  } catch {
    return { title: "Sinyal bulunamadı" };
  }
}

export default async function SignalDetailPage({ params }: SignalDetailPageProps) {
  const { signalId } = await params;

  // Load card (for consensus statement), health and qualification in parallel.
  const [cards, health, qualification] = await Promise.all([
    listSignalConsensusCards(100, 0).catch(() => []),
    getSignalHealth(signalId).catch(() => null),
    getSignalQualification(signalId).catch((err: unknown) => {
      if (err instanceof KefApiError && err.status === 404) return null;
      throw err;
    }),
  ]);

  if (!qualification && !health) notFound();

  const card = cards.find((c) => c.signal_id === signalId);

  return (
    <main className={styles.main}>
      <nav className={styles.breadcrumb} aria-label="Navigasyon yolu">
        <Link href="/signal" className={styles.breadcrumbLink}>
          ← Sinyaller
        </Link>
      </nav>

      <article className={styles.article}>
        <header className={styles.header}>
          {qualification && (
            <span className={styles.tierBadge}>
              {TIER_LABELS[qualification.qualification_tier] ?? qualification.qualification_tier}
            </span>
          )}

          <h1 className={styles.title}>
            {qualification?.case_title ?? "Sinyal"}
          </h1>

          {card && (
            <p className={styles.consensusStatement}>
              {card.consensus_statement}
            </p>
          )}

          <div className={styles.metaRow}>
            {qualification && (
              <>
                <span className={styles.metaItem}>
                  <span className={styles.metaLabel}>Genel Skor:</span>{" "}
                  <span className={styles.metaScore}>
                    %{(qualification.overall_score * 100).toFixed(1)}
                  </span>
                </span>
                <span className={styles.metaItem}>
                  <span className={styles.metaLabel}>Katılımcı:</span>{" "}
                  {qualification.sample_size.toLocaleString("tr-TR")}
                </span>
              </>
            )}
            {card && (
              <span className={styles.metaItem}>
                <span className={styles.metaLabel}>Uzlaşı:</span>{" "}
                %{card.agreement_percentage.toFixed(1)}
              </span>
            )}
            {qualification?.certified_at && (
              <time
                dateTime={qualification.certified_at}
                className={styles.metaItem}
              >
                {new Date(qualification.certified_at).toLocaleDateString("tr-TR")}
              </time>
            )}
          </div>
        </header>

        {health && (
          <section className={styles.section} aria-label="Sinyal Sağlık Raporu">
            <h2 className={styles.sectionTitle}>
              Sinyal Sağlık Raporu
              <span className={styles.sectionScore}>
                %{(health.overall_health_score * 100).toFixed(0)}
              </span>
            </h2>
            <ul className={styles.dimensionList} role="list">
              {health.dimensions.map((d) => (
                <li key={d.dimension_id} className={styles.dimensionItem}>
                  <span
                    className={d.is_passed ? styles.passIcon : styles.failIcon}
                    aria-label={d.is_passed ? "Geçti" : "Başarısız"}
                  >
                    {d.is_passed ? "✓" : "✗"}
                  </span>
                  <span className={styles.dimensionTitle}>{d.title_tr}</span>
                  <span className={styles.dimensionScore}>
                    %{(d.score * 100).toFixed(0)} / %{(d.threshold * 100).toFixed(0)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {qualification && qualification.criteria.length > 0 && (
          <section className={styles.section} aria-label="Yeterlilik Kriterleri">
            <h2 className={styles.sectionTitle}>Yeterlilik Kriterleri</h2>
            <ul className={styles.dimensionList} role="list">
              {qualification.criteria.map((c) => (
                <li key={c.criterion_id} className={styles.dimensionItem}>
                  <span
                    className={c.is_passed ? styles.passIcon : styles.failIcon}
                    aria-label={c.is_passed ? "Geçti" : "Başarısız"}
                  >
                    {c.is_passed ? "✓" : "✗"}
                  </span>
                  <span className={styles.dimensionTitle}>{c.name_tr}</span>
                  <span className={styles.dimensionScore}>
                    %{(c.score * 100).toFixed(0)} / %{(c.threshold * 100).toFixed(0)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {qualification?.eligible_channels && qualification.eligible_channels.length > 0 && (
          <section className={styles.section} aria-label="Uygun Kanallar">
            <h2 className={styles.sectionTitle}>Uygun Dağıtım Kanalları</h2>
            <ul className={styles.channelList} role="list">
              {qualification.eligible_channels.map((ch) => (
                <li key={ch} className={styles.channelItem}>{ch}</li>
              ))}
            </ul>
          </section>
        )}

        <footer className={styles.footer}>
          <p className={styles.footerNote}>
            Sinyal niteliği, yalnızca Taahhüt İlk (Commit-First) ön-sonuç metodolojisiyle
            hesaplanır. Kolektif sonuç otomatik olarak sinyal veya gerçek sayılmaz.
          </p>
          {qualification?.qualification_audit_hash && (
            <p className={styles.auditHash}>
              Denetim: <code>{qualification.qualification_audit_hash.slice(0, 16)}…</code>
            </p>
          )}
          <nav className={styles.footerNav} aria-label="İlgili sayfalar">
            <Link href="/impact" className={styles.footerLink}>
              Etki Takibi →
            </Link>
            <Link href="/signal" className={styles.footerLink}>
              ← Tüm Sinyaller
            </Link>
          </nav>
        </footer>
      </article>
    </main>
  );
}