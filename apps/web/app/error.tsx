"use client";

import Link from "next/link";
import { useEffect } from "react";

import styles from "@/app/error.module.css";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // In production, log to an error monitoring service
    if (process.env.NODE_ENV === "production") {
      console.error("[KEFE Error Boundary]", error.message, error.digest);
    }
  }, [error]);

  return (
    <main className={styles.main} role="alert" aria-live="assertive">
      <p className={styles.code}>Hata</p>
      <h1 className={styles.title}>Bir şeyler yanlış gitti</h1>
      <p className={styles.description}>
        Sayfa yüklenirken beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.
      </p>
      {error.digest && (
        <p className={styles.digest}>
          Hata kodu: <code>{error.digest}</code>
        </p>
      )}
      <div className={styles.actions}>
        <button
          type="button"
          onClick={reset}
          className={styles.retryButton}
        >
          Tekrar Dene
        </button>
        <Link href="/" className={styles.homeLink}>
          Ana sayfaya dön
        </Link>
      </div>
    </main>
  );
}