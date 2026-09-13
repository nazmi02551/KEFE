export type CorrectionType =
  | "FACTUAL_UPDATE"
  | "CLARIFICATION"
  | "SOURCE_EXPANSION"
  | "TYPO_FIX"
  | "LEGAL_STATUS_UPDATE";

export type CorrectionSeverity = "MINOR" | "MATERIAL" | "SUBSTANTIAL";

export interface CaseCorrectionEntry {
  correction_id: string;
  correction_type: CorrectionType;
  severity: CorrectionSeverity;
  summary: string;
  editorial_rationale: string;
  timestamp: string;
  target_field?: string | null;
  previous_value?: string | null;
  corrected_value?: string | null;
}

export interface CaseCorrectionHistory {
  case_version_id: string;
  corrections: CaseCorrectionEntry[];
}

export interface AddCorrectionRequest {
  correction_type: CorrectionType;
  severity: CorrectionSeverity;
  summary: string;
  editorial_rationale: string;
  target_field?: string;
  previous_value?: string;
  corrected_value?: string;
  csrf_token: string;
}

export class CaseCorrectionApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "CaseCorrectionApiError";
    this.code = code;
    this.status = status;
  }
}

export interface CaseCorrectionApiOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new CaseCorrectionApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new CaseCorrectionApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new CaseCorrectionApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

export class CaseCorrectionApiClient {
  readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CaseCorrectionApiOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.csrfToken = options.csrfToken?.trim() || undefined;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async getCorrectionHistory(caseVersionId: string): Promise<CaseCorrectionHistory> {
    const url = `${this.baseUrl}/v1/cases/${encodeURIComponent(caseVersionId)}/corrections`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new CaseCorrectionApiError(
        "CORRECTIONS_FETCH_FAILED",
        `Failed to fetch correction history: HTTP ${response.status}`,
        response.status
      );
    }
    const data = await response.json();
    return {
      case_version_id: data.case_version_id ?? caseVersionId,
      corrections: data.corrections ?? [],
    };
  }

  async addCorrection(
    caseVersionId: string,
    request: AddCorrectionRequest
  ): Promise<CaseCorrectionEntry> {
    const csrf = request.csrf_token || this.csrfToken;
    if (!csrf) {
      throw new CaseCorrectionApiError(
        "CSRF_TOKEN_REQUIRED",
        "A valid CSRF token is required to append a case correction",
        403
      );
    }
    if (!request.summary || request.summary.trim().length < 5) {
      throw new CaseCorrectionApiError(
        "SUMMARY_TOO_SHORT",
        "Correction summary must be at least 5 characters long",
        400
      );
    }
    if (!request.editorial_rationale || request.editorial_rationale.trim().length < 10) {
      throw new CaseCorrectionApiError(
        "RATIONALE_TOO_SHORT",
        "Editorial rationale must be at least 10 characters long",
        400
      );
    }

    const url = `${this.baseUrl}/v1/cases/${encodeURIComponent(caseVersionId)}/corrections`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRF-Token": csrf,
      },
      body: JSON.stringify({
        correction_type: request.correction_type,
        severity: request.severity,
        summary: request.summary.trim(),
        editorial_rationale: request.editorial_rationale.trim(),
        target_field: request.target_field || null,
        previous_value: request.previous_value || null,
        corrected_value: request.corrected_value || null,
      }),
    });

    if (!response.ok) {
      throw new CaseCorrectionApiError(
        "ADD_CORRECTION_FAILED",
        `Failed to append correction: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }
}
