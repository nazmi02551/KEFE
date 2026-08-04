import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient, AdminApiError } from "../src/lib/admin-api";
import type {
  CaseBuilderDraftInput,
  CaseBuilderVersion
} from "../src/lib/contracts";

const VERSION_ID = "11111111-1111-1111-1111-111111111111";
const CASE_ID = "22222222-2222-2222-2222-222222222222";

const version: CaseBuilderVersion = {
  id: VERSION_ID,
  case_id: CASE_ID,
  version_no: 1,
  state: "DRAFT",
  title: "Case Builder",
  summary: "Explicit DRAFT fixture.",
  base_format_code: "STANDARD_CASE",
  primary_domain_code: "PUBLIC_LIFE",
  content_risk: "MEDIUM",
  issues: [],
  context_blocks: [],
  sources: [],
  modifiers: [],
  is_fact_bearing: true,
  is_real_event: true,
  required_review_modes: ["EDITORIAL"],
  completed_review_modes: [],
  flow_template_code: "STANDARD_WEIGH",
  flow_template_version_no: 1,
  content_locale: "tr",
  market_scope: "GLOBAL",
  country_codes: [],
  cultural_context_note: null,
  legal_context_note: null,
  localizations: [],
  created_at: "2026-08-04T16:00:00Z",
  published_at: null
};

const draft: CaseBuilderDraftInput = {
  title: version.title,
  summary: version.summary,
  base_format_code: version.base_format_code,
  primary_domain_code: version.primary_domain_code,
  content_risk: version.content_risk,
  issues: version.issues,
  context_blocks: version.context_blocks,
  sources: version.sources,
  modifiers: version.modifiers,
  is_fact_bearing: version.is_fact_bearing,
  is_real_event: version.is_real_event,
  required_review_modes: version.required_review_modes,
  content_locale: version.content_locale,
  market_scope: version.market_scope,
  country_codes: version.country_codes,
  cultural_context_note: version.cultural_context_note,
  legal_context_note: version.legal_context_note,
  localizations: version.localizations
};

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

test("Case Builder construction and reads never mutate or require CSRF", async () => {
  const calls: Array<{ method: string; path: string; csrf: string | null }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      csrf: headers.get("X-KEFE-CSRF")
    });
    if (url.pathname.endsWith("/audit")) return jsonResponse({ items: [] });
    return jsonResponse(version);
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  const loaded = await client.caseBuilderVersion(VERSION_ID);
  assert.equal(loaded.id, VERSION_ID);
  const audit = await client.caseAudit(CASE_ID);
  assert.deepEqual(audit.items, []);
  assert.deepEqual(calls, [
    {
      method: "GET",
      path: `/internal/admin/v1/case-builder/case-versions/${VERSION_ID}`,
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/cases/${CASE_ID}/audit`,
      csrf: null
    }
  ]);
});

test("Case Builder writes fail closed before network when CSRF is missing", async () => {
  let networkCalls = 0;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(version);
    }
  });

  await assert.rejects(
    client.saveCaseBuilderDraft(VERSION_ID, draft),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  await assert.rejects(
    client.submitCaseVersion(VERSION_ID),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("save and submit are separate exact commands with same-session CSRF", async () => {
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
    return jsonResponse(
      url.pathname.endsWith("/submit") ? { ...version, state: "IN_REVIEW" } : version
    );
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });

  const saved = await client.saveCaseBuilderDraft(VERSION_ID, draft);
  assert.equal(saved.state, "DRAFT");
  const submitted = await client.submitCaseVersion(VERSION_ID);
  assert.equal(submitted.state, "IN_REVIEW");

  assert.equal(calls.length, 2);
  assert.deepEqual(calls[0], {
    method: "PUT",
    path: `/internal/admin/v1/case-builder/case-versions/${VERSION_ID}`,
    csrf: "same-session-token",
    body: JSON.stringify(draft)
  });
  assert.deepEqual(calls[1], {
    method: "POST",
    path: `/internal/admin/v1/case-versions/${VERSION_ID}/submit`,
    csrf: "same-session-token",
    body: null
  });
  assert.equal(calls.some((call) => /approve|publish|withdraw|reject/.test(call.path)), false);
});
