import type { AdminSession } from "@/src/lib/contracts";
import type {
  ReasonModerationAuditTrail,
  ReasonModerationDecisionRequest,
  ReasonModerationDecisionResponse,
  ReasonModerationFilters,
  ReasonModerationItem,
  ReasonModerationQueuePage
} from "@/src/lib/reason-moderation";
import { boundedReasonText } from "@/src/lib/reason-moderation";

const WRITE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class ReasonModerationApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ReasonModerationApiError";
    this.code = code;
    this.status = status;
  }
}

export interface ReasonModerationApiOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new ReasonModerationApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new ReasonModerationApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new ReasonModerationApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

function queryString(filters: ReasonModerationFilters): string {
  const params = new URLSearchParams();
  for (const [key, raw] of Object.entries(filters)) {
    if (raw === undefined || raw === "") continue;
    params.set(key, String(raw));
  }
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

async function parseError(response: Response): Promise<ReasonModerationApiError> {
  const fallback = `Admin API request failed with HTTP ${response.status}`;
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    return new ReasonModerationApiError(
      "ADMIN_API_HTTP_ERROR",
      fallback,
      response.status
    );
  }
  if (!payload || typeof payload !== "object") {
    return new ReasonModerationApiError(
      "ADMIN_API_HTTP_ERROR",
      fallback,
      response.status
    );
  }
  const record = payload as Record<string, unknown>;
  const nested =
    record.error && typeof record.error === "object"
      ? (record.error as Record<string, unknown>)
      : record;
  const code =
    typeof nested.code === "string" && nested.code.length <= 120
      ? nested.code
      : "ADMIN_API_HTTP_ERROR";
  const message = boundedReasonText(nested.message ?? nested.detail, fallback);
  return new ReasonModerationApiError(code, message, response.status);
}

export class ReasonModerationApiClient {
  private readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: ReasonModerationApiOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.csrfToken = options.csrfToken?.trim() || undefined;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const upperMethod = method.toUpperCase();
    const headers = new Headers({ Accept: "application/json" });
    if (body !== undefined) headers.set("Content-Type", "application/json");
    if (WRITE_METHODS.has(upperMethod)) {
      if (!this.csrfToken) {
        throw new ReasonModerationApiError(
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

  queue(filters: ReasonModerationFilters): Promise<ReasonModerationQueuePage> {
    return this.request(
      "GET",
      `/internal/admin/v1/community-reason-moderation${queryString(filters)}`
    );
  }

  detail(reasonId: string): Promise<ReasonModerationItem> {
    return this.request(
      "GET",
      `/internal/admin/v1/community-reason-moderation/${encodeURIComponent(reasonId)}`
    );
  }

  audit(reasonId: string): Promise<ReasonModerationAuditTrail> {
    return this.request(
      "GET",
      `/internal/admin/v1/community-reason-moderation/${encodeURIComponent(reasonId)}/audit`
    );
  }

  decide(
    reasonId: string,
    body: ReasonModerationDecisionRequest
  ): Promise<ReasonModerationDecisionResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/community-reason-moderation/${encodeURIComponent(reasonId)}/decision`,
      body
    );
  }
}
