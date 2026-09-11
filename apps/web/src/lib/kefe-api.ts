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

export interface QuestionOption {
  code: string;
  label: string;
}

export interface CaseQuestion {
  question_id: string;
  prompt: string;
  response_type: string;
  required: boolean;
  response_schema: Record<string, unknown>;
  options: QuestionOption[];
}

export interface CaseDetail {
  case_id: string;
  case_version_id: string;
  version_no: number;
  title: string;
  summary: string;
  base_format: string;
  primary_domain: string;
  content_risk: string;
  questions: CaseQuestion[];
}

export async function listPublicCases(
  limit = 20,
  offset = 0,
): Promise<CaseContextSummary[]> {
  return fetchJson<CaseContextSummary[]>(
    `/v1/cases?limit=${limit}&offset=${offset}`,
  );
}

export async function getPublicCase(caseId: string): Promise<CaseDetail> {
  return fetchJson<CaseDetail>(`/v1/cases/${encodeURIComponent(caseId)}`);
}

// ---------------------------------------------------------------------------
// Public Share (share link resolution)
// ---------------------------------------------------------------------------

export interface PublicShare {
  share_id: string;
  case_id: string;
  case_version_id: string;
  title: string;
  summary: string;
  primary_domain: string;
  created_at: string;
  expires_at: string;
}

export async function getPublicShare(token: string): Promise<PublicShare> {
  return fetchJson<PublicShare>(`/v1/shares/${encodeURIComponent(token)}`);
}

// ---------------------------------------------------------------------------
// Case Version History (ADR-0134, CAP-072)
// ---------------------------------------------------------------------------

export interface PublicCaseVersionItem {
  case_version_id: string;
  version_no: number;
  title: string;
  summary: string;
  published_at: string | null;
  /** "CURRENT" for the active published version, "PREVIOUS" for superseded. */
  classification: "CURRENT" | "PREVIOUS";
}

export interface PublicCaseVersionHistory {
  case_id: string;
  items: PublicCaseVersionItem[];
}

/**
 * Fetches the bounded public version history for a case.
 * Returns null when the API returns 404 (case not found / not published).
 * Throws on network or unexpected errors.
 */
export async function getCaseVersionHistory(
  caseId: string,
): Promise<PublicCaseVersionHistory | null> {
  try {
    return await fetchJson<PublicCaseVersionHistory>(
      `/v1/cases/${encodeURIComponent(caseId)}/history`,
    );
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) return null;
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Case Signal Consensus Cards (public — filtered by case_version_id)
// ---------------------------------------------------------------------------

/**
 * Lists signal consensus cards for a specific case version.
 * Returns empty array on 404 (no qualified signals yet).
 */
export async function listCaseSignalCards(
  caseVersionId: string,
): Promise<SignalConsensusCard[]> {
  try {
    return await fetchJson<SignalConsensusCard[]>(
      `/v1/signals/consensus-cards?case_version_id=${encodeURIComponent(caseVersionId)}&limit=10`,
    );
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) return [];
    throw err;
  }
}