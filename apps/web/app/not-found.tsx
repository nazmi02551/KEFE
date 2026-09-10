import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/app/not-found.module.css";

export const metadata: Metadata = {
  title: "Sayfa bulunamadı",
};

export default function NotFound() {
  return (
    <main className={styles.main}>
      <p className={styles.code}>404</p>
      <h1 className={styles.title}>Sayfa bulunamadı</h1>
      <p className={styles.description}>
        Aradığınız sayfa mevcut değil veya taşınmış olabilir.
      </p>
      <Link href="/" className={styles.homeLink}>
        Ana sayfaya dön
      </Link>
    </main>
  );
}