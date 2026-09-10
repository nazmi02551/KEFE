/**
 * KEFE Web — Public API Client
 *
 * Typed client for public KEFE API endpoints consumed by the web application.
 * Server-side calls use KEFE_API_BASE_URL.
 * Client-side calls use NEXT_PUBLIC_KEFE_API_BASE_URL.
 *
 * Invariants:
 * - Only public (non-admin, non-internal) endpoints are exposed here.
 * - Bearer token is NOT used by the web app for public read endpoints.
 * - Consensus statements with [PROVISIONAL] must never be rendered on public pages
 *   (the API already filters them, but the client must not bypass this).
 */

export class KefApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "KefApiError";
  }
}

function apiBase(): string {
  // Server-side: use KEFE_API_BASE_URL (not exposed to browser)
  // Client-side: use NEXT_PUBLIC_KEFE_API_BASE_URL
  if (typeof window === "undefined") {
    return process.env.KEFE_API_BASE_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "http://localhost:8000";
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
    cache: options?.cache ?? "no-store",
  });

  if (!res.ok) {
    let code = "API_ERROR";
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json() as Record<string, unknown>;
      const err = (body.error ?? body) as Record<string, unknown>;
      if (typeof err.code === "string") code = err.code;
      if (typeof err.message === "string") message = err.message;
    } catch {
      // ignore parse error
    }
    throw new KefApiError(code, message, res.status);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Signal Consensus Cards (public)
// ---------------------------------------------------------------------------

export interface SignalConsensusCard {
  signal_id: string;
  case_version_id: string;
  case_title: string;
  consensus_statement: string;
  agreement_percentage: number;
  sample_size: number;
  confidence_tier: string;
  certified_at: string;
  qualification_tier: string;
}

export async function listSignalConsensusCards(
  limit = 20,
  offset = 0,
): Promise<SignalConsensusCard[]> {
  return fetchJson<SignalConsensusCard[]>(
    `/v1/signals/consensus-cards?limit=${limit}&offset=${offset}`,
  );
}

// ---------------------------------------------------------------------------
// Cases / Context (public read)
// ---------------------------------------------------------------------------

export interface CaseContextSummary {
  case_id: string;
  case_version_id: string;
  title: string;
  summary: string;
  primary_domain_code: string;
}

export async function listPublicCases(
  limit = 20,
  offset = 0,
): Promise<CaseContextSummary[]> {
  return fetchJson<CaseContextSummary[]>(
    `/v1/context?limit=${limit}&offset=${offset}`,
  );
}

export async function getPublicCase(caseId: string): Promise<CaseContextSummary> {
  return fetchJson<CaseContextSummary>(`/v1/context/${encodeURIComponent(caseId)}`);
}