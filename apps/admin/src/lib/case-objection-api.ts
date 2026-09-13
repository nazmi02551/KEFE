import type { AdminSession } from "@/src/lib/contracts";

export type ObjectionReasonCategory =
  | "EDITORIAL_BIAS_FRAMING"
  | "FACTUAL_INACCURACY"
  | "EXCLUDED_STAKEHOLDER"
  | "AMBIGUOUS_OPTIONS"
  | "DEPRECIATED_CONTEXT";

export type ObjectionStatus =
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "ACCEPTED_CORRECTION_FILED"
  | "REJECTED_WITH_REASON";

export interface CaseObjectionItem {
  objection_id: string;
  case_version_id: string;
  reason_category: ObjectionReasonCategory;
  statement: string;
  supporting_evidence_url: string | null;
  status: ObjectionStatus;
  created_at: string;
  resolution_note: string | null;
  resolved_at: string | null;
}

export interface CaseObjectionDecisionRequest {
  objection_id: string;
  decision: "ACCEPT_AND_FILE_CORRECTION" | "REJECT_WITH_REASON";
  resolution_note: string;
  csrf_token: string;
}

export interface CaseObjectionDecisionResponse {
  objection_id: string;
  status: ObjectionStatus;
  resolution_note: string;
  resolved_at: string;
  audit_hash: string;
}

export class CaseObjectionApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "CaseObjectionApiError";
    this.code = code;
    this.status = status;
  }
}

export interface CaseObjectionApiOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new CaseObjectionApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new CaseObjectionApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new CaseObjectionApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

export class CaseObjectionApiClient {
  readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CaseObjectionApiOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.csrfToken = options.csrfToken?.trim() || undefined;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async listObjections(caseVersionId: string): Promise<CaseObjectionItem[]> {
    const url = `${this.baseUrl}/v1/cases/${encodeURIComponent(caseVersionId)}/objections`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new CaseObjectionApiError(
        "OBJECTIONS_FETCH_FAILED",
        `Failed to fetch objections: HTTP ${response.status}`,
        response.status
      );
    }
    const data = await response.json();
    return Array.isArray(data) ? data : (data.objections ?? []);
  }

  async decideObjection(
    caseVersionId: string,
    request: CaseObjectionDecisionRequest
  ): Promise<CaseObjectionDecisionResponse> {
    const csrf = request.csrf_token || this.csrfToken;
    if (!csrf) {
      throw new CaseObjectionApiError(
        "CSRF_TOKEN_REQUIRED",
        "A valid CSRF token is required for objection review decisions",
        403
      );
    }
    if (!request.resolution_note || request.resolution_note.trim().length < 10) {
      throw new CaseObjectionApiError(
        "RESOLUTION_NOTE_TOO_SHORT",
        "Resolution note must be at least 10 characters long",
        400
      );
    }

    const url = `${this.baseUrl}/v1/cases/${encodeURIComponent(caseVersionId)}/objections/${encodeURIComponent(request.objection_id)}/decision`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRF-Token": csrf,
      },
      body: JSON.stringify({
        decision: request.decision,
        resolution_note: request.resolution_note.trim(),
      }),
    });

    if (!response.ok) {
      throw new CaseObjectionApiError(
        "OBJECTION_DECISION_FAILED",
        `Failed to submit objection decision: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }
}
