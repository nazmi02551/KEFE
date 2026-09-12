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
// Signal Detail (public — health + qualification)
// ---------------------------------------------------------------------------

export interface SignalHealthDimension {
  dimension_id: string;
  title_tr: string;
  title_en: string;
  score: number;
  threshold: number;
  is_passed: boolean;
  detail: string;
}

export interface SignalHealthReport {
  signal_id: string;
  case_version_id: string;
  overall_qualification: string;
  overall_health_score: number;
  sample_size: number;
  dimensions: SignalHealthDimension[];
  certified_at: string;
  methodology_hash: string;
}

export interface SignalQualificationCriterion {
  criterion_id: string;
  name_tr: string;
  name_en: string;
  score: number;
  threshold: number;
  is_passed: boolean;
  audit_note: string;
}

export interface SignalQualificationReport {
  signal_id: string;
  case_version_id: string;
  case_title: string;
  qualification_status: string;
  qualification_tier: string;
  overall_score: number;
  sample_size: number;
  criteria: SignalQualificationCriterion[];
  eligible_channels: string[];
  certified_at: string;
  qualification_audit_hash: string;
}

export async function getSignalHealth(
  signalId: string,
): Promise<SignalHealthReport | null> {
  try {
    return await fetchJson<SignalHealthReport>(
      `/v1/signals/${encodeURIComponent(signalId)}/health`,
    );
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) return null;
    throw err;
  }
}

export async function getSignalQualification(
  signalId: string,
): Promise<SignalQualificationReport | null> {
  try {
    return await fetchJson<SignalQualificationReport>(
      `/v1/signals/${encodeURIComponent(signalId)}/qualification`,
    );
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) return null;
    throw err;
  }
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
  /** true only when the backend explicitly returns boolean true (ADR-0133). */
  is_real_event?: boolean;
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
  /** true only when the backend explicitly returns boolean true (ADR-0133). */
  is_real_event?: boolean;
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

// ---------------------------------------------------------------------------
// Case Context (public read — Commit First isolated, no result/perspective)
// CAP-069, CAP-070, ADR-0142
// ---------------------------------------------------------------------------

export interface ContextSource {
  source_id: string;
  title: string;
  publisher: string;
  source_kind: string;
  url: string | null;
  published_at: string | null;
}

export interface ContextBlock {
  context_block_id: string;
  display_order: number;
  disclosure_level: string;
  title: string;
  body: string;
  claim_status: string;
  source_ids: string[];
}

export interface CaseContextSnapshot {
  case_version_id: string;
  blocks: ContextBlock[];
  sources: ContextSource[];
}

/**
 * Fetches context blocks for a case version.
 * Returns null on 404. Commit First: response never contains result/perspective.
 */
export async function getCaseContext(
  caseVersionId: string,
): Promise<CaseContextSnapshot | null> {
  try {
    return await fetchJson<CaseContextSnapshot>(
      `/v1/case-versions/${encodeURIComponent(caseVersionId)}/context`,
    );
  } catch (err) {
    if (err instanceof KefApiError && err.status === 404) return null;
    throw err;
  }
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

// ---------------------------------------------------------------------------
// Impact — public institution responses and action milestones (CAP-048..054)
// ---------------------------------------------------------------------------

export interface InstitutionResponsePublic {
  response_id: string;
  case_version_id: string;
  institution_name: string;
  authority_role: string;
  verification_status: string;
  response_type: string;
  statement: string;
  published_at: string;
  milestone_date: string | null;
}

export interface ActionMilestonePublic {
  action_id: string;
  case_version_id: string;
  title: string;
  description: string;
  status: string;
  progress_percentage: number;
  created_at: string;
  institution_response_id: string | null;
  target_completion_date: string | null;
  evidence_summary: string | null;
  evidence_url: string | null;
}

export async function listInstitutionResponses(
  caseVersionId?: string,
): Promise<InstitutionResponsePublic[]> {
  const qs = caseVersionId
    ? `?case_version_id=${encodeURIComponent(caseVersionId)}`
    : "";
  return fetchJson<InstitutionResponsePublic[]>(`/v1/impact/institution-responses${qs}`);
}

export async function listActionMilestones(
  caseVersionId?: string,
): Promise<ActionMilestonePublic[]> {
  const qs = caseVersionId
    ? `?case_version_id=${encodeURIComponent(caseVersionId)}`
    : "";
  return fetchJson<ActionMilestonePublic[]>(`/v1/impact/actions${qs}`);
}