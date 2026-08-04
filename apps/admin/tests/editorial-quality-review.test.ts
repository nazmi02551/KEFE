import assert from "node:assert/strict";
import test from "node:test";

import {
  approvalRequest,
  canApproveEditorialReview,
  canRejectEditorialReview,
  rejectionRequest,
  reviewModesExactlyComplete
} from "../src/lib/editorial-quality-review";
import type { EditorialReviewDetail } from "../src/lib/contracts";

function detail(required: string[], state = "IN_REVIEW"): EditorialReviewDetail {
  return {
    submitter_actor_ref: "admin:submitter",
    submitted_at: "2026-08-04T17:00:00Z",
    version: {
      id: "version-1",
      case_id: "case-1",
      version_no: 1,
      state,
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
      required_review_modes: required,
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
}

test("review mode completion requires an exact unique set", () => {
  assert.equal(
    reviewModesExactlyComplete(
      ["SOURCE_VERIFY", "LEGAL_REVIEW"],
      ["LEGAL_REVIEW", "SOURCE_VERIFY"]
    ),
    true
  );
  assert.equal(
    reviewModesExactlyComplete(["SOURCE_VERIFY"], ["SOURCE_VERIFY", "EXTRA"]),
    false
  );
  assert.equal(
    reviewModesExactlyComplete(["SOURCE_VERIFY"], ["SOURCE_VERIFY", "SOURCE_VERIFY"]),
    false
  );
});

test("approval guard requires review state, exact modes, confirmation and CSRF", () => {
  const review = detail(["SOURCE_VERIFY"]);
  assert.equal(
    canApproveEditorialReview({
      detail: review,
      completedReviewModes: ["SOURCE_VERIFY"],
      confirmed: true,
      csrfToken: "csrf"
    }),
    true
  );
  assert.equal(
    canApproveEditorialReview({
      detail: review,
      completedReviewModes: [],
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
  assert.equal(
    canApproveEditorialReview({
      detail: detail([], "APPROVED"),
      completedReviewModes: [],
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
});

test("rejection guard requires IN_REVIEW, rationale and CSRF", () => {
  assert.equal(
    canRejectEditorialReview({
      detail: detail([]),
      rationale: "Needs revision",
      csrfToken: "csrf"
    }),
    true
  );
  assert.equal(
    canRejectEditorialReview({ detail: detail([]), rationale: " ", csrfToken: "csrf" }),
    false
  );
});

test("decision requests are normalized and bounded to one command", () => {
  assert.deepEqual(approvalRequest([" SOURCE_VERIFY "]), {
    decision: "APPROVE",
    completed_review_modes: ["SOURCE_VERIFY"]
  });
  assert.deepEqual(rejectionRequest("  Needs revision  "), {
    decision: "REJECT",
    completed_review_modes: [],
    rationale: "Needs revision"
  });
});
