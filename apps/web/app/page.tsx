import type { Metadata } from "next";

import styles from "@/app/page.module.css";

export const metadata: Metadata = {
  title: "KEFE — Kolektif ses, kurumsal etki",
  description:
    "Methodology-qualified civic deliberation. Your Commit First, your voice qualified.",
};

export default function HomePage() {
  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <h1 className={styles.heroTitle}>
          <span className={styles.heroTitleKefe}>KEFE</span>
        </h1>
        <p className={styles.heroSubtitle}>
          Kolektif ses. Kurumsal etki.
        </p>
        <p className={styles.heroDescription}>
          Methodology-qualified civic deliberation platform.
          Commit First, Blind First — your voice, qualified.
        </p>
        <div className={styles.heroCta}>
          <a href="/cases" className={styles.ctaPrimary}>
            Meseleleri incele
          </a>
          <a href="/signal" className={styles.ctaSecondary}>
            Sinyal kartları
          </a>
        </div>
      </section>
    </main>
  );
}