"use client";

/**
 * CasesFilter — client-side search + domain filter for the cases list page.
 *
 * Turkish-tolerant normalization mirrors ADR-0141 / ExploreSearchController.
 * Locale: Turkish. No API calls — filters data passed from server component.
 */

import { useMemo, useState } from "react";
import Link from "next/link";

import type { CaseContextSummary } from "@/src/lib/kefe-api";
import styles from "@/src/components/cases-filter.module.css";

const DOMAIN_LABELS: Record<string, string> = {
  GOVERNANCE: "Yönetim",
  ENVIRONMENT: "Çevre",
  SOCIAL: "Sosyal",
  ECONOMY: "Ekonomi",
  HEALTH: "Sağlık",
  EDUCATION: "Eğitim",
  TECHNOLOGY: "Teknoloji",
  CULTURE: "Kültür",
};

function domainLabel(code: string): string {
  return DOMAIN_LABELS[code] ?? code;
}

/** Turkish-tolerant normalization (mirrors ADR-0141). */
function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[İI]/g, "i")
    .replace(/ı/g, "i")
    .replace(/ç/g, "c")
    .replace(/ğ/g, "g")
    .replace(/ö/g, "o")
    .replace(/ş/g, "s")
    .replace(/ü/g, "u")
    .trim()
    .replace(/\s+/g, " ");
}

function matchesQuery(query: string, item: CaseContextSummary): boolean {
  if (!query) return true;
  const normalizedQuery = normalize(query);
  const tokens = normalizedQuery.split(" ").filter(Boolean);
  const haystack = normalize(`${item.title} ${item.summary} ${item.primary_domain_code}`);
  return tokens.every((t) => haystack.includes(t));
}

interface CasesFilterProps {
  cases: CaseContextSummary[];
}

export function CasesFilter({ cases }: CasesFilterProps) {
  const [query, setQuery] = useState("");
  const [selectedDomain, setSelectedDomain] = useState<string>("ALL");

  const domains = useMemo(() => {
    const domainSet = new Set(cases.map((c) => c.primary_domain_code));
    return Array.from(domainSet).sort();
  }, [cases]);

  const filtered = useMemo(() => {
    return cases.filter((c) => {
      const matchesDomain =
        selectedDomain === "ALL" || c.primary_domain_code === selectedDomain;
      return matchesDomain && matchesQuery(query, c);
    });
  }, [cases, query, selectedDomain]);

  const showingAll = filtered.length === cases.length;

  return (
    <div>
      <div className={styles.filterRow}>
        <div className={styles.searchWrapper}>
          <label htmlFor="cases-search" className={styles.srOnly}>
            Mesele ara
          </label>
          <input
            id="cases-search"
            type="search"
            className={styles.searchInput}
            placeholder="Mesele ara…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Mesele ara"
          />
        </div>

        <div className={styles.domainFilter} role="group" aria-label="Alan filtresi">
          <button
            type="button"
            className={`${styles.domainBtn} ${selectedDomain === "ALL" ? styles.domainBtnActive : ""}`}
            onClick={() => setSelectedDomain("ALL")}
            aria-pressed={selectedDomain === "ALL"}
          >
            Tümü
          </button>
          {domains.map((d) => (
            <button
              key={d}
              type="button"
              className={`${styles.domainBtn} ${selectedDomain === d ? styles.domainBtnActive : ""}`}
              onClick={() => setSelectedDomain(d)}
              aria-pressed={selectedDomain === d}
            >
              {domainLabel(d)}
            </button>
          ))}
        </div>

        {!showingAll && (
          <p className={styles.resultCount} aria-live="polite" role="status">
            {filtered.length} / {cases.length} mesele
          </p>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className={styles.emptyState}>
          <p>Arama kriterlerine uyan mesele bulunamadı.</p>
          <button
            type="button"
            className={styles.clearBtn}
            onClick={() => { setQuery(""); setSelectedDomain("ALL"); }}
          >
            Filtreleri temizle
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {filtered.map((c) => (
            <article key={c.case_version_id} className={styles.card}>
              <div className={styles.badgeRow}>
                <span className={styles.domainBadge}>
                  {domainLabel(c.primary_domain_code)}
                </span>
                {c.is_real_event === true && (
                  <span className={styles.realEventBadge} aria-label="Gerçek Olay">
                    Gerçek Olay
                  </span>
                )}
              </div>
              <h2 className={styles.cardTitle}>{c.title}</h2>
              <p className={styles.cardSummary}>{c.summary}</p>
              <div className={styles.cardFooter}>
                <Link
                  href={`/cases/${encodeURIComponent(c.case_id)}`}
                  className={styles.cardLink}
                >
                  İncele →
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}