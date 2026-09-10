import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPublicShare, KefApiError } from "@/src/lib/kefe-api";
import styles from "@/app/share/[token]/page.module.css";

interface SharePageProps {
  params: Promise<{ token: string }>;
}

export async function generateMetadata(
  { params }: SharePageProps,
): Promise<Metadata> {
  const { token } = await params;
  try {
    const share = await getPublicShare(token);
    return {
      title: share.title,
      description: share.summary,
      openGraph: {
        title: share.title,
        description: share.summary,
        type: "article",
      },
    };
  } catch {
    return { title: "Paylaşım bulunamadı" };
  }
}

function isExpired(expiresAt: string): boolean {
  return new Date(expiresAt) < new Date();
}

export default async function SharePage({ params }: SharePageProps) {
  const { token } = await params;

  let share = null;
  try {
    share = await getPublicShare(token);
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  const expired = isExpired(share.expires_at);

  return (
    <main className={styles.main}>
      <div className={styles.card}>
        {expired && (
          <div className={styles.expiredBanner} role="alert">
            Bu paylaşım bağlantısının süresi dolmuş.
          </div>
        )}

        <header className={styles.header}>
          <span className={styles.domainBadge}>{share.primary_domain}</span>
          <h1 className={styles.title}>{share.title}</h1>
          <p className={styles.summary}>{share.summary}</p>
        </header>

        <div className={styles.meta}>
          <span className={styles.metaItem}>
            <span className={styles.metaLabel}>Paylaşım tarihi:</span>{" "}
            {new Date(share.created_at).toLocaleDateString("tr-TR", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>
          {!expired && (
            <span className={styles.metaItem}>
              <span className={styles.metaLabel}>Geçerlilik:</span>{" "}
              {new Date(share.expires_at).toLocaleDateString("tr-TR", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          )}
        </div>

        <div className={styles.actions}>
          <Link
            href={`/cases/${encodeURIComponent(share.case_id)}`}
            className={styles.primaryBtn}
          >
            Meseleyi incele
          </Link>
          <Link href="/cases" className={styles.secondaryBtn}>
            Tüm meseleler
          </Link>
        </div>

        <footer className={styles.footer}>
          <p className={styles.commitNote}>
            Bu meseleye katılmak için mobil uygulamayı kullanın.
            <br />
            <strong>Commit First, Blind First</strong> — sesiniz metodolojik olarak nitelendirilir.
          </p>
        </footer>
      </div>
    </main>
  );
}