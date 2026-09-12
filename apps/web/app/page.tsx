import type { Metadata } from "next";
import Link from "next/link";

import {
  listPublicCases,
  listSignalConsensusCards,
  listActionMilestones,
} from "@/src/lib/kefe-api";
import styles from "@/app/page.module.css";

export const metadata: Metadata = {
  title: "KEFE — Kolektif ses, kurumsal etki",
  description:
    "Methodology-qualified civic deliberation. Your Commit First, your voice qualified.",
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
  DAILY_LIFE: "Günlük Yaşam",
};

const TIER_LABELS: Record<string, string> = {
  GOLD_STANDARD: "Altın Standart",
  SILVER_VALIDATED: "Gümüş",
  BRONZE_OBSERVED: "Bronz",
};

const ACTION_STATUS_LABELS: Record<string, string> = {
  PROPOSED: "Önerildi",
  IN_PROGRESS: "Devam Ediyor",
  VERIFIED_COMPLETE: "Tamamlandı",
  STALLED: "Askıya Alındı",
};

export default async function HomePage() {
  // All three are fail-open — errors yield empty arrays
  const [recentCases, signalCards, actions] = await Promise.all([
    listPublicCases(4, 0).catch(() => []),
    listSignalConsensusCards(3, 0).catch(() => []),
    listActionMilestones().catch(() => []),
  ]);

  const activeActions = actions.filter(
    (a) => a.status === "IN_PROGRESS" || a.status === "PROPOSED",
  ).slice(0, 3);

  return (
    <main className={styles.main}>
      {/* Hero */}
      <section className={styles.hero} aria-label="Giriş">
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            <span className={styles.heroTitleKefe}>KEFE</span>
          </h1>
          <p className={styles.heroSubtitle}>Kolektif ses. Kurumsal etki.</p>
          <p className={styles.heroDescription}>
            Methodology-qualified civic deliberation.{" "}
            <strong>Commit First, Blind First</strong> — sesiniz nitelendiriliyor.
          </p>
          <div className={styles.heroCta}>
            <Link href="/cases" className={styles.ctaPrimary}>
              Meseleleri incele
            </Link>
            <Link href="/signal" className={styles.ctaSecondary}>
              Sinyal kartları
            </Link>
          </div>
        </div>
      </section>

      {/* Methodology bar */}
      <section className={styles.methodologyBar} aria-label="Metodoloji">
        <div className={styles.methodologyItems}>
          <div className={styles.methodologyItem}>
            <span className={styles.methodologyLabel}>Commit First</span>
            <span className={styles.methodologyDesc}>
              Karar ver, sonra kolektif sonucu gör
            </span>
          </div>
          <div className={styles.methodologyDivider} aria-hidden="true" />
          <div className={styles.methodologyItem}>
            <span className={styles.methodologyLabel}>Blind First</span>
            <span className={styles.methodologyDesc}>
              Sonuç öncesi bağımsız değerlendirme
            </span>
          </div>
          <div className={styles.methodologyDivider} aria-hidden="true" />
          <div className={styles.methodologyItem}>
            <span className={styles.methodologyLabel}>Signal → Impact</span>
            <span className={styles.methodologyDesc}>
              Nitelendirilmiş ses → kurumsal yanıt
            </span>
          </div>
        </div>
      </section>

      {/* Recent cases */}
      {recentCases.length > 0 && (
        <section className={styles.section} aria-label="Son Meseleler">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Güncel Meseleler</h2>
            <Link href="/cases" className={styles.seeAll}>
              Tümünü gör →
            </Link>
          </div>
          <div className={styles.caseGrid}>
            {recentCases.map((c) => (
              <article key={c.case_version_id} className={styles.caseCard}>
                <div className={styles.caseCardBadge}>
                  {DOMAIN_LABELS[c.primary_domain_code] ?? c.primary_domain_code}
                </div>
                <h3 className={styles.caseCardTitle}>{c.title}</h3>
                <p className={styles.caseCardSummary}>{c.summary}</p>
                <Link
                  href={`/cases/${encodeURIComponent(c.case_id)}`}
                  className={styles.caseCardLink}
                >
                  İncele →
                </Link>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Signal cards */}
      {signalCards.length > 0 && (
        <section className={styles.section} aria-label="Sinyal Konsensüs Kartları">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Öne Çıkan Sinyaller</h2>
            <Link href="/signal" className={styles.seeAll}>
              Tümünü gör →
            </Link>
          </div>
          <div className={styles.signalGrid}>
            {signalCards.map((card) => (
              <article key={card.signal_id} className={styles.signalCard}>
                <div className={styles.signalCardHeader}>
                  <span className={styles.signalTier}>
                    {TIER_LABELS[card.qualification_tier] ?? card.qualification_tier}
                  </span>
                  <span className={styles.signalAgreement}>
                    %{Math.round(card.agreement_percentage)}
                  </span>
                </div>
                <p className={styles.signalStatement}>{card.consensus_statement}</p>
                <span className={styles.signalSample}>
                  {card.sample_size.toLocaleString("tr-TR")} katılımcı
                </span>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Active actions */}
      {activeActions.length > 0 && (
        <section className={styles.section} aria-label="Aktif Eylemler">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Eylem Takibi</h2>
            <Link href="/impact" className={styles.seeAll}>
              Tümünü gör →
            </Link>
          </div>
          <ul className={styles.actionList} role="list">
            {activeActions.map((a) => (
              <li key={a.action_id} className={styles.actionItem}>
                <div className={styles.actionItemHeader}>
                  <span className={styles.actionTitle}>{a.title}</span>
                  <span className={styles.actionStatus}>
                    {ACTION_STATUS_LABELS[a.status] ?? a.status}
                  </span>
                </div>
                <div className={styles.progressBar} role="presentation">
                  <div
                    className={styles.progressFill}
                    style={{ width: `${a.progress_percentage}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* CTA footer */}
      <section className={styles.ctaSection} aria-label="Uygulamaya geç">
        <h2 className={styles.ctaSectionTitle}>Kolektif sese katılın</h2>
        <p className={styles.ctaSectionDesc}>
          Mobil uygulamamızla Commit First metodolojisiyle değerlendirin.
        </p>
        <Link href="/cases" className={styles.ctaPrimary}>
          Meseleleri keşfet
        </Link>
      </section>
    </main>
  );
}