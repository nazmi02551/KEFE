import assert from "node:assert/strict";
import test from "node:test";

import type { CaseBuilderVersion } from "../src/lib/contracts";
import {
  canPublish,
  canWithdraw,
  preflightFingerprint,
  publishRequest,
  withdrawRequest,
  type PublicationDetail,
  type PublicationPreflight
} from "../src/lib/publication-operations";

const version: CaseBuilderVersion = {
  id: "11111111-1111-1111-1111-111111111111",
  case_id: "22222222-2222-2222-2222-222222222222",
  version_no: 2,
  state: "APPROVED",
  title: "Publication candidate",
  summary: "Explicit publication fixture.",
  base_format_code: "DILEMMA",
  primary_domain_code: "DAILY_LIFE",
  content_risk: "L1",
  issues: [],
  context_blocks: [],
  sources: [],
  modifiers: [],
  is_fact_bearing: false,
  is_real_event: false,
  required_review_modes: [],
  completed_review_modes: [],
  flow_template_code: "STANDARD_COMMIT_REVEAL",
  flow_template_version_no: 1,
  content_locale: "tr-TR",
  market_scope: "GLOBAL",
  country_codes: [],
  cultural_context_note: null,
  legal_context_note: null,
  localizations: [],
  created_at: "2026-08-04T20:00:00Z",
  published_at: null
};

const detail: PublicationDetail = {
  version,
  pin: {
    content_configuration_id: null,
    content_configuration_version_no: null,
    flow_template_code: null,
    flow_template_version_no: null,
    entry_step_code: null
  },
  approval: {
    audit_id: "33333333-3333-3333-3333-333333333333",
    actor_ref: "admin:reviewer",
    command: "approve",
    previous_state: "IN_REVIEW",
    new_state: "APPROVED",
    rationale: "No required review modes",
    occurred_at: "2026-08-04T20:10:00Z"
  },
  publication: null
};

const preflight: PublicationPreflight = {
  version_id: version.id,
  eligible: true,
  validation_failures: [],
  prospective_content_configuration_id: "44444444-4444-4444-4444-444444444444",
  prospective_content_configuration_version_no: 4,
  prospective_flow_template_code: "STANDARD_COMMIT_REVEAL",
  prospective_flow_template_version_no: 1,
  prospective_entry_step_code: "CONTEXT",
  advisory_only: true
};

test("publish requires matching eligible advisory preflight, confirmation and csrf", () => {
  assert.equal(
    canPublish({ detail, preflight, confirmed: true, csrfToken: "csrf" }),
    true
  );
  assert.equal(
    canPublish({ detail, preflight, confirmed: false, csrfToken: "csrf" }),
    false
  );
  assert.equal(
    canPublish({ detail, preflight: null, confirmed: true, csrfToken: "csrf" }),
    false
  );
  assert.equal(
    canPublish({
      detail,
      preflight: { ...preflight, version_id: "other" },
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
  assert.equal(
    canPublish({ detail, preflight, confirmed: true, csrfToken: " " }),
    false
  );
  assert.equal(
    canPublish({
      detail: { ...detail, version: { ...version, state: "PUBLISHED" } },
      preflight,
      confirmed: true,
      csrfToken: "csrf"
    }),
    false
  );
});

test("withdraw requires published state, rationale and csrf", () => {
  const publishedDetail: PublicationDetail = {
    ...detail,
    version: { ...version, state: "PUBLISHED", published_at: "2026-08-04T20:20:00Z" }
  };
  assert.equal(
    canWithdraw({ detail: publishedDetail, rationale: "Reason", csrfToken: "csrf" }),
    true
  );
  assert.equal(
    canWithdraw({ detail, rationale: "Reason", csrfToken: "csrf" }),
    false
  );
  assert.equal(
    canWithdraw({ detail: publishedDetail, rationale: " ", csrfToken: "csrf" }),
    false
  );
});

test("decision payloads are strict and rationale is normalized", () => {
  assert.deepEqual(publishRequest(), {
    decision: "PUBLISH",
    acknowledge_immutable: true
  });
  assert.deepEqual(withdrawRequest("  Operational reason  "), {
    decision: "WITHDRAW",
    rationale: "Operational reason"
  });
});

test("preflight fingerprint binds prospective provenance to the loaded version", () => {
  assert.equal(
    preflightFingerprint(preflight),
    [
      version.id,
      preflight.prospective_content_configuration_id,
      "4",
      "STANDARD_COMMIT_REVEAL",
      "1"
    ].join(":")
  );
  assert.notEqual(
    preflightFingerprint(preflight),
    preflightFingerprint({
      ...preflight,
      prospective_content_configuration_version_no: 5
    })
  );
});
