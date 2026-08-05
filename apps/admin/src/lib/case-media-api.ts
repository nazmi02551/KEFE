import type { AdminSession } from "@/src/lib/contracts";
import type {
  BindMediaRequest,
  MediaAsset,
  MediaAssetWriteResponse,
  MediaAuditTrail,
  MediaBindingWriteResponse,
  MediaInventory,
  MediaState,
  RegisterMediaRequest
} from "@/src/lib/case-media";
import { boundedMediaText } from "@/src/lib/case-media";

const WRITE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class CaseMediaApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "CaseMediaApiError";
    this.code = code;
    this.status = status;
  }
}

export interface CaseMediaApiOptions {
  baseUrl: string;
  csrfToken?: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new CaseMediaApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new CaseMediaApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new CaseMediaApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

async function parseError(response: Response): Promise<CaseMediaApiError> {
  const fallback = `Admin API request failed with HTTP ${response.status}`;
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    return new CaseMediaApiError("ADMIN_API_HTTP_ERROR", fallback, response.status);
  }
  if (!payload || typeof payload !== "object") {
    return new CaseMediaApiError("ADMIN_API_HTTP_ERROR", fallback, response.status);
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
  return new CaseMediaApiError(
    code,
    boundedMediaText(nested.message ?? nested.detail, fallback),
    response.status
  );
}

export class CaseMediaApiClient {
  private readonly baseUrl: string;
  private readonly csrfToken?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CaseMediaApiOptions) {
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
        throw new CaseMediaApiError(
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

  inventory(state?: MediaState): Promise<MediaInventory> {
    const query = state ? `?state=${encodeURIComponent(state)}` : "";
    return this.request("GET", `/internal/admin/v1/case-media${query}`);
  }

  detail(mediaAssetId: string): Promise<MediaAsset> {
    return this.request(
      "GET",
      `/internal/admin/v1/case-media/${encodeURIComponent(mediaAssetId)}`
    );
  }

  audit(mediaAssetId: string): Promise<MediaAuditTrail> {
    return this.request(
      "GET",
      `/internal/admin/v1/case-media/${encodeURIComponent(mediaAssetId)}/audit`
    );
  }

  register(body: RegisterMediaRequest): Promise<MediaAssetWriteResponse> {
    return this.request("POST", "/internal/admin/v1/case-media", body);
  }

  markReady(mediaAssetId: string): Promise<MediaAssetWriteResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/case-media/${encodeURIComponent(mediaAssetId)}/ready`
    );
  }

  bind(
    mediaAssetId: string,
    body: BindMediaRequest
  ): Promise<MediaBindingWriteResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/case-media/${encodeURIComponent(mediaAssetId)}/bindings`,
      body
    );
  }

  retire(mediaAssetId: string): Promise<MediaAssetWriteResponse> {
    return this.request(
      "POST",
      `/internal/admin/v1/case-media/${encodeURIComponent(mediaAssetId)}/retire`
    );
  }
}
