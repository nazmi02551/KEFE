import assert from "node:assert/strict";
import test from "node:test";

import {
  ReasonModerationApiClient,
  ReasonModerationApiError
} from "../src/lib/reason-moderation-api";
import type {
  ReasonModerationAuditTrail,
  ReasonModerationDecisionResponse,
  ReasonModerationItem,
  ReasonModerationQueuePage
} from "../src/lib/reason-moderation";

const REASON_ID = "11111111-1111-1111-1111-111111111111";

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

const queue: ReasonModerationQueuePage = { items: [], next_offset: null };
const detail = { reason_id: REASON_ID } as ReasonModerationItem;
const audit: ReasonModerationAuditTrail = { items: [] };
const decision = {
  reason: detail,
  audit: { audit_id: "audit" }
} as unknown as ReasonModerationDecisionResponse;

test("client construction starts no request and reads omit csrf", async () => {
  const calls: Array<{ method: string; path: string; search: string; csrf: string | null }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      search: url.search,
      csrf: headers.get("X-KEFE-CSRF")
    });
    if (url.pathname.endsWith("/audit")) return jsonResponse(audit);
    if (url.pathname.endsWith(REASON_ID)) return jsonResponse(detail);
    return jsonResponse(queue);
  };
  const client = new ReasonModerationApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  await client.queue({
    kind: "REPORTED",
    limit: 25,
    offset: 0,
    case_version_id: "case-version",
    report_code: "PERSONAL_DATA"
  });
  await client.detail(REASON_ID);
  await client.audit(REASON_ID);

  assert.deepEqual(calls, [
    {
      method: "GET",
      path: "/internal/admin/v1/community-reason-moderation",
      search:
        "?kind=REPORTED&limit=25&offset=0&case_version_id=case-version&report_code=PERSONAL_DATA",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/community-reason-moderation/${REASON_ID}`,
      search: "",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/community-reason-moderation/${REASON_ID}/audit`,
      search: "",
      csrf: null
    }
  ]);
});

test("decision fails closed before network without csrf", async () => {
  let networkCalls = 0;
  const client = new ReasonModerationApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(decision);
    }
  });

  await assert.rejects(
    client.decide(REASON_ID, {
      state: "BLOCKED",
      rationale: "Personal data is exposed.",
      confirm_reason_id: REASON_ID
    }),
    (error: unknown) =>
      error instanceof ReasonModerationApiError &&
      error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("decision is one exact POST with same-session csrf", async () => {
  const calls: Array<{
    method: string;
    path: string;
    csrf: string | null;
    body: string | null;
  }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      csrf: headers.get("X-KEFE-CSRF"),
      body: typeof init.body === "string" ? init.body : null
    });
    return jsonResponse(decision);
  };
  const client = new ReasonModerationApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });
  const body = {
    state: "ALLOWED" as const,
    rationale: "The reason is safe after review.",
    confirm_reason_id: REASON_ID
  };

  await client.decide(REASON_ID, body);

  assert.deepEqual(calls, [
    {
      method: "POST",
      path: `/internal/admin/v1/community-reason-moderation/${REASON_ID}/decision`,
      csrf: "same-session-token",
      body: JSON.stringify(body)
    }
  ]);
});

test("insecure remote API base fails before network", () => {
  assert.throws(
    () => new ReasonModerationApiClient({ baseUrl: "http://api.example.test" }),
    (error: unknown) =>
      error instanceof ReasonModerationApiError &&
      error.code === "ADMIN_API_BASE_INSECURE"
  );
});
