import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient, AdminApiError } from "../src/lib/admin-api";
import type {
  EditorialReviewDecisionRequest,
  EditorialReviewDetail,
  EditorialReviewQueuePage
} from "../src/lib/contracts";

const VERSION_ID = "11111111-1111-1111-1111-111111111111";
const CASE_ID = "22222222-2222-2222-2222-222222222222";

const detail: EditorialReviewDetail = {
  submitter_actor_ref: "admin:submitter",
  submitted_at: "2026-08-04T17:00:00Z",
  version: {
    id: VERSION_ID,
    case_id: CASE_ID,
    version_no: 1,
    state: "IN_REVIEW",
    title: "Review fixture",
    summary: "Summary",
    base_format_code: "DILEMMA",
    primary_domain_code: "PUBLIC_LIFE",
    content_risk: "L1",
    issues: [],
    context_blocks: [],
    sources: [],
    modifiers: [],
    is_fact_bearing: false,
    is_real_event: false,
    required_review_modes: ["SOURCE_VERIFY"],
    completed_review_modes: [],
    flow_template_code: "STANDARD_COMMIT_REVEAL",
    flow_template_version_no: 1,
    content_locale: "tr-TR",
    market_scope: "GLOBAL",
    country_codes: [],
    cultural_context_note: null,
    legal_context_note: null,
    localizations: [],
    created_at: "2026-08-04T16:00:00Z",
    published_at: null
  }
};

const page: EditorialReviewQueuePage = {
  items: [
    {
      version_id: VERSION_ID,
      case_id: CASE_ID,
      version_no: 1,
      title: detail.version.title,
      content_risk: "L1",
      primary_domain_code: "PUBLIC_LIFE",
      content_locale: "tr-TR",
      required_review_modes: ["SOURCE_VERIFY"],
      created_at: detail.version.created_at
    }
  ],
  next_offset: null
};

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

test("editorial review reads are explicit credentialed GETs without CSRF", async () => {
  const calls: Array<{ method: string; url: URL; csrf: string | null }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({ method: String(init.method), url, csrf: headers.get("X-KEFE-CSRF") });
    return jsonResponse(url.pathname.endsWith(VERSION_ID) ? detail : page);
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  const queue = await client.contentReviews({
    limit: 25,
    offset: 50,
    content_risk: "L1",
    primary_domain_code: "PUBLIC_LIFE"
  });
  assert.equal(queue.items[0]?.version_id, VERSION_ID);
  const loaded = await client.contentReview(VERSION_ID);
  assert.equal(loaded.version.state, "IN_REVIEW");

  assert.equal(calls.length, 2);
  assert.equal(calls[0]?.method, "GET");
  assert.equal(calls[0]?.url.pathname, "/internal/admin/v1/content-reviews");
  assert.equal(calls[0]?.url.searchParams.get("limit"), "25");
  assert.equal(calls[0]?.url.searchParams.get("offset"), "50");
  assert.equal(calls[0]?.url.searchParams.get("content_risk"), "L1");
  assert.equal(calls[0]?.csrf, null);
  assert.equal(
    calls[1]?.url.pathname,
    `/internal/admin/v1/content-reviews/${VERSION_ID}`
  );
  assert.equal(calls[1]?.csrf, null);
});

test("editorial review decision fails before network without same-session CSRF", async () => {
  let networkCalls = 0;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(detail);
    }
  });

  await assert.rejects(
    client.decideContentReview(VERSION_ID, {
      decision: "APPROVE",
      completed_review_modes: ["SOURCE_VERIFY"]
    }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("approval and rejection use one exact decision path and CSRF", async () => {
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
    const request = JSON.parse(String(init.body)) as EditorialReviewDecisionRequest;
    return jsonResponse({
      ...detail,
      version: {
        ...detail.version,
        state: request.decision === "APPROVE" ? "APPROVED" : "DRAFT"
      }
    });
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });

  const approval: EditorialReviewDecisionRequest = {
    decision: "APPROVE",
    completed_review_modes: ["SOURCE_VERIFY"]
  };
  const rejection: EditorialReviewDecisionRequest = {
    decision: "REJECT",
    completed_review_modes: [],
    rationale: "Needs revision"
  };
  assert.equal((await client.decideContentReview(VERSION_ID, approval)).version.state, "APPROVED");
  assert.equal((await client.decideContentReview(VERSION_ID, rejection)).version.state, "DRAFT");

  assert.deepEqual(
    calls.map((call) => ({ method: call.method, path: call.path, csrf: call.csrf })),
    [
      {
        method: "POST",
        path: `/internal/admin/v1/content-reviews/${VERSION_ID}/decision`,
        csrf: "same-session-token"
      },
      {
        method: "POST",
        path: `/internal/admin/v1/content-reviews/${VERSION_ID}/decision`,
        csrf: "same-session-token"
      }
    ]
  );
  assert.equal(calls[0]?.body, JSON.stringify(approval));
  assert.equal(calls[1]?.body, JSON.stringify(rejection));
  assert.equal(calls.some((call) => /publish|withdraw/.test(call.path)), false);
});
