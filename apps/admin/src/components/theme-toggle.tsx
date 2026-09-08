"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("kefe-admin-theme") as "dark" | "light" | null;
    if (saved) {
      setTheme(saved);
      document.documentElement.setAttribute("data-theme", saved);
    } else {
      const isLight = window.matchMedia("(prefers-color-scheme: light)").matches;
      const initial = isLight ? "light" : "dark";
      setTheme(initial);
      document.documentElement.setAttribute("data-theme", initial);
    }
  }, []);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("kefe-admin-theme", next);
    document.documentElement.setAttribute("data-theme", next);
  };

  if (!mounted) {
    return (
      <button
        type="button"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.45rem",
          minHeight: "2.4rem",
          padding: "0.45rem 0.85rem",
          fontSize: "0.88rem",
          fontWeight: 700,
          border: "1.5px solid var(--line-strong)",
          borderRadius: "0.65rem",
          color: "var(--text)",
          background: "var(--surface-strong)",
        }}
      >
        🌓 Tema
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.45rem",
        minHeight: "2.4rem",
        padding: "0.45rem 0.85rem",
        fontSize: "0.88rem",
        fontWeight: 700,
        border: "1.5px solid var(--gold)",
        borderRadius: "0.65rem",
        color: "var(--gold)",
        background: "var(--surface-strong)",
      }}
      title="Temayı değiştir (Koyu / Açık)"
    >
      <span>{theme === "dark" ? "☀️ Açık Tema" : "🌙 Koyu Tema"}</span>
    </button>
  );
}
