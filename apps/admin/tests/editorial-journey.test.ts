import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient } from "../src/lib/admin-api";
import type { CandidateBundleRequest } from "../src/lib/contracts";
import { projectionIdempotencyKey } from "../src/lib/idempotency";

const SOURCE_BRIEF = "11111111-1111-1111-1111-111111111111";
const SOURCE_REVIEW = "22222222-2222-2222-2222-222222222222";
const DECISION_PROBLEM = "33333333-3333-3333-3333-333333333333";
const QUESTION_DRAFT = "44444444-4444-4444-4444-444444444444";
const CANDIDATE_CASE = "55555555-5555-5555-5555-555555555555";
const CANDIDATE_REVIEW = "66666666-6666-6666-6666-666666666666";

function response(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

test("mocked canonical journey keeps every mutation explicit and separate", async () => {
  const calls: Array<{ method: string; path: string; csrf: string | null }> = [];
  const accepted = new Map<string, string>();
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const method = String(init.method ?? "GET");
    const headers = new Headers(init.headers);
    calls.push({
      method,
      path: url.pathname + url.search,
      csrf: headers.get("X-KEFE-CSRF")
    });

    if (method === "GET" && url.pathname.endsWith("/session")) {
      return response({
        admin_subject_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        session_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        roles: ["REVIEWER"],
        direct_capabilities: ["CONTENT_REVIEW", "SOURCE_VERIFY", "CONTENT_PROJECT"],
        authenticated_at: "2026-08-04T16:00:00Z",
        mfa_satisfied_at: "2026-08-04T16:00:00Z",
        step_up_at: "2026-08-04T16:00:00Z",
        expires_at: "2026-08-04T18:00:00Z"
      });
    }

    if (method === "GET" && url.pathname.endsWith("/proposals")) {
      return response({
        items: [
          {
            proposal_id: SOURCE_BRIEF,
            proposal_kind: "SOURCE_BRIEF",
            payload_schema_ref: "kefe.source-brief",
            payload_schema_version: "1.0.0",
            payload_hash: "a".repeat(64),
            run_id: "77777777-7777-7777-7777-777777777777",
            stage_execution_id: "88888888-8888-8888-8888-888888888888",
            input_artifact_kind: "NORMALIZED_ARTIFACT",
            input_artifact_id: "99999999-9999-9999-9999-999999999999",
            pipeline_code: "FEED_ITEM_SOURCE_BRIEF",
            pipeline_version: "1.0.0",
            locale: "tr",
            jurisdiction_code: null,
            proposal_taxonomy_version: null,
            proposal_configuration_version: "1.0.0",
            proposal_methodology_version: null,
            run_taxonomy_version: null,
            run_methodology_version: null,
            confidence: null,
            risk_code: "UNREVIEWED_SOURCE_BRIEF",
            ai_execution_ref: null,
            provenance_ref: null,
            supersedes_proposal_id: null,
            created_at: "2026-08-04T16:01:00Z",
            review_state: "PENDING",
            review: null
          }
        ],
        next_cursor: null
      });
    }

    if (method === "POST" && url.pathname.endsWith("/review")) {
      const proposalId = url.pathname.split("/").at(-2) ?? "";
      const reviewId = proposalId === CANDIDATE_CASE ? CANDIDATE_REVIEW :
        proposalId === SOURCE_BRIEF ? SOURCE_REVIEW :
        `${proposalId.slice(0, 24)}aaaaaaaaaaaa`;
      accepted.set(proposalId, reviewId);
      return response(
        {
          proposal_review_decision_id: reviewId,
          proposal_id: proposalId,
          decision: "ACCEPTED",
          reviewer_ref: "admin:reviewer",
          decided_at: "2026-08-04T16:05:00Z",
          rationale: "independently reviewed",
          reason_code: null,
          policy_version: "editorial-v1",
          risk_policy_version: "risk-v1"
        },
        201
      );
    }

    if (method === "POST" && url.pathname.endsWith("/candidate-bundle")) {
      assert.equal(accepted.get(SOURCE_BRIEF), SOURCE_REVIEW);
      return response({
        candidate_seed_artifact_id: "12121212-1212-1212-1212-121212121212",
        run_id: "13131313-1313-1313-1313-131313131313",
        decision_problem_proposal_id: DECISION_PROBLEM,
        question_draft_proposal_id: QUESTION_DRAFT,
        candidate_case_proposal_id: CANDIDATE_CASE,
        run_state: "SUCCEEDED",
        proposal_review_state: "PENDING"
      });
    }

    if (method === "POST" && url.pathname.endsWith("/projection")) {
      assert.equal(accepted.has(DECISION_PROBLEM), true);
      assert.equal(accepted.has(QUESTION_DRAFT), true);
      assert.equal(accepted.get(CANDIDATE_CASE), CANDIDATE_REVIEW);
      return response({
        projection_record_id: "14141414-1414-1414-1414-141414141414",
        candidate_proposal_id: CANDIDATE_CASE,
        proposal_review_decision_id: CANDIDATE_REVIEW,
        profile_code: "STANDARD_EDITORIAL",
        profile_version: 1,
        authoring_case_id: "15151515-1515-1515-1515-151515151515",
        authoring_case_version_id: "16161616-1616-1616-1616-161616161616",
        lifecycle_state: "DRAFT",
        replayed: false,
        created_at: "2026-08-04T16:10:00Z"
      });
    }

    return response({ error: { code: "UNEXPECTED_ROUTE", message: url.pathname } }, 500);
  };

  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });

  assert.equal(calls.length, 0, "constructing the workspace client performs no request");
  await client.session();
  const queue = await client.proposals({ review_state: "PENDING" });
  assert.equal(queue.items[0].proposal_id, SOURCE_BRIEF);

  const sourceReview = await client.reviewProposal(SOURCE_BRIEF, {
    decision: "ACCEPTED",
    rationale: "independently reviewed",
    policy_version: "editorial-v1",
    risk_policy_version: "risk-v1"
  });

  const bundleRequest: CandidateBundleRequest = {
    source_brief_review_decision_id: sourceReview.proposal_review_decision_id,
    slug: "ornek-kamu-vakasi",
    title: "Örnek kamu vakası",
    summary: "Editör tarafından açıkça tanımlanan örnek özet.",
    base_format_code: "STANDARD_CASE",
    primary_domain_code: "PUBLIC_LIFE",
    content_risk: "MEDIUM",
    issue_code: "primary-issue",
    issue_title: "Ana mesele",
    question_stable_code: "primary-question",
    question_prompt: "Bu durumda en adil karar hangisidir?",
    response_options: ["Katılıyorum", "Katılmıyorum"],
    flow_template_code: "STANDARD_WEIGH",
    flow_template_version_no: 1,
    content_locale: "tr",
    market_scope: "GLOBAL",
    country_codes: [],
    required_review_modes: ["EDITORIAL", "FACT_CHECK"],
    is_fact_bearing: true,
    is_real_event: true,
    context_title: "Bağlam",
    cultural_context_note: null,
    legal_context_note: null
  };
  const bundle = await client.buildCandidateBundle(SOURCE_BRIEF, bundleRequest);
  assert.equal(bundle.proposal_review_state, "PENDING");

  await client.reviewProposal(bundle.decision_problem_proposal_id, {
    decision: "ACCEPTED"
  });
  await client.reviewProposal(bundle.question_draft_proposal_id, {
    decision: "ACCEPTED"
  });
  const candidateReview = await client.reviewProposal(
    bundle.candidate_case_proposal_id,
    { decision: "ACCEPTED" }
  );

  const projection = await client.projectCandidate(CANDIDATE_CASE, {
    proposal_review_decision_id: candidateReview.proposal_review_decision_id,
    profile_code: "STANDARD_EDITORIAL",
    profile_version: 1,
    idempotency_key: projectionIdempotencyKey(
      CANDIDATE_CASE,
      candidateReview.proposal_review_decision_id
    )
  });

  assert.equal(projection.lifecycle_state, "DRAFT");
  assert.equal(calls.filter((call) => call.method === "POST").length, 5);
  assert.equal(
    calls.filter((call) => call.method === "POST").every(
      (call) => call.csrf === "same-session-token"
    ),
    true
  );
  assert.equal(
    calls.some((call) => /submit|approve|publish/.test(call.path)),
    false
  );
});
