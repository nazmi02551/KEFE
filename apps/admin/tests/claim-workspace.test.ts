import test from "node:test";
import assert from "node:assert/strict";

import {
  ClaimApiClient,
  ClaimApiError,
  type ClaimItem,
  type ClaimAssessmentItem,
  type ClaimAssertionItem,
  type ClaimRelationItem,
  type ArgumentItem,
  type ArgumentRelationItem,
} from "../src/lib/claim-api";

test("Claim Workspace: full end-to-end knowledge lifecycle (CAP-057, CAP-058, CAP-059)", async () => {
  const claimId = "44444444-4444-4444-8444-444444444444";
  const targetClaimId = "55555555-5555-4555-8555-555555555555";
  const argId = "66666666-6666-4666-8666-666666666666";
  const calls: { url: string; method: string; body?: string }[] = [];

  const mockFetch: typeof fetch = async (input, init) => {
    const url = input.toString();
    const method = init?.method ?? "GET";
    const body = init?.body as string | undefined;
    calls.push({ url, method, body });

    // 1. Create claim
    if (url.endsWith("/v1/claims") && method === "POST") {
      return new Response(
        JSON.stringify({
          id: claimId,
          normalized_text: "Yenilenebilir enerjiye geçiş kamusal bir zorunluluktur.",
          language_code: "tr",
          created_at: "2026-09-12T10:00:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    // 2. Get claim with full history
    if (url.endsWith(`/v1/claims/${claimId}`) && method === "GET") {
      return new Response(
        JSON.stringify({
          id: claimId,
          normalized_text: "Yenilenebilir enerjiye geçiş kamusal bir zorunluluktur.",
          language_code: "tr",
          created_at: "2026-09-12T10:00:00Z",
          assessments: [
            {
              id: "ass-1",
              claim_id: claimId,
              claim_type: "NORMATIVE",
              claim_state: "SUPPORTED",
              taxonomy_version: "v1.0",
              review_state: "ACCEPTED",
              assessed_at: "2026-09-12T10:05:00Z",
              reviewer_ref: "editor:admin",
            },
          ],
          assertions: [
            {
              id: "ast-1",
              claim_id: claimId,
              claimant_kind: "CIVIL_SOCIETY",
              claimant_ref: "ngo:clean-energy",
              asserted_at: "2026-09-12T10:10:00Z",
            },
          ],
          relations: [
            {
              id: "rel-1",
              from_claim_id: claimId,
              to_claim_id: targetClaimId,
              relation_code: "NARROWS_SCOPE_OF",
              taxonomy_version: "v1.0",
              review_state: "ACCEPTED",
              provenance_ref: "admin-link",
              created_at: "2026-09-12T10:15:00Z",
            },
          ],
          evidence_links: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // 3. Add assessment
    if (url.includes(`/v1/claims/${claimId}/assessments`) && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "ass-1",
          claim_id: claimId,
          claim_type: "NORMATIVE",
          claim_state: "SUPPORTED",
          taxonomy_version: "v1.0",
          review_state: "ACCEPTED",
          assessed_at: "2026-09-12T10:05:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    // 4. Add assertion
    if (url.includes(`/v1/claims/${claimId}/assertions`) && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "ast-1",
          claim_id: claimId,
          claimant_kind: "CIVIL_SOCIETY",
          claimant_ref: "ngo:clean-energy",
          asserted_at: "2026-09-12T10:10:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    // 5. Add claim relation
    if (url.includes(`/v1/claims/${claimId}/relations`) && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "rel-1",
          from_claim_id: claimId,
          to_claim_id: targetClaimId,
          relation_code: "NARROWS_SCOPE_OF",
          taxonomy_version: "v1.0",
          review_state: "ACCEPTED",
          created_at: "2026-09-12T10:15:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    // 6. Create argument
    if (url.endsWith("/v1/arguments") && method === "POST") {
      return new Response(
        JSON.stringify({
          id: argId,
          body: "Fosil yakıt tükenişi ve iklim krizi alternatif enerji yatırımlarını zorunlu kılmaktadır.",
          language_code: "tr",
          review_state: "ACCEPTED",
          created_at: "2026-09-12T10:20:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    // 7. Add argument relation
    if (url.includes(`/v1/arguments/${argId}/relations`) && method === "POST") {
      return new Response(
        JSON.stringify({
          id: "arg-rel-1",
          argument_id: argId,
          target_kind: "CLAIM",
          target_ref: claimId,
          relation: "SUPPORTS",
          taxonomy_version: "v1.0",
          review_state: "ACCEPTED",
          created_at: "2026-09-12T10:25:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response(JSON.stringify({ detail: "Not found" }), { status: 404 });
  };

  const client = new ClaimApiClient({
    baseUrl: "http://localhost:8000",
    csrfToken: "admin-csrf-key",
    fetchImpl: mockFetch,
  });

  // Step 1: Create Claim (CAP-057)
  const claim = await client.createClaim({
    normalized_text: "Yenilenebilir enerjiye geçiş kamusal bir zorunluluktur.",
    language_code: "tr",
  });
  assert.equal(claim.id, claimId);

  // Step 2: Add Assessment (CAP-058)
  const assessment = await client.addClaimAssessment(claimId, {
    claim_type: "NORMATIVE",
    claim_state: "SUPPORTED",
    review_state: "ACCEPTED",
  });
  assert.equal(assessment.claim_state, "SUPPORTED");

  // Step 3: Add Assertion
  const assertion = await client.addClaimAssertion(claimId, {
    claimant_kind: "CIVIL_SOCIETY",
    claimant_ref: "ngo:clean-energy",
  });
  assert.equal(assertion.claimant_kind, "CIVIL_SOCIETY");

  // Step 4: Add Claim Relation (CAP-059)
  const claimRel = await client.addClaimRelation(claimId, {
    to_claim_id: targetClaimId,
    relation_code: "NARROWS_SCOPE_OF",
  });
  assert.equal(claimRel.relation_code, "NARROWS_SCOPE_OF");

  // Step 5: Create Argument and link to Claim (CAP-059)
  const argument = await client.createArgument({
    body: "Fosil yakıt tükenişi ve iklim krizi alternatif enerji yatırımlarını zorunlu kılmaktadır.",
  });
  const argRel = await client.addArgumentRelation(argument.id, {
    target_kind: "CLAIM",
    target_ref: claimId,
    relation: "SUPPORTS",
  });
  assert.equal(argRel.relation, "SUPPORTS");

  // Step 6: Verify full retrieval reflects all nodes and edges
  const fullClaim = await client.getClaim(claimId);
  assert.equal(fullClaim.assessments?.length, 1);
  assert.equal(fullClaim.assertions?.length, 1);
  assert.equal(fullClaim.relations?.length, 1);
});

test("Claim Workspace: input validation guards prevent corrupt knowledge state", async () => {
  const client = new ClaimApiClient({ baseUrl: "http://localhost:8000" });

  // Disallow empty or too short text
  await assert.rejects(
    () => client.createClaim({ normalized_text: "  " }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "INVALID_CLAIM_TEXT");
      return true;
    }
  );

  // Disallow self-linking claim
  await assert.rejects(
    () =>
      client.addClaimRelation("claim-A", {
        to_claim_id: "claim-A",
        relation_code: "SAME_AS",
      }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "SELF_RELATION_FORBIDDEN");
      return true;
    }
  );

  // Disallow self-linking argument
  await assert.rejects(
    () =>
      client.addArgumentRelation("arg-A", {
        target_kind: "ARGUMENT",
        target_ref: "arg-A",
        relation: "REBUTS",
      }),
    (err: unknown) => {
      assert(err instanceof ClaimApiError);
      assert.equal(err.code, "SELF_RELATION_FORBIDDEN");
      return true;
    }
  );
});
