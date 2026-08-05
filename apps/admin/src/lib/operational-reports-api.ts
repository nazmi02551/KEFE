import type { AdminSession } from "@/src/lib/contracts";
import type { OperationalReportsSnapshot } from "@/src/lib/operational-reports";
import { boundedOperationalText } from "@/src/lib/operational-reports";

export class OperationalReportsApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "OperationalReportsApiError";
    this.code = code;
    this.status = status;
  }
}

export interface OperationalReportsApiOptions {
  baseUrl: string;
  fetchImpl?: typeof fetch;
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new OperationalReportsApiError(
      "ADMIN_API_BASE_REQUIRED",
      "Admin API base URL is required",
      0
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new OperationalReportsApiError(
      "ADMIN_API_BASE_INVALID",
      "Admin API base URL is invalid",
      0
    );
  }
  const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !local) {
    throw new OperationalReportsApiError(
      "ADMIN_API_BASE_INSECURE",
      "Admin API requires HTTPS outside localhost",
      0
    );
  }
  return trimmed;
}

async function parseError(response: Response): Promise<OperationalReportsApiError> {
  const fallback = `Admin API request failed with HTTP ${response.status}`;
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    return new OperationalReportsApiError(
      "ADMIN_API_HTTP_ERROR",
      fallback,
      response.status
    );
  }
  if (!payload || typeof payload !== "object") {
    return new OperationalReportsApiError(
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
  return new OperationalReportsApiError(
    code,
    boundedOperationalText(nested.message ?? nested.detail, fallback),
    response.status
  );
}

export class OperationalReportsApiClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: OperationalReportsApiOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private async get<T>(path: string): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "GET",
      credentials: "include",
      headers: new Headers({ Accept: "application/json" }),
      cache: "no-store",
      redirect: "error"
    });
    if (!response.ok) throw await parseError(response);
    return (await response.json()) as T;
  }

  session(): Promise<AdminSession> {
    return this.get("/internal/admin/v1/session");
  }

  snapshot(): Promise<OperationalReportsSnapshot> {
    return this.get("/internal/admin/v1/operational-reports/snapshot");
  }
}
