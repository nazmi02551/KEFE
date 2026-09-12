"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "@/src/components/site-header.module.css";

const NAV_LINKS = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/signal", label: "Sinyaller" },
  { href: "/cases", label: "Meseleler" },
  { href: "/impact", label: "Etki" },
  { href: "/about", label: "Metodoloji" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/" className={styles.logoLink} aria-label="KEFE Ana Sayfa">
          <span className={styles.logo}>KEFE</span>
        </Link>

        <nav className={styles.nav} aria-label="Ana navigasyon">
          <ul className={styles.navList} role="list">
            {NAV_LINKS.map(({ href, label }) => {
              const isActive =
                href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className={`${styles.navLink} ${isActive ? styles.navLinkActive : ""}`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}