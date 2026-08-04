import type {
  AdminSession,
  AuthoringAuditTrail,
  CandidateBundleRequest,
  CandidateBundleResponse,
  CaseBuilderDraftInput,
  CaseBuilderVersion,
  EditorialProjectionRequest,
  EditorialProjectionResponse,
  EditorialReviewDecisionRequest,
  EditorialReviewDetail,
  EditorialReviewFilters,
  EditorialReviewQueuePage,
  ProposalDetail,
  ProposalFilters,
  ProposalQueuePage,
  ProposalReviewRequest,
  ProposalReviewResponse
} from "@/src/lib/contracts";
import type {
  ConfigurationAuditTrail,
  FlowComposerSaveInput,
  FlowComposerVersion
} from "@/src/lib/flow-composer";
import type {
  PublicationDecisionRequest,
  PublicationDecisionResponse,
  PublicationDetail,
  PublicationFilters,
  PublicationPreflight,
  PublicationQueuePage
} from "@/src/lib/publication-operations";

const WRITE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class AdminApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "AdminApiError";
    this.code = code;
    this.status = status;
  }
}

export interface AdminApiClientOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new AdminApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is not configured",
      0
    );
  }

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new AdminApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }

  if (parsed.protocol !== "https:" && parsed.hostname !== "localhost") {
    throw new AdminApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

function queryString<T extends object>(filters: T): string {
  const params = new URLSearchParams();
  for (const [key, rawValue] of Object.entries(filters)) {
    if (rawValue === undefined || rawValue === "") continue;
    params.set(key, String(rawValue));
  }
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

function safeMessage(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const compact = value.replace(/\s+/g, " ").trim();
  return compact.slice(0, 500) || fallback;
}

async function parseError(response: Response): Promise<AdminApiError> {
  const fallback = `Admin API request failed with HTTP ${response.status}`;
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    return new AdminApiError("ADMIN_API_HTTP_ERROR", fallback, response.status);
  }

  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const nested =
      record.error && typeof record.error === "object"
        ? (record.error as Record<string, unknown>)
        : record;
    const code =
      typeof nested.code === "string" && nested.code.length <= 120
        ? nested.code
        : "ADMIN_API_HTTP_ERROR";
    const message = safeMessage(nested.message ?? nested.detail, fallback);
    return new AdminApiError(code, message, response.status);
  }

  return new AdminApiError("ADMIN_API_HTTP_ERROR", fallback, response.status);
}

export class AdminApiClient {
  private readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: AdminApiClientOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.csrfToken = options.csrfToken?.trim() || undefined;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const upperMethod = method.toUpperCase();
    const headers = new Headers({ Accept: "application/json" });

    if (body !== undefined) headers.set("Content-Type", "application/json");
    if (WRITE_METHODS.has(upperMethod)) {
      if (!this.csrfToken) {
        throw new AdminApiError(
          "ADMIN_CSRF_REQUIRED",
          "A same-session CSRF token is required for this action",
          0
        );
      }
      headers.set("X-KEFE-CSRF", this.csrfToken);
    }

    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: upperMethod,
      credentials: "include",
      headers,
      cache: "no-store",
      redirect: "error",
      body: body === undefined ? undefined : JSON.stringify(body)
    });

    if (!response.ok) throw await parseError(response);
    return (await response.json()) as T;
  }

  session(): Promise<AdminSession> {
    return this.request("GET", "/internal/admin/v1/session");
  }

  proposals(filters: ProposalFilters = {}): Promise<ProposalQueuePage> {
    return this.request(
      "GET",
      `/internal/admin/v1/proposals${queryString(filters)}`
    );
  }

  proposal(proposalId: string): Promise<ProposalDetail> {
    return this.request(
      "GET",
      `/internal/admin/v1/proposals/${encodeURIComponent(proposalId)}`
    );
  }

  reviewProposal(
    proposalId: string,
    request: ProposalReviewRequest
  ): Promise<ProposalReviewResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/proposals/${encodeURIComponent(proposalId)}/review`,
      request
    );
  }

  buildCandidateBundle(
    sourceBriefProposalId: string,
    request: CandidateBundleRequest
  ): Promise<CandidateBundleResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/source-briefs/${encodeURIComponent(sourceBriefProposalId)}/candidate-bundle`,
      request
    );
  }

  projectCandidate(
    candidateProposalId: string,
    request: EditorialProjectionRequest
  ): Promise<EditorialProjectionResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/candidate-proposals/${encodeURIComponent(candidateProposalId)}/projection`,
      request
    );
  }

  caseBuilderVersion(versionId: string): Promise<CaseBuilderVersion> {
    return this.request(
      "GET",
      `/internal/admin/v1/case-builder/case-versions/${encodeURIComponent(versionId)}`
    );
  }

  saveCaseBuilderDraft(
    versionId: string,
    draft: CaseBuilderDraftInput
  ): Promise<CaseBuilderVersion> {
    return this.request(
      "PUT",
      `/internal/admin/v1/case-builder/case-versions/${encodeURIComponent(versionId)}`,
      draft
    );
  }

  submitCaseVersion(versionId: string): Promise<CaseBuilderVersion> {
    return this.request(
      "POST",
      `/internal/admin/v1/case-versions/${encodeURIComponent(versionId)}/submit`
    );
  }

  caseAudit(caseId: string): Promise<AuthoringAuditTrail> {
    return this.request(
      "GET",
      `/internal/admin/v1/cases/${encodeURIComponent(caseId)}/audit`
    );
  }

  contentReviews(
    filters: EditorialReviewFilters = {}
  ): Promise<EditorialReviewQueuePage> {
    return this.request(
      "GET",
      `/internal/admin/v1/content-reviews${queryString(filters)}`
    );
  }

  contentReview(versionId: string): Promise<EditorialReviewDetail> {
    return this.request(
      "GET",
      `/internal/admin/v1/content-reviews/${encodeURIComponent(versionId)}`
    );
  }

  decideContentReview(
    versionId: string,
    request: EditorialReviewDecisionRequest
  ): Promise<EditorialReviewDetail> {
    return this.request(
      "POST",
      `/internal/admin/v1/content-reviews/${encodeURIComponent(versionId)}/decision`,
      request
    );
  }

  createFlowComposerDraft(): Promise<FlowComposerVersion> {
    return this.request("POST", "/internal/admin/v1/flow-composer/drafts");
  }

  flowComposerVersion(versionId: string): Promise<FlowComposerVersion> {
    return this.request(
      "GET",
      `/internal/admin/v1/flow-composer/configuration-versions/${encodeURIComponent(versionId)}`
    );
  }

  saveFlowComposerVersion(
    versionId: string,
    input: FlowComposerSaveInput
  ): Promise<FlowComposerVersion> {
    return this.request(
      "PUT",
      `/internal/admin/v1/flow-composer/configuration-versions/${encodeURIComponent(versionId)}`,
      input
    );
  }

  flowComposerAudit(versionId: string): Promise<ConfigurationAuditTrail> {
    return this.request(
      "GET",
      `/internal/admin/v1/flow-composer/configuration-versions/${encodeURIComponent(versionId)}/audit`
    );
  }

  publicationOperations(
    filters: PublicationFilters = {}
  ): Promise<PublicationQueuePage> {
    return this.request(
      "GET",
      `/internal/admin/v1/publication-operations${queryString(filters)}`
    );
  }

  publicationOperation(versionId: string): Promise<PublicationDetail> {
    return this.request(
      "GET",
      `/internal/admin/v1/publication-operations/${encodeURIComponent(versionId)}`
    );
  }

  publicationPreflight(versionId: string): Promise<PublicationPreflight> {
    return this.request(
      "GET",
      `/internal/admin/v1/publication-operations/${encodeURIComponent(versionId)}/preflight`
    );
  }

  decidePublication(
    versionId: string,
    request: PublicationDecisionRequest
  ): Promise<PublicationDecisionResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/publication-operations/${encodeURIComponent(versionId)}/decision`,
      request
    );
  }
}
