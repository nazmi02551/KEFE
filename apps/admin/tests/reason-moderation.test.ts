import assert from "node:assert/strict";
import test from "node:test";

import {
  boundedReasonText,
  canSubmitModeration,
  moderationDecisionRequest,
  reportSummary,
  type ReasonModerationItem
} from "../src/lib/reason-moderation";

const reason: ReasonModerationItem = {
  reason_id: "11111111-1111-1111-1111-111111111111",
  case_version_id: "22222222-2222-2222-2222-222222222222",
  tags: ["FAIRNESS"],
  body: "A reason requiring an explicit moderation decision.",
  moderation_state: "PENDING",
  created_at: "2026-08-05T05:00:00Z",
  updated_at: "2026-08-05T05:00:00Z",
  report_count: 3,
  report_counts_by_code: {
    PERSONAL_DATA: 2,
    ABUSE: 1,
    OTHER: 0
  },
  latest_reported_at: "2026-08-05T05:05:00Z",
  candidate_at: "2026-08-05T05:00:00Z"
};

test("decision requires exact reason confirmation, rationale, checkbox and csrf", () => {
  assert.equal(
    canSubmitModeration({
      reason,
      state: "ALLOWED",
      rationale: "This reason is safe after review.",
      confirmationReasonId: reason.reason_id,
      confirmed: true,
      csrfToken: "csrf"
    }),
    true
  );
  assert.equal(
    canSubmitModeration({
      reason,
      state: "BLOCKED",
      rationale: "This reason is unsafe after review.",
      confirmationReasonId: "other",
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
  assert.equal(
    canSubmitModeration({
      reason,
      state: "BLOCKED",
      rationale: "short",
      confirmationReasonId: reason.reason_id,
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
  assert.equal(
    canSubmitModeration({
      reason,
      state: "BLOCKED",
      rationale: "This reason is unsafe after review.",
      confirmationReasonId: reason.reason_id,
      confirmed: false,
      csrfToken: "csrf"
    }),
    false
  );
  assert.equal(
    canSubmitModeration({
      reason,
      state: "BLOCKED",
      rationale: "This reason is unsafe after review.",
      confirmationReasonId: reason.reason_id,
      confirmed: true,
      csrfToken: " "
    }),
    false
  );
});

test("decision payload is trimmed and bound to exact reason id", () => {
  assert.deepEqual(
    moderationDecisionRequest({
      reasonId: reason.reason_id,
      state: "BLOCKED",
      rationale: "  Personal data is exposed in the text.  "
    }),
    {
      state: "BLOCKED",
      rationale: "Personal data is exposed in the text.",
      confirm_reason_id: reason.reason_id
    }
  );
});

test("report summary is aggregate-only and deterministically sorted", () => {
  assert.deepEqual(reportSummary(reason), ["ABUSE: 1", "PERSONAL_DATA: 2"]);
});

test("error text is compact and bounded", () => {
  const text = boundedReasonText(`  ${"x".repeat(700)}\n`, "fallback");
  assert.equal(text.length, 500);
  assert.equal(boundedReasonText(null, "fallback"), "fallback");
});
