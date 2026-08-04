import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient, AdminApiError } from "../src/lib/admin-api";
import type {
  PublicationDecisionResponse,
  PublicationDetail,
  PublicationPreflight,
  PublicationQueuePage
} from "../src/lib/publication-operations";

const VERSION_ID = "11111111-1111-1111-1111-111111111111";

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

const queue: PublicationQueuePage = { items: [], next_offset: null };
const detail = { version: { id: VERSION_ID } } as unknown as PublicationDetail;
const preflight = {
  version_id: VERSION_ID,
  eligible: true,
  validation_failures: [],
  advisory_only: true
} as unknown as PublicationPreflight;
const decision = {
  decision: "PUBLISH",
  version: { id: VERSION_ID },
  pin: {}
} as unknown as PublicationDecisionResponse;

test("publication reads are explicit GET requests without csrf", async () => {
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
    if (url.pathname.endsWith("/preflight")) return jsonResponse(preflight);
    if (url.pathname.endsWith(VERSION_ID)) return jsonResponse(detail);
    return jsonResponse(queue);
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  await client.publicationOperations({
    state: "APPROVED",
    limit: 25,
    offset: 0,
    content_risk: "L1",
    primary_domain_code: "DAILY_LIFE"
  });
  await client.publicationOperation(VERSION_ID);
  await client.publicationPreflight(VERSION_ID);

  assert.deepEqual(calls, [
    {
      method: "GET",
      path: "/internal/admin/v1/publication-operations",
      search: "?state=APPROVED&limit=25&offset=0&content_risk=L1&primary_domain_code=DAILY_LIFE",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/publication-operations/${VERSION_ID}`,
      search: "",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/publication-operations/${VERSION_ID}/preflight`,
      search: "",
      csrf: null
    }
  ]);
});

test("publication decision fails closed before network without csrf", async () => {
  let networkCalls = 0;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(decision);
    }
  });

  await assert.rejects(
    client.decidePublication(VERSION_ID, {
      decision: "PUBLISH",
      acknowledge_immutable: true
    }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("publish and withdraw are exact POST commands with same-session csrf", async () => {
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
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });

  await client.decidePublication(VERSION_ID, {
    decision: "PUBLISH",
    acknowledge_immutable: true
  });
  await client.decidePublication(VERSION_ID, {
    decision: "WITHDRAW",
    rationale: "Operational reason"
  });

  assert.deepEqual(calls, [
    {
      method: "POST",
      path: `/internal/admin/v1/publication-operations/${VERSION_ID}/decision`,
      csrf: "same-session-token",
      body: JSON.stringify({
        decision: "PUBLISH",
        acknowledge_immutable: true
      })
    },
    {
      method: "POST",
      path: `/internal/admin/v1/publication-operations/${VERSION_ID}/decision`,
      csrf: "same-session-token",
      body: JSON.stringify({
        decision: "WITHDRAW",
        rationale: "Operational reason"
      })
    }
  ]);
});
