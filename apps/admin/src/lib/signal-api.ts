/**
 * Admin Studio — Signal API client
 *
 * Wraps /v1/signals/* endpoints.
 * All signal data is read-only from Admin Studio; signals are computed
 * from the live decision pipeline, not entered manually.
 *
 * Invariants:
 * - UNQUALIFIED signals are excluded from public display but visible in Admin.
 * - sample_size reflects only CORE_PRE_RESULT (Commit-First) contributions.
 * - Collective Result is not automatically Signal, truth or authority.
 */

import { AdminApiError } from "@/src/lib/admin-api";

export interface SignalConsensusCard {
  signal_id: string;
  case_version_id: string;
  case_title: string;
  consensus_statement: string;
  agreement_percentage: number;
  sample_size: number;
  confidence_tier: "GOLD_STANDARD" | "SILVER_VALIDATED" | "BRONZE_OBSERVED" | "UNQUALIFIED";
  certified_at: string;
  qualification_tier: string;
}

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

export interface ContributionClassSummary {
  class_id: string;
  name_tr: string;
  name_en: string;
  count: number;
  percentage: number;
  is_signal_eligible: boolean;
  description: string;
}

export interface ContributionClassesReport {
  case_version_id: string;
  total_contributions: number;
  classes: ContributionClassSummary[];
  contamination_risk_index: number;
  isolation_audit_status: string;
  certified_at: string;
  isolation_proof_hash: string;
}

export interface SignalScopeAlignmentReport {
  signal_id: string;
  case_version_id: string;
  jurisdiction_level: string;
  target_population: string;
  geographic_scope: string;
  alignment_status: string;
  overall_alignment_score: number;
  dimensions: Array<{
    dimension: string;
    declared_scope: string;
    sample_scope: string;
    alignment_score: number;
    is_valid: boolean;
  }>;
  validity_window_days: number;
  certified_at: string;
  scope_seal_hash: string;
}

export interface SignalVersioningReport {
  signal_id: string;
  case_version_id: string;
  current_version: string;
  current_methodology_hash: string;
  snapshots: Array<{
    snapshot_id: string;
    methodology_version: string;
    methodology_name: string;
    sample_size: number;
    confidence_score: number;
    consensus_distribution: Record<string, number>;
    calculated_at: string;
    parent_snapshot_hash: string | null;
    snapshot_hash: string;
  }>;
  latest_delta: {
    from_version: string;
    to_version: string;
    distribution_shift: number;
    confidence_delta: number;
    notes: string;
  } | null;
  audit_chain_valid: boolean;
  certified_at: string;
}

export interface SignalTargetRegistryReport {
  signal_id: string;
  case_version_id: string;
  primary_target_id: string;
  targets: Array<{
    target_id: string;
    target_name: string;
    target_type: string;
    jurisdiction_level: string;
    official_contact_channel: string;
    dispatch_status: string;
    response_due_days: number;
    dispatched_at: string | null;
    acknowledged_at: string | null;
  }>;
  certified_at: string;
  registry_proof_hash: string;
}

// ---------------------------------------------------------------------------
// API client functions
// ---------------------------------------------------------------------------

async function apiFetch<T>(url: string, fetchImpl: typeof fetch = fetch): Promise<T> {
  const res = await fetchImpl(url);
  if (!res.ok) {
    let code = "SIGNAL_API_ERROR";
    let message = `Signal API error: ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) message = body.detail;
      if (body?.code) code = body.code;
    } catch {
      // Ignore parse errors
    }
    throw new AdminApiError(code, message, res.status);
  }
  return res.json() as Promise<T>;
}

export async function listSignalConsensusCards(
  baseUrl: string,
  options: { limit?: number; offset?: number; fetchImpl?: typeof fetch } = {}
): Promise<SignalConsensusCard[]> {
  const { limit = 20, offset = 0, fetchImpl } = options;
  const url = `${baseUrl}/v1/signals/consensus-cards?limit=${limit}&offset=${offset}`;
  return apiFetch<SignalConsensusCard[]>(url, fetchImpl);
}

export async function getSignalHealthReport(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<SignalHealthReport> {
  return apiFetch<SignalHealthReport>(`${baseUrl}/v1/signals/${signalId}/health`, fetchImpl);
}

export async function getSignalQualificationReport(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<SignalQualificationReport> {
  return apiFetch<SignalQualificationReport>(
    `${baseUrl}/v1/signals/${signalId}/qualification`,
    fetchImpl
  );
}

export async function getContributionClassesReport(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<ContributionClassesReport> {
  return apiFetch<ContributionClassesReport>(
    `${baseUrl}/v1/signals/${signalId}/contribution-classes`,
    fetchImpl
  );
}

export async function getSignalScopeAlignmentReport(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<SignalScopeAlignmentReport> {
  return apiFetch<SignalScopeAlignmentReport>(
    `${baseUrl}/v1/signals/${signalId}/scope-alignment`,
    fetchImpl
  );
}

export async function getSignalVersioningReport(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<SignalVersioningReport> {
  return apiFetch<SignalVersioningReport>(
    `${baseUrl}/v1/signals/${signalId}/versioning`,
    fetchImpl
  );
}

export async function getSignalTargetRegistry(
  baseUrl: string,
  signalId: string,
  fetchImpl?: typeof fetch
): Promise<SignalTargetRegistryReport> {
  return apiFetch<SignalTargetRegistryReport>(
    `${baseUrl}/v1/signals/${signalId}/targets`,
    fetchImpl
  );
}