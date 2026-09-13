/** Keeps externally supplied percentage values safe for visual and ARIA output. */
export function clampPercentage(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

/** Converts a normalized zero-to-one ratio into a safe display percentage. */
export function ratioToPercentage(value: number): number {
  return clampPercentage(value * 100);
}

/** Keeps externally supplied count values finite, integral and non-negative. */
export function safeCount(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.trunc(value));
}

/** Allows public outbound links only when they use an ordinary web protocol. */
export function safeExternalHttpUrl(value: string | null | undefined): string | null {
  if (!value) return null;

  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    if (url.username || url.password) return null;
    return url.toString();
  } catch {
    return null;
  }
}

/**
 * Converts request failures into copy that is safe to render on a public page.
 *
 * API error bodies can contain implementation details supplied by upstream
 * services. Keep those details available to diagnostics, but never reflect
 * them into public HTML.
 */
export function publicLoadErrorMessage(error: unknown, fallback: string): string {
  if (
    typeof error === "object"
    && error !== null
    && "status" in error
    && error.status === 429
  ) {
    return "Çok fazla istek gönderildi. Lütfen kısa süre sonra yeniden deneyin.";
  }

  return fallback;
}
