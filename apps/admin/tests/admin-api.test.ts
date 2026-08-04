import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient, AdminApiError } from "../src/lib/admin-api";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

test("read requests include the Admin session cookie boundary without CSRF", async () => {
  const calls: Array<{ input: string; init?: RequestInit }> = [];
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async (input, init) => {
      calls.push({ input: String(input), init });
      return jsonResponse({
        admin_subject_id: "11111111-1111-1111-1111-111111111111",
        session_id: "22222222-2222-2222-2222-222222222222",
        roles: ["REVIEWER"],
        direct_capabilities: [],
        authenticated_at: "2026-08-04T16:00:00Z",
        mfa_satisfied_at: null,
        step_up_at: null,
        expires_at: "2026-08-04T18:00:00Z"
      });
    }
  });

  const session = await client.session();

  assert.equal(session.roles[0], "REVIEWER");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].input, "https://api.example.test/internal/admin/v1/session");
  assert.equal(calls[0].init?.credentials, "include");
  assert.equal(new Headers(calls[0].init?.headers).has("X-KEFE-CSRF"), false);
});

test("write requests fail closed before network access when CSRF is missing", async () => {
  let calls = 0;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      calls += 1;
      return jsonResponse({});
    }
  });

  await assert.rejects(
    client.reviewProposal("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", {
      decision: "ACCEPTED"
    }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(calls, 0);
});

test("explicit writes include same-session CSRF and exact JSON body", async () => {
  let captured: RequestInit | undefined;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl: async (_input, init) => {
      captured = init;
      return jsonResponse({
        proposal_review_decision_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        proposal_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        decision: "ACCEPTED",
        reviewer_ref: "admin:1",
        decided_at: "2026-08-04T16:10:00Z",
        rationale: "checked",
        reason_code: null,
        policy_version: "editorial-v1",
        risk_policy_version: null
      });
    }
  });

  await client.reviewProposal("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", {
    decision: "ACCEPTED",
    rationale: "checked",
    policy_version: "editorial-v1"
  });

  const headers = new Headers(captured?.headers);
  assert.equal(captured?.method, "POST");
  assert.equal(headers.get("X-KEFE-CSRF"), "same-session-token");
  assert.deepEqual(JSON.parse(String(captured?.body)), {
    decision: "ACCEPTED",
    rationale: "checked",
    policy_version: "editorial-v1"
  });
});

test("API errors are bounded and HTML is never surfaced as markup", async () => {
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () =>
      jsonResponse(
        {
          error: {
            code: "ADMIN_TEST_FAILURE",
            message: `<script>alert(1)</script>${"x".repeat(800)}`
          }
        },
        422
      )
  });

  await assert.rejects(client.session(), (error: unknown) => {
    assert.ok(error instanceof AdminApiError);
    assert.equal(error.code, "ADMIN_TEST_FAILURE");
    assert.equal(error.status, 422);
    assert.ok(error.message.length <= 500);
    return true;
  });
});

test("non-local insecure API origins are rejected", () => {
  assert.throws(
    () => new AdminApiClient({ baseUrl: "http://api.example.test" }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_API_BASE_INSECURE"
  );
});
