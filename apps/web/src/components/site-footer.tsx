import Link from "next/link";

import styles from "@/src/components/site-footer.module.css";

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span className={styles.logo}>KEFE</span>
          <p className={styles.tagline}>
            Kolektif ses. Kurumsal etki.
          </p>
        </div>

        <nav className={styles.links} aria-label="Footer navigasyon">
          <ul className={styles.linkList} role="list">
            <li>
              <Link href="/cases" className={styles.link}>
                Meseleler
              </Link>
            </li>
            <li>
              <Link href="/signal" className={styles.link}>
                Sinyaller
              </Link>
            </li>
            <li>
              <Link href="/impact" className={styles.link}>
                Etki
              </Link>
            </li>
            <li>
              <Link href="/about" className={styles.link}>
                Metodoloji
              </Link>
            </li>
            <li>
              <Link href="/faq" className={styles.link}>
                SSS
              </Link>
            </li>
            <li>
              <Link href="/privacy" className={styles.link}>
                Gizlilik
              </Link>
            </li>
          </ul>
        </nav>

        <div className={styles.methodology}>
          <p className={styles.methodologyText}>
            <strong>Commit First · Blind First</strong> —
            Sonuçlar ve perspektifler yalnızca taahhüt sonrası görünür.
            Kolektif sonuç otomatik olarak sinyal veya gerçek sayılmaz.
          </p>
        </div>
      </div>

      <div className={styles.bottom}>
        <p className={styles.copyright}>
          © {new Date().getFullYear()} KEFE. Metodoloji korumalıdır.
        </p>
      </div>
    </footer>
  );
}