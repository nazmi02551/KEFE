"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import styles from "./admin-studio-header.module.css";

const navItems = [
  { href: "/", label: "Editoryal Merkez" },
  { href: "/case-builder", label: "Vaka Oluşturucu" },
  { href: "/content-review", label: "İçerik İnceleme" },
  { href: "/flow-composer", label: "Akış Bestecisi" },
  { href: "/publication-operations", label: "Yayın Operasyonları" },
  { href: "/reason-moderation", label: "Moderasyon" },
  { href: "/operational-reports", label: "Raporlar" },
  { href: "/case-media", label: "Medya" },
] as const;

export function AdminStudioHeader() {
  const pathname = usePathname();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("kefe-admin-theme") as "dark" | "light" | null;
      if (saved === "light" || saved === "dark") return saved;
    }
    return "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("kefe-admin-theme", next);
  };

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brandArea}>
          <span className={styles.brandLogo}>
            <span style={{ color: "var(--gold)" }}>⚖️</span> KEFE Studio
          </span>
          <span className={styles.brandBadge}>Yönetim</span>
        </Link>

        <nav className={styles.nav} aria-label="Admin Studio Ana Menü">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navLink} ${isActive ? styles.navLinkActive : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className={styles.actions}>
          <button
            type="button"
            onClick={toggleTheme}
            className={styles.themeBtn}
            title="Temayı değiştir (Koyu / Açık)"
          >
            {theme === "dark" ? "☀️ Açık Tema" : "🌙 Koyu Tema"}
          </button>
        </div>
      </div>
    </header>
  );
}
