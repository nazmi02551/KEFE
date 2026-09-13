/**
 * Normalizes human-entered Turkish text for forgiving local search.
 *
 * The Turkish locale step is intentional: plain `toLowerCase()` converts
 * uppercase İ to `i` plus a combining dot, which does not match a plain `i`.
 */
export function normalizeSearchText(text: string): string {
  return text
    .normalize("NFC")
    .toLocaleLowerCase("tr-TR")
    .replace(/ı/g, "i")
    .replace(/ç/g, "c")
    .replace(/ğ/g, "g")
    .replace(/ö/g, "o")
    .replace(/ş/g, "s")
    .replace(/ü/g, "u")
    .trim()
    .replace(/\s+/g, " ");
}

/** Matches every non-empty query token across the supplied searchable fields. */
export function matchesSearchQuery(
  query: string,
  fields: readonly string[],
): boolean {
  const tokens = normalizeSearchText(query).split(" ").filter(Boolean);
  if (tokens.length === 0) return true;

  const haystack = normalizeSearchText(fields.join(" "));
  return tokens.every((token) => haystack.includes(token));
}
