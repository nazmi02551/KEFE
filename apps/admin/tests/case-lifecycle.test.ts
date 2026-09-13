import test from "node:test";
import assert from "node:assert/strict";
import { CaseLifecycleApiClient } from "../src/lib/case-lifecycle-api";

test("CaseLifecycleApiClient retrieves published version status (CAP-079)", async () => {
  const client = new CaseLifecycleApiClient();
  const res = await client.getCaseLifecycle("case_ai_001");

  assert.equal(res.case_id, "case_ai_001");
  assert.equal(res.is_published, true);
  assert.ok(res.current_case_version_id);
  assert.ok(res.last_updated_at);
});

test("CaseLifecycleApiClient reconciles saved cases and detects version shifts", async () => {
  const client = new CaseLifecycleApiClient();
  const res = await client.reconcileSavedCases([
    { case_id: "case_ai_001", saved_version_id: "case_ai_001_v1" },
    { case_id: "case_edu_002", saved_version_id: "case_edu_002_v2" },
  ]);

  assert.equal(res.total_checked, 2);
  const shifted = res.results.find((r) => r.case_id === "case_ai_001");
  assert.ok(shifted);
  assert.equal(shifted?.has_update, true);
  assert.equal(shifted?.change_type, "VERSION_SHIFT");
});

test("CaseLifecycleApiClient throws on empty savedCases array", async () => {
  const client = new CaseLifecycleApiClient();
  await assert.rejects(
    async () => await client.reconcileSavedCases([]),
    /must not be empty/
  );
});
