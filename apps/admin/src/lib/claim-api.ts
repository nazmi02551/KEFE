export type ClaimType = "FACTUAL" | "NORMATIVE" | "VALUE" | "CAUSAL";

export type ClaimState =
  | "CLAIMED"
  | "CONTESTED"
  | "SUPPORTED"
  | "REFUTED"
  | "UNVERIFIABLE";

export type ReviewState =
  | "PROPOSED"
  | "UNDER_REVIEW"
  | "ACCEPTED"
  | "REJECTED";

export type ArgumentRelationKind =
  | "SUPPORTS"
  | "ATTACKS"
  | "REBUTS"
  | "UNDERCUTS"
  | "UNDERMINES"
  | "QUALIFIES";

export type ArgumentTargetKind = "CLAIM" | "ARGUMENT";

export interface ClaimAssessmentItem {
  id: string;
  claim_id: string;
  claim_type: ClaimType;
  claim_state: ClaimState;
  taxonomy_version: string;
  review_state: ReviewState;
  assessed_at: string;
  methodology_version?: string | null;
  reviewer_ref?: string | null;
  rationale_code?: string | null;
  provenance_ref?: string | null;
}

export interface ClaimAssertionItem {
  id: string;
  claim_id: string;
  claimant_kind: string;
  claimant_ref: string;
  asserted_at: string;
  source_artifact_id?: string | null;
  normalized_artifact_id?: string | null;
  provenance_ref?: string | null;
}

export interface ClaimEvidenceLinkItem {
  id: string;
  claim_id: string;
  target_kind: string;
  target_id: string;
  relation: string;
  review_state: string;
  provenance_ref: string;
  created_at: string;
}

export interface ClaimRelationItem {
  id: string;
  from_claim_id: string;
  to_claim_id: string;
  relation_code: string;
  taxonomy_version: string;
  review_state: ReviewState;
  provenance_ref: string;
  created_at: string;
}

export interface ClaimItem {
  id: string;
  normalized_text: string;
  language_code: string;
  created_at: string;
  assessments?: ClaimAssessmentItem[];
  assertions?: ClaimAssertionItem[];
  evidence_links?: ClaimEvidenceLinkItem[];
  relations?: ClaimRelationItem[];
}

export interface ArgumentRelationItem {
  id: string;
  argument_id: string;
  target_kind: ArgumentTargetKind;
  target_ref: string;
  relation: ArgumentRelationKind;
  taxonomy_version: string;
  review_state: ReviewState;
  created_at: string;
}

export interface ArgumentItem {
  id: string;
  body: string;
  language_code: string;
  review_state: ReviewState;
  created_at: string;
  author_or_claimant_ref?: string | null;
  provenance_ref?: string | null;
  relations?: ArgumentRelationItem[];
}

export interface CreateClaimRequest {
  normalized_text: string;
  language_code?: string;
}

export interface CreateClaimAssessmentRequest {
  claim_type: ClaimType;
  claim_state: ClaimState;
  taxonomy_version?: string;
  review_state?: ReviewState;
  methodology_version?: string;
  reviewer_ref?: string;
  rationale_code?: string;
  provenance_ref?: string;
}

export interface CreateClaimAssertionRequest {
  claimant_kind: string;
  claimant_ref: string;
  source_artifact_id?: string;
  normalized_artifact_id?: string;
  provenance_ref?: string;
}

export interface CreateClaimRelationRequest {
  to_claim_id: string;
  relation_code: string;
  taxonomy_version?: string;
  review_state?: ReviewState;
  provenance_ref?: string;
}

export interface CreateArgumentRequest {
  body: string;
  language_code?: string;
  review_state?: ReviewState;
  author_or_claimant_ref?: string;
  provenance_ref?: string;
}

export interface CreateArgumentRelationRequest {
  target_kind: ArgumentTargetKind;
  target_ref: string;
  relation: ArgumentRelationKind;
  taxonomy_version?: string;
  review_state?: ReviewState;
  provenance_ref?: string;
}

export class ClaimApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ClaimApiError";
    this.code = code;
    this.status = status;
  }
}

export interface ClaimApiOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new ClaimApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new ClaimApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new ClaimApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

export class ClaimApiClient {
  readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: ClaimApiOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.csrfToken = options.csrfToken?.trim() || undefined;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private authHeaders(includeCsrf = false): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (includeCsrf && this.csrfToken) {
      headers["X-CSRF-Token"] = this.csrfToken;
    }
    return headers;
  }

  async createClaim(request: CreateClaimRequest): Promise<ClaimItem> {
    if (!request.normalized_text || request.normalized_text.trim().length < 3) {
      throw new ClaimApiError(
        "INVALID_CLAIM_TEXT",
        "Claim normalized text must be at least 3 characters",
        400
      );
    }

    const url = `${this.baseUrl}/v1/claims`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        normalized_text: request.normalized_text.trim(),
        language_code: (request.language_code ?? "tr").trim(),
      }),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_CREATION_FAILED",
        `Failed to create claim: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async getClaim(claimId: string): Promise<ClaimItem> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_NOT_FOUND",
        `Failed to retrieve claim: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async addClaimAssessment(
    claimId: string,
    request: CreateClaimAssessmentRequest
  ): Promise<ClaimAssessmentItem> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/assessments`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_ASSESSMENT_FAILED",
        `Failed to add claim assessment: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async listClaimAssessments(claimId: string): Promise<ClaimAssessmentItem[]> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/assessments`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_ASSESSMENTS_FETCH_FAILED",
        `Failed to fetch claim assessments: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async addClaimAssertion(
    claimId: string,
    request: CreateClaimAssertionRequest
  ): Promise<ClaimAssertionItem> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/assertions`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_ASSERTION_FAILED",
        `Failed to add claim assertion: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async listClaimAssertions(claimId: string): Promise<ClaimAssertionItem[]> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/assertions`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_ASSERTIONS_FETCH_FAILED",
        `Failed to fetch claim assertions: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async addClaimRelation(
    fromClaimId: string,
    request: CreateClaimRelationRequest
  ): Promise<ClaimRelationItem> {
    if (fromClaimId === request.to_claim_id) {
      throw new ClaimApiError(
        "SELF_RELATION_FORBIDDEN",
        "A claim cannot relate to itself",
        400
      );
    }

    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(fromClaimId)}/relations`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_RELATION_FAILED",
        `Failed to add claim relation: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async listClaimRelations(claimId: string): Promise<ClaimRelationItem[]> {
    const url = `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/relations`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "CLAIM_RELATIONS_FETCH_FAILED",
        `Failed to fetch claim relations: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async createArgument(request: CreateArgumentRequest): Promise<ArgumentItem> {
    if (!request.body || request.body.trim().length < 3) {
      throw new ClaimApiError(
        "INVALID_ARGUMENT_BODY",
        "Argument body must be at least 3 characters",
        400
      );
    }

    const url = `${this.baseUrl}/v1/arguments`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "ARGUMENT_CREATION_FAILED",
        `Failed to create argument: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async getArgument(argumentId: string): Promise<ArgumentItem> {
    const url = `${this.baseUrl}/v1/arguments/${encodeURIComponent(argumentId)}`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "ARGUMENT_NOT_FOUND",
        `Failed to retrieve argument: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async addArgumentRelation(
    argumentId: string,
    request: CreateArgumentRelationRequest
  ): Promise<ArgumentRelationItem> {
    if (request.target_kind === "ARGUMENT" && argumentId === request.target_ref) {
      throw new ClaimApiError(
        "SELF_RELATION_FORBIDDEN",
        "An argument cannot relate to itself",
        400
      );
    }

    const url = `${this.baseUrl}/v1/arguments/${encodeURIComponent(argumentId)}/relations`;
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        ...this.authHeaders(true),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "ARGUMENT_RELATION_FAILED",
        `Failed to add argument relation: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }

  async listArgumentRelations(argumentId: string): Promise<ArgumentRelationItem[]> {
    const url = `${this.baseUrl}/v1/arguments/${encodeURIComponent(argumentId)}/relations`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: this.authHeaders(false),
    });

    if (!response.ok) {
      throw new ClaimApiError(
        "ARGUMENT_RELATIONS_FETCH_FAILED",
        `Failed to fetch argument relations: HTTP ${response.status}`,
        response.status
      );
    }
    return response.json();
  }
}
