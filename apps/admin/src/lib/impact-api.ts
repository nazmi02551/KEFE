/**
 * Admin Studio — Impact API client
 *
 * Wraps /v1/impact/* endpoints.
 * Institution responses are read-only in Admin Studio (write path is via
 * authority-verified external ingestion).
 * Action milestones can be proposed and updated via Admin Studio.
 *
 * Invariants:
 * - Only VERIFIED responses are shown in public-facing surfaces.
 * - Collective Result is not Impact; Signal must precede Impact per F6 gates.
 * - Action progress evidence_url must be a valid HTTPS URL.
 */

import { AdminApiError } from "@/src/lib/admin-api";

export interface InstitutionResponse {
  response_id: string;
  case_version_id: string;
  institution_name: string;
  authority_role: string;
  verification_status: "VERIFIED" | "PENDING_VERIFICATION" | "REJECTED";
  response_type:
    | "ACKNOWLEDGE"
    | "COMMITMENT"
    | "POLICY_CHANGE"
    | "FACTUAL_CLARIFICATION"
    | "DECLINE_WITH_REASON";
  statement: string;
  published_at: string;
  milestone_date: string | null;
}

export interface ActionMilestone {
  action_id: string;
  case_version_id: string;
  title: string;
  description: string;
  status: "PROPOSED" | "IN_PROGRESS" | "VERIFIED_COMPLETE" | "STALLED";
  progress_percentage: number;
  created_at: string;
  institution_response_id: string | null;
  target_completion_date: string | null;
  evidence_summary: string | null;
  evidence_url: string | null;
}

export interface ProposeActionInput {
  case_version_id: string;
  title: string;
  description: string;
  institution_response_id?: string | null;
  target_completion_date?: string | null;
}

export interface UpdateActionProgressInput {
  case_version_id: string;
  progress_percentage: number;
  status: ActionMilestone["status"];
  evidence_summary?: string | null;
  evidence_url?: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(url: string, fetchImpl: typeof fetch = fetch): Promise<T> {
  const res = await fetchImpl(url);
  if (!res.ok) {
    let code = "IMPACT_API_ERROR";
    let message = `Impact API error: ${res.status}`;
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

async function apiMutate<T>(
  url: string,
  method: "POST" | "PATCH",
  body: unknown,
  csrfToken: string,
  fetchImpl: typeof fetch = fetch
): Promise<T> {
  const res = await fetchImpl(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let code = "IMPACT_API_MUTATE_ERROR";
    let message = `Impact API mutation error: ${res.status}`;
    try {
      const respBody = await res.json();
      if (respBody?.detail) message = respBody.detail;
      if (respBody?.code) code = respBody.code;
    } catch {
      // Ignore parse errors
    }
    throw new AdminApiError(code, message, res.status);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Institution Responses (read-only in Admin Studio)
// ---------------------------------------------------------------------------

export async function listInstitutionResponses(
  baseUrl: string,
  options: {
    caseVersionId?: string;
    limit?: number;
    offset?: number;
    fetchImpl?: typeof fetch;
  } = {}
): Promise<InstitutionResponse[]> {
  const { caseVersionId, limit = 50, offset = 0, fetchImpl } = options;
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (caseVersionId) {
    params.set("case_version_id", caseVersionId);
  }
  return apiFetch<InstitutionResponse[]>(
    `${baseUrl}/v1/impact/institution-responses?${params.toString()}`,
    fetchImpl
  );
}

// ---------------------------------------------------------------------------
// Action Milestones
// ---------------------------------------------------------------------------

export async function listActionMilestones(
  baseUrl: string,
  options: {
    caseVersionId?: string;
    limit?: number;
    offset?: number;
    fetchImpl?: typeof fetch;
  } = {}
): Promise<ActionMilestone[]> {
  const { caseVersionId, limit = 50, offset = 0, fetchImpl } = options;
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (caseVersionId) {
    params.set("case_version_id", caseVersionId);
  }
  return apiFetch<ActionMilestone[]>(
    `${baseUrl}/v1/impact/actions?${params.toString()}`,
    fetchImpl
  );
}

export async function proposeAction(
  baseUrl: string,
  input: ProposeActionInput,
  csrfToken: string,
  fetchImpl?: typeof fetch
): Promise<ActionMilestone> {
  return apiMutate<ActionMilestone>(
    `${baseUrl}/v1/impact/actions`,
    "POST",
    input,
    csrfToken,
    fetchImpl
  );
}

export async function updateActionProgress(
  baseUrl: string,
  actionId: string,
  input: UpdateActionProgressInput,
  csrfToken: string,
  fetchImpl?: typeof fetch
): Promise<ActionMilestone> {
  return apiMutate<ActionMilestone>(
    `${baseUrl}/v1/impact/actions/${actionId}/progress`,
    "PATCH",
    input,
    csrfToken,
    fetchImpl
  );
}