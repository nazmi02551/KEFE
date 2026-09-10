"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

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
  { href: "/signal", label: "Sinyal" },
  { href: "/impact", label: "Etki" },
] as const;

function subscribeTheme(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getThemeSnapshot(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  const saved = localStorage.getItem("kefe-admin-theme");
  return saved === "light" ? "light" : "dark";
}

function getThemeServerSnapshot(): "dark" | "light" {
  return "dark";
}

export function AdminStudioHeader() {
  const pathname = usePathname();
  const theme = useSyncExternalStore(subscribeTheme, getThemeSnapshot, getThemeServerSnapshot);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    localStorage.setItem("kefe-admin-theme", next);
    window.dispatchEvent(new Event("storage"));
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
                aria-current={isActive ? "page" : undefined}
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
            suppressHydrationWarning
          >
            {theme === "dark" ? "☀️ Açık Tema" : "🌙 Koyu Tema"}
          </button>
        </div>
      </div>
    </header>
  );
}
