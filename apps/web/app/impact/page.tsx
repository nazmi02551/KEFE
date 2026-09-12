import type { Metadata } from "next";
import Link from "next/link";

import {
  listInstitutionResponses,
  listActionMilestones,
} from "@/src/lib/kefe-api";
import styles from "@/app/impact/page.module.css";

export const metadata: Metadata = {
  title: "Etki Takibi",
  description:
    "KEFE — Kurumsal yanıtlar ve eylem kilometre taşları. Signal'dan Impact'e.",
};

const RESPONSE_TYPE_LABELS: Record<string, string> = {
  ACKNOWLEDGE: "Alındı",
  COMMITMENT: "Taahhüt",
  POLICY_CHANGE: "Politika Değişikliği",
  FACTUAL_CLARIFICATION: "Bilgi Tashihi",
  DECLINE_WITH_REASON: "Gerekçeli Red",
};

const ACTION_STATUS_LABELS: Record<string, string> = {
  PROPOSED: "Önerildi",
  IN_PROGRESS: "Devam Ediyor",
  VERIFIED_COMPLETE: "Tamamlandı",
  STALLED: "Askıya Alındı",
};

const VERIFICATION_LABELS: Record<string, string> = {
  VERIFIED: "Doğrulandı",
  PENDING: "Beklemede",
  REJECTED: "Reddedildi",
};

function responseTypeLabel(code: string): string {
  return RESPONSE_TYPE_LABELS[code] ?? code;
}

function actionStatusLabel(code: string): string {
  return ACTION_STATUS_LABELS[code] ?? code;
}

function verificationLabel(code: string): string {
  return VERIFICATION_LABELS[code] ?? code;
}

function actionStatusClass(status: string): string {
  switch (status) {
    case "PROPOSED": return styles.statusProposed;
    case "IN_PROGRESS": return styles.statusInProgress;
    case "VERIFIED_COMPLETE": return styles.statusComplete;
    case "STALLED": return styles.statusStalled;
    default: return styles.statusProposed;
  }
}

export default async function ImpactPage() {
  let responses = null;
  let actions = null;
  let error: string | null = null;

  try {
    [responses, actions] = await Promise.all([
      listInstitutionResponses(),
      listActionMilestones(),
    ]);
  } catch (err) {
    error = err instanceof Error ? err.message : "Etki verileri yüklenemedi.";
  }

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1 className={styles.title}>Etki Takibi</h1>
        <p className={styles.subtitle}>
          Signal → Impact: Kurumsal yanıtlar ve eylem kilometre taşları
        </p>
      </div>

      {error && (
        <div className={styles.errorBanner} role="alert">
          <strong>Hata:</strong> {error}
        </div>
      )}

      <div className={styles.layout}>
        {/* Institution responses */}
        <section className={styles.section} aria-label="Kurumsal Yanıtlar">
          <h2 className={styles.sectionTitle}>
            Kurumsal Yanıtlar
            {responses && responses.length > 0 && (
              <span className={styles.sectionCount}>{responses.length}</span>
            )}
          </h2>

          {responses !== null && responses.length === 0 && (
            <div className={styles.emptyState}>
              <p>Henüz kayıtlı kurumsal yanıt bulunmuyor.</p>
            </div>
          )}

          {responses !== null && responses.length > 0 && (
            <ul className={styles.responseList} role="list">
              {responses.map((r) => (
                <li key={r.response_id} className={styles.responseCard}>
                  <div className={styles.responseHeader}>
                    <span className={styles.institutionName}>
                      {r.institution_name}
                    </span>
                    <span className={styles.verificationBadge}>
                      {verificationLabel(r.verification_status)}
                    </span>
                  </div>
                  <p className={styles.authorityRole}>{r.authority_role}</p>
                  <p className={styles.responseType}>
                    {responseTypeLabel(r.response_type)}
                  </p>
                  <p className={styles.statement}>{r.statement}</p>
                  <time
                    className={styles.publishedAt}
                    dateTime={r.published_at}
                  >
                    {new Date(r.published_at).toLocaleDateString("tr-TR", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Action milestones */}
        <section className={styles.section} aria-label="Eylem Kilometre Taşları">
          <h2 className={styles.sectionTitle}>
            Eylem Kilometre Taşları
            {actions && actions.length > 0 && (
              <span className={styles.sectionCount}>{actions.length}</span>
            )}
          </h2>

          {actions !== null && actions.length === 0 && (
            <div className={styles.emptyState}>
              <p>Henüz kayıtlı eylem bulunmuyor.</p>
            </div>
          )}

          {actions !== null && actions.length > 0 && (
            <ul className={styles.actionList} role="list">
              {actions.map((a) => (
                <li key={a.action_id} className={styles.actionCard}>
                  <div className={styles.actionHeader}>
                    <h3 className={styles.actionTitle}>{a.title}</h3>
                    <span className={`${styles.statusBadge} ${actionStatusClass(a.status)}`}>
                      {actionStatusLabel(a.status)}
                    </span>
                  </div>
                  <p className={styles.actionDescription}>{a.description}</p>
                  <div className={styles.progressRow}>
                    <div
                      className={styles.progressBar}
                      role="progressbar"
                      aria-valuenow={a.progress_percentage}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`İlerleme: %${a.progress_percentage}`}
                    >
                      <div
                        className={styles.progressFill}
                        style={{ width: `${a.progress_percentage}%` }}
                      />
                    </div>
                    <span className={styles.progressLabel}>
                      %{a.progress_percentage}
                    </span>
                  </div>
                  {a.evidence_summary && (
                    <p className={styles.evidenceSummary}>{a.evidence_summary}</p>
                  )}
                  {a.target_completion_date && (
                    <time
                      className={styles.targetDate}
                      dateTime={a.target_completion_date}
                    >
                      Hedef: {new Date(a.target_completion_date).toLocaleDateString("tr-TR")}
                    </time>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <footer className={styles.footer}>
        <p className={styles.footerNote}>
          Etki kaydı, kurumsal otorite doğrulamasından geçmiş yanıtlarla sınırlıdır.
          Signal metodolojisinden bağımsız olarak değerlendirilemez.
        </p>
        <nav className={styles.footerNav} aria-label="İlgili sayfalar">
          <Link href="/signal" className={styles.footerLink}>Sinyaller</Link>
          <Link href="/cases" className={styles.footerLink}>Meseleler</Link>
        </nav>
      </footer>
    </main>
  );
}