import assert from "node:assert/strict";
import test from "node:test";

import {
  parseJsonSection,
  prettyJson,
  splitLines,
  toDraftInput,
  validateDraft
} from "../src/lib/case-builder";
import type { CaseBuilderVersion } from "../src/lib/contracts";

const version: CaseBuilderVersion = {
  id: "11111111-1111-1111-1111-111111111111",
  case_id: "22222222-2222-2222-2222-222222222222",
  version_no: 4,
  state: "DRAFT",
  title: "Düzenlenebilir vaka",
  summary: "Açık kaydetme için fixture.",
  base_format_code: "STANDARD_CASE",
  primary_domain_code: "PUBLIC_LIFE",
  content_risk: "MEDIUM",
  issues: [
    {
      id: "33333333-3333-3333-3333-333333333333",
      code: "primary-issue",
      title: "Ana mesele",
      sort_order: 0,
      questions: []
    }
  ],
  context_blocks: [],
  sources: [],
  modifiers: ["BLIND_FIRST"],
  is_fact_bearing: true,
  is_real_event: true,
  required_review_modes: ["EDITORIAL"],
  completed_review_modes: ["SOURCE_VERIFY"],
  flow_template_code: "STANDARD_WEIGH",
  flow_template_version_no: 9,
  content_locale: "tr",
  market_scope: "COUNTRY_SET",
  country_codes: ["TR"],
  cultural_context_note: null,
  legal_context_note: null,
  localizations: [],
  created_at: "2026-08-04T16:00:00Z",
  published_at: null
};

test("toDraftInput excludes lifecycle, Flow and completed review authority", () => {
  const draft = toDraftInput(version);
  assert.equal(draft.title, version.title);
  assert.equal("state" in draft, false);
  assert.equal("flow_template_code" in draft, false);
  assert.equal("flow_template_version_no" in draft, false);
  assert.equal("completed_review_modes" in draft, false);
  assert.equal("published_at" in draft, false);
});

test("structured JSON sections require arrays and retain nested values", () => {
  const issues = parseJsonSection("issues", prettyJson(version.issues));
  assert.equal(issues.length, 1);
  assert.equal(issues[0].title, "Ana mesele");
  assert.throws(
    () => parseJsonSection("sources", "{}"),
    /bir JSON dizisi olmalıdır/
  );
  assert.throws(
    () => parseJsonSection("localizations", "not-json"),
    /geçerli JSON olmalıdır/
  );
});

test("DRAFT validation is explicit and market-aware", () => {
  assert.deepEqual(validateDraft(version), []);
  assert.deepEqual(
    validateDraft({ ...version, state: "IN_REVIEW" }),
    ["Yalnız DRAFT sürümü düzenlenebilir."]
  );
  assert.deepEqual(
    validateDraft({ ...version, country_codes: [] }),
    ["COUNTRY_SET için en az bir ülke kodu gereklidir."]
  );
});

test("line lists are deterministic and discard empty items", () => {
  assert.deepEqual(splitLines("TR, DE\n\nFR"), ["TR", "DE", "FR"]);
});
