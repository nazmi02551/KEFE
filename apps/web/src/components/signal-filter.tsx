"use client";

/**
 * SignalFilter — client-side tier filter + search for the signal list page.
 * Turkish-tolerant normalization mirrors ADR-0141.
 */

import { useMemo, useState } from "react";
import Link from "next/link";

import type { SignalConsensusCard } from "@/src/lib/kefe-api";
import styles from "@/src/components/signal-filter.module.css";

const TIER_LABELS: Record<string, string> = {
  GOLD_STANDARD: "Altın Standart",
  SILVER_VALIDATED: "Gümüş Doğrulanmış",
  BRONZE_OBSERVED: "Bronz Gözlemlendi",
  UNQUALIFIED: "Nitelenmemiş",
};

const TIER_ORDER = ["GOLD_STANDARD", "SILVER_VALIDATED", "BRONZE_OBSERVED", "UNQUALIFIED"];

/** Turkish-tolerant normalization (ADR-0141). */
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

function matchesQuery(query: string, card: SignalConsensusCard): boolean {
  if (!query) return true;
  const tokens = normalize(query).split(" ").filter(Boolean);
  const haystack = normalize(`${card.case_title} ${card.consensus_statement}`);
  return tokens.every((t) => haystack.includes(t));
}

function tierColorVar(tier: string): string {
  switch (tier) {
    case "GOLD_STANDARD":
      return "var(--kefe-signal-tier-gold-standard, #c9a227)";
    case "SILVER_VALIDATED":
      return "var(--kefe-signal-tier-silver-validated, #8ca3b5)";
    case "BRONZE_OBSERVED":
      return "var(--kefe-signal-tier-bronze-observed, #b07c50)";
    default:
      return "var(--kefe-color-muted)";
  }
}

interface SignalFilterProps {
  cards: SignalConsensusCard[];
}

export function SignalFilter({ cards }: SignalFilterProps) {
  const [query, setQuery] = useState("");
  const [selectedTier, setSelectedTier] = useState<string>("ALL");

  const tiers = useMemo(() => {
    const tierSet = new Set(cards.map((c) => c.qualification_tier));
    return TIER_ORDER.filter((t) => tierSet.has(t));
  }, [cards]);

  const filtered = useMemo(() => {
    return cards.filter((c) => {
      const matchesTier =
        selectedTier === "ALL" || c.qualification_tier === selectedTier;
      return matchesTier && matchesQuery(query, c);
    });
  }, [cards, query, selectedTier]);

  const showingAll = filtered.length === cards.length;

  return (
    <div>
      <div className={styles.filterRow}>
        <div className={styles.searchWrapper}>
          <label htmlFor="signal-search" className={styles.srOnly}>
            Sinyal ara
          </label>
          <input
            id="signal-search"
            type="search"
            className={styles.searchInput}
            placeholder="Sinyal ara…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Sinyal ara"
          />
        </div>

        {tiers.length > 1 && (
          <div className={styles.tierFilter} role="group" aria-label="Tier filtresi">
            <button
              type="button"
              className={`${styles.tierBtn} ${selectedTier === "ALL" ? styles.tierBtnActive : ""}`}
              onClick={() => setSelectedTier("ALL")}
              aria-pressed={selectedTier === "ALL"}
            >
              Tümü
            </button>
            {tiers.map((t) => (
              <button
                key={t}
                type="button"
                className={`${styles.tierBtn} ${selectedTier === t ? styles.tierBtnActive : ""}`}
                onClick={() => setSelectedTier(t)}
                aria-pressed={selectedTier === t}
                style={selectedTier === t ? { borderColor: tierColorVar(t), color: tierColorVar(t) } : undefined}
              >
                {TIER_LABELS[t] ?? t}
              </button>
            ))}
          </div>
        )}

        {!showingAll && (
          <p className={styles.resultCount} aria-live="polite" role="status">
            {filtered.length} / {cards.length} sinyal
          </p>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className={styles.emptyState}>
          <p>Arama kriterlerine uyan sinyal bulunamadı.</p>
          <button
            type="button"
            className={styles.clearBtn}
            onClick={() => { setQuery(""); setSelectedTier("ALL"); }}
          >
            Filtreleri temizle
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {filtered.map((card) => (
            <article key={card.signal_id} className={styles.card}>
              <header className={styles.cardHeader}>
                <span
                  className={styles.tierBadge}
                  style={{ color: tierColorVar(card.qualification_tier) }}
                >
                  {TIER_LABELS[card.qualification_tier] ?? card.qualification_tier}
                </span>
                <span className={styles.agreementPct}>
                  %{Math.round(card.agreement_percentage)}
                </span>
              </header>
              <h2 className={styles.cardTitle}>{card.case_title}</h2>
              <p className={styles.cardStatement}>{card.consensus_statement}</p>
              <footer className={styles.cardFooter}>
                <span className={styles.sampleSize}>
                  {card.sample_size.toLocaleString("tr-TR")} katılımcı
                </span>
                <time
                  className={styles.certifiedAt}
                  dateTime={card.certified_at}
                >
                  {new Date(card.certified_at).toLocaleDateString("tr-TR", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </time>
              </footer>
              <Link
                href={`/signal/${encodeURIComponent(card.signal_id)}`}
                className={styles.detailLink}
              >
                Sinyal Detayı →
              </Link>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}