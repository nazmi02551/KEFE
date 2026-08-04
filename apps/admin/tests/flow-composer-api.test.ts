import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiClient, AdminApiError } from "../src/lib/admin-api";
import type { FlowComposerVersion } from "../src/lib/flow-composer";

const VERSION_ID = "33333333-3333-4333-8333-333333333333";

const version: FlowComposerVersion = {
  id: VERSION_ID,
  version_no: 2,
  state: "DRAFT",
  primitives: [
    {
      code: "CONTEXT",
      label_key: "primitive.context",
      payload_schema_ref: null,
      enabled: true
    }
  ],
  capabilities: [
    {
      code: "SOURCE_REVEAL",
      label_key: "capability.source_reveal",
      compatible_primitive_codes: ["CONTEXT"],
      config_schema_ref: null,
      enabled: true
    }
  ],
  flow_templates: [
    {
      code: "LINEAR",
      version_no: 1,
      label_key: "flow.linear",
      entry_step_code: "A",
      enabled: true,
      steps: [
        {
          code: "A",
          primitive_code: "CONTEXT",
          capability_codes: ["SOURCE_REVEAL"],
          next_step_codes: [],
          payload_schema_ref: null
        }
      ]
    }
  ],
  created_at: "2026-08-04T18:00:00Z",
  published_at: null,
  cloned_from_version_id: "77777777-7777-4777-8777-777777777777"
};

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

test("Flow Composer construction and exact reads never start a request early", async () => {
  const calls: Array<{ method: string; path: string; csrf: string | null }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      csrf: headers.get("X-KEFE-CSRF")
    });
    return url.pathname.endsWith("/audit")
      ? jsonResponse({ items: [] })
      : jsonResponse(version);
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  const loaded = await client.flowComposerVersion(VERSION_ID);
  assert.equal(loaded.state, "DRAFT");
  const audit = await client.flowComposerAudit(VERSION_ID);
  assert.deepEqual(audit.items, []);
  assert.deepEqual(calls, [
    {
      method: "GET",
      path: `/internal/admin/v1/flow-composer/configuration-versions/${VERSION_ID}`,
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/flow-composer/configuration-versions/${VERSION_ID}/audit`,
      csrf: null
    }
  ]);
});

test("Flow Composer writes fail closed before network without same-session CSRF", async () => {
  let networkCalls = 0;
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(version);
    }
  });

  await assert.rejects(
    client.createFlowComposerDraft(),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  await assert.rejects(
    client.saveFlowComposerVersion(VERSION_ID, {
      flow_templates: version.flow_templates
    }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("Flow Composer exposes separate create and save commands with no publication path", async () => {
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
    return jsonResponse(version, url.pathname.endsWith("/drafts") ? 201 : 200);
  };
  const client = new AdminApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });

  await client.createFlowComposerDraft();
  await client.saveFlowComposerVersion(VERSION_ID, {
    flow_templates: version.flow_templates
  });

  assert.deepEqual(calls[0], {
    method: "POST",
    path: "/internal/admin/v1/flow-composer/drafts",
    csrf: "same-session-token",
    body: null
  });
  assert.deepEqual(calls[1], {
    method: "PUT",
    path: `/internal/admin/v1/flow-composer/configuration-versions/${VERSION_ID}`,
    csrf: "same-session-token",
    body: JSON.stringify({ flow_templates: version.flow_templates })
  });
  assert.equal(
    calls.some((call) => /publish|rollback|supersede|case-versions/.test(call.path)),
    false
  );
});
