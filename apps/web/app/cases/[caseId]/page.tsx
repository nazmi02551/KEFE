import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  getPublicCase,
  getCaseContext,
  getCaseVersionHistory,
  listCaseSignalCards,
  KefApiError,
} from "@/src/lib/kefe-api";
import styles from "@/app/cases/[caseId]/page.module.css";

interface CaseDetailPageProps {
  params: Promise<{ caseId: string }>;
}

export async function generateMetadata(
  { params }: CaseDetailPageProps,
): Promise<Metadata> {
  const { caseId } = await params;
  try {
    const c = await getPublicCase(caseId);
    return {
      title: c.title,
      description: c.summary,
    };
  } catch {
    return { title: "Mesele bulunamadı" };
  }
}

const CLAIM_STATUS_LABELS: Record<string, string> = {
  VERIFIED: "Doğrulandı",
  CLAIMED: "İddia Edildi",
  DISPUTED: "Tartışmalı",
  UNKNOWN: "Bilinmiyor",
};

const DISCLOSURE_LEVEL_LABELS: Record<string, string> = {
  ESSENTIAL: "Temel",
  DETAIL: "Detay",
  SOURCE: "Kaynak",
};

const RISK_LABELS: Record<string, string> = {
  LOW: "Düşük",
  MEDIUM: "Orta",
  HIGH: "Yüksek",
};

const FORMAT_LABELS: Record<string, string> = {
  BINARY: "İkili seçim",
  RANKED: "Sıralama",
  SCORE: "Puanlama",
  OPEN: "Açık uçlu",
};

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const { caseId } = await params;

  let caseDetail = null;
  try {
    caseDetail = await getPublicCase(caseId);
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  // Load context, version history and signal cards in parallel — all fail-open.
  const [context, history, signalCards] = await Promise.all([
    getCaseContext(caseDetail.case_version_id),
    getCaseVersionHistory(caseId),
    listCaseSignalCards(caseDetail.case_version_id),
  ]);

  return (
    <main className={styles.main}>
      <nav className={styles.breadcrumb} aria-label="Navigasyon yolu">
        <Link href="/cases" className={styles.breadcrumbLink}>
          ← Meseleler
        </Link>
      </nav>

      <article className={styles.article}>
        <header className={styles.header}>
          <div className={styles.badges}>
            <span className={styles.domainBadge}>{caseDetail.primary_domain}</span>
            {caseDetail.is_real_event === true && (
              <span className={styles.realEventBadge} aria-label="Gerçek Olay">
                Gerçek Olay
              </span>
            )}
          </div>
          <h1 className={styles.title}>{caseDetail.title}</h1>
          <p className={styles.summary}>{caseDetail.summary}</p>
          <div className={styles.meta}>
            <span className={styles.metaItem}>
              <span className={styles.metaLabel}>Format:</span>{" "}
              {FORMAT_LABELS[caseDetail.base_format] ?? caseDetail.base_format}
            </span>
            <span className={styles.metaItem}>
              <span className={styles.metaLabel}>İçerik riski:</span>{" "}
              {RISK_LABELS[caseDetail.content_risk] ?? caseDetail.content_risk}
            </span>
            <span className={styles.metaItem}>
              <span className={styles.metaLabel}>Sürüm:</span>{" "}
              v{caseDetail.version_no}
            </span>
          </div>
        </header>

        {caseDetail.questions.length > 0 && (
          <section className={styles.questions}>
            <h2 className={styles.sectionTitle}>Sorular</h2>
            <ol className={styles.questionList}>
              {caseDetail.questions.map((q) => (
                <li key={q.question_id} className={styles.questionItem}>
                  <p className={styles.questionPrompt}>{q.prompt}</p>
                  {q.options.length > 0 && (
                    <ul className={styles.optionList} role="list">
                      {q.options.map((opt) => (
                        <li key={opt.code} className={styles.optionItem}>
                          <span className={styles.optionCode}>{opt.code}</span>
                          <span className={styles.optionLabel}>{opt.label}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ol>
          </section>
        )}

        {context !== null && context.blocks.length > 0 && (
          <section className={styles.context} aria-label="Bağlam Blokları">
            <h2 className={styles.sectionTitle}>Bağlam</h2>
            <ol className={styles.contextList}>
              {context.blocks
                .slice()
                .sort((a, b) => a.display_order - b.display_order)
                .map((block) => {
                  const blockSources = context.sources.filter((s) =>
                    block.source_ids.includes(s.source_id),
                  );
                  return (
                    <li key={block.context_block_id} className={styles.contextBlock}>
                      <div className={styles.contextBlockMeta}>
                        <span className={styles.disclosureLevel}>
                          {DISCLOSURE_LEVEL_LABELS[block.disclosure_level] ?? block.disclosure_level}
                        </span>
                        <span className={styles.claimStatus}>
                          {CLAIM_STATUS_LABELS[block.claim_status] ?? block.claim_status}
                        </span>
                      </div>
                      <h3 className={styles.contextBlockTitle}>{block.title}</h3>
                      <p className={styles.contextBlockBody}>{block.body}</p>
                      {blockSources.length > 0 && (
                        <ul className={styles.sourceList} aria-label="Kaynaklar">
                          {blockSources.map((src) => (
                            <li key={src.source_id} className={styles.sourceItem}>
                              {src.url ? (
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={styles.sourceLink}
                                >
                                  {src.title}
                                </a>
                              ) : (
                                <span className={styles.sourceTitle}>{src.title}</span>
                              )}
                              <span className={styles.sourcePublisher}>
                                {src.publisher}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}
            </ol>
          </section>
        )}

        {signalCards.length > 0 && (
          <section className={styles.signals} aria-label="Sinyal Konsensüs Kartları">
            <h2 className={styles.sectionTitle}>Sinyal Konsensüs Kartları</h2>
            <ul className={styles.signalList} role="list">
              {signalCards.map((card) => (
                <li key={card.signal_id} className={styles.signalCard}>
                  <p className={styles.signalStatement}>{card.consensus_statement}</p>
                  <div className={styles.signalMeta}>
                    <span
                      className={styles.signalTier}
                      style={{
                        color:
                          card.qualification_tier === "GOLD_STANDARD"
                            ? "var(--kefe-gold)"
                            : card.qualification_tier === "SILVER_VALIDATED"
                              ? "#9ca3af"
                              : "#b45309",
                      }}
                    >
                      {card.qualification_tier === "GOLD_STANDARD"
                        ? "Altın Standart"
                        : card.qualification_tier === "SILVER_VALIDATED"
                          ? "Gümüş Doğrulanmış"
                          : "Bronz Gözlemlendi"}
                    </span>
                    <span className={styles.signalAgreement}>
                      %{card.agreement_percentage} uzlaşı · {card.sample_size} katılımcı
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {history && history.items.length > 1 && (
          <section className={styles.history} aria-label="Sürüm Geçmişi">
            <h2 className={styles.sectionTitle}>Yayın Geçmişi</h2>
            <ol className={styles.historyList} reversed>
              {history.items.map((v) => (
                <li key={v.case_version_id} className={styles.historyItem}>
                  <span className={styles.historyBadge}>
                    {v.classification === "CURRENT" ? "Güncel" : "Önceki Sürüm"}
                  </span>
                  <span className={styles.historyVersion}>v{v.version_no}</span>
                  <span className={styles.historyTitle}>{v.title}</span>
                  {v.published_at && (
                    <time
                      dateTime={v.published_at}
                      className={styles.historyDate}
                    >
                      {new Date(v.published_at).toLocaleDateString("tr-TR")}
                    </time>
                  )}
                </li>
              ))}
            </ol>
          </section>
        )}

        <footer className={styles.footer}>
          <p className={styles.commitNotice}>
            Bu meseleye katılmak için mobil uygulamamızı kullanın.
            Commit First, Blind First — sesiniz metodolojik olarak nitelendirilir.
          </p>
        </footer>
      </article>
    </main>
  );
}