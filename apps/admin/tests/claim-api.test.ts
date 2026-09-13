import test from "node:test";
import assert from "node:assert/strict";

import {
  ClaimApiClient,
  ClaimApiError,
  type ClaimItem,
  type ClaimAssessmentItem,
  type ClaimRelationItem,
  type ArgumentItem,
  type ArgumentRelationItem,
} from "../src/lib/claim-api";

test("ClaimApiClient validates baseUrl rules correctly", () => {
  assert.throws(
    () => new ClaimApiClient({ baseUrl: "" }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "ADMIN_API_BASE_REQUIRED");
      return true;
    }
  );

  assert.throws(
    () => new ClaimApiClient({ baseUrl: "not-a-valid-url" }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "ADMIN_API_BASE_INVALID");
      return true;
    }
  );

  assert.throws(
    () => new ClaimApiClient({ baseUrl: "http://remote-claim-service.kefe.org" }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "ADMIN_API_BASE_INSECURE");
      return true;
    }
  );
});

test("ClaimApiClient enforces input validations and prevents self-relations", async () => {
  const client = new ClaimApiClient({ baseUrl: "http://localhost:8000" });

  await assert.rejects(
    () => client.createClaim({ normalized_text: "a" }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "INVALID_CLAIM_TEXT");
      return true;
    }
  );

  await assert.rejects(
    () => client.createArgument({ body: "ab" }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "INVALID_ARGUMENT_BODY");
      return true;
    }
  );

  await assert.rejects(
    () =>
      client.addClaimRelation("claim-123", {
        to_claim_id: "claim-123",
        relation_code: "SAME_AS",
      }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "SELF_RELATION_FORBIDDEN");
      return true;
    }
  );

  await assert.rejects(
    () =>
      client.addArgumentRelation("arg-123", {
        target_kind: "ARGUMENT",
        target_ref: "arg-123",
        relation: "REBUTS",
      }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "SELF_RELATION_FORBIDDEN");
      return true;
    }
  );
});

test("ClaimApiClient performs mock HTTP operations with correct headers and payload", async () => {
  const capturedRequests: { url: string; method?: string; headers?: Record<string, string>; body?: string }[] = [];

  const mockFetch: typeof fetch = async (input, init) => {
    const url = input.toString();
    const method = init?.method ?? "GET";
    const headers = init?.headers as Record<string, string>;
    const body = init?.body as string;
    capturedRequests.push({ url, method, headers, body });

    if (url.endsWith("/v1/claims") && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "claim-uuid-1",
          normalized_text: "Yapay zeka modelleri denetlenmelidir.",
          language_code: "tr",
          created_at: "2026-09-12T12:00:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.includes("/v1/claims/claim-uuid-1/assessments") && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "ass-uuid-1",
          claim_id: "claim-uuid-1",
          claim_type: "FACTUAL",
          claim_state: "SUPPORTED",
          taxonomy_version: "v1.0",
          review_state: "ACCEPTED",
          assessed_at: "2026-09-12T12:05:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.includes("/v1/claims/claim-uuid-1") && method === "GET") {
      return new Response(
        JSON.stringify({
          id: "claim-uuid-1",
          normalized_text: "Yapay zeka modelleri denetlenmelidir.",
          language_code: "tr",
          created_at: "2026-09-12T12:00:00Z",
          assessments: [],
          assertions: [],
          evidence_links: [],
          relations: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.endsWith("/v1/arguments") && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "arg-uuid-1",
          body: "Denetim kamu yararını ve şeffaflığı temin eder.",
          language_code: "tr",
          review_state: "ACCEPTED",
          created_at: "2026-09-12T12:10:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response(JSON.stringify({ detail: "Not found" }), { status: 404 });
  };

  const client = new ClaimApiClient({
    baseUrl: "http://localhost:8000",
    csrfToken: "mock-csrf-token",
    fetchImpl: mockFetch,
  });

  // 1. Create claim
  const claim = await client.createClaim({
    normalized_text: "Yapay zeka modelleri denetlenmelidir.",
    language_code: "tr",
  });
  assert.equal(claim.id, "claim-uuid-1");
  assert.equal(capturedRequests[0].headers?.["X-CSRF-Token"], "mock-csrf-token");

  // 2. Add assessment
  const assessment = await client.addClaimAssessment("claim-uuid-1", {
    claim_type: "FACTUAL",
    claim_state: "SUPPORTED",
    review_state: "ACCEPTED",
  });
  assert.equal(assessment.claim_state, "SUPPORTED");

  // 3. Get claim
  const retrievedClaim = await client.getClaim("claim-uuid-1");
  assert.equal(retrievedClaim.id, "claim-uuid-1");

  // 4. Create argument
  const arg = await client.createArgument({
    body: "Denetim kamu yararını ve şeffaflığı temin eder.",
  });
  assert.equal(arg.id, "arg-uuid-1");

  // 5. 404 error handling
  await assert.rejects(
    () => client.getClaim("nonexistent-claim"),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "CLAIM_NOT_FOUND");
      assert.equal(err.status, 404);
      return true;
    }
  );
});
