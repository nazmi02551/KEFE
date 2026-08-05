import assert from "node:assert/strict";
import test from "node:test";

import {
  OperationalReportsApiClient,
  OperationalReportsApiError
} from "../src/lib/operational-reports-api";

test("client construction and navigation cause no request", () => {
  let calls = 0;
  new OperationalReportsApiClient({
    baseUrl: "http://localhost:8000",
    fetchImpl: async () => {
      calls += 1;
      return new Response("{}", { status: 200 });
    }
  });
  assert.equal(calls, 0);
});

test("session and snapshot are explicit GET-only credentialed reads", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const client = new OperationalReportsApiClient({
    baseUrl: "http://localhost:8000/",
    fetchImpl: async (input, init) => {
      calls.push({ url: String(input), init });
      return new Response(
        JSON.stringify(
          calls.length === 1
            ? {
                admin_subject_id: "00000000-0000-0000-0000-000000000001",
                session_id: "00000000-0000-0000-0000-000000000002",
                roles: ["REVIEWER"],
                direct_capabilities: [],
                authenticated_at: "2026-08-05T00:00:00Z",
                mfa_satisfied_at: null,
                step_up_at: null,
                expires_at: "2026-08-06T00:00:00Z"
              }
            : {
                as_of: "2026-08-05T00:00:00Z",
                overall_signal: "NOMINAL",
                reason_codes: [],
                thresholds: {
                  in_review_attention_threshold: 50,
                  pending_proposal_attention_threshold: 100,
                  moderation_candidate_attention_threshold: 50
                },
                content_supply_policy: {},
                content_supply: { signal: "NOMINAL", as_of: "2026-08-05T00:00:00Z", reason_codes: [] },
                editorial_lifecycle: {},
                proposal_review: {},
                moderation: {},
                aggregate_only: true
              }
        ),
        { status: 200, headers: { "content-type": "application/json" } }
      );
    }
  });

  await client.session();
  await client.snapshot();
  assert.deepEqual(
    calls.map((call) => call.url),
    [
      "http://localhost:8000/internal/admin/v1/session",
      "http://localhost:8000/internal/admin/v1/operational-reports/snapshot"
    ]
  );
  for (const call of calls) {
    assert.equal(call.init?.method, "GET");
    assert.equal(call.init?.credentials, "include");
    assert.equal(call.init?.cache, "no-store");
    assert.equal(new Headers(call.init?.headers).has("X-KEFE-CSRF"), false);
    assert.equal(call.init?.body, undefined);
  }
});

test("remote HTTP base fails closed before a request", () => {
  assert.throws(
    () => new OperationalReportsApiClient({ baseUrl: "http://example.com" }),
    (error: unknown) =>
      error instanceof OperationalReportsApiError &&
      error.code === "ADMIN_API_BASE_INSECURE"
  );
});
