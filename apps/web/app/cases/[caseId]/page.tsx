import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPublicCase, KefApiError } from "@/src/lib/kefe-api";
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

  return (
    <main className={styles.main}>
      <nav className={styles.breadcrumb} aria-label="Navigasyon yolu">
        <Link href="/cases" className={styles.breadcrumbLink}>
          ← Meseleler
        </Link>
      </nav>

      <article className={styles.article}>
        <header className={styles.header}>
          <span className={styles.domainBadge}>{caseDetail.primary_domain}</span>
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