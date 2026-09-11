import test from "node:test";
import assert from "node:assert/strict";

import {
  CaseObjectionApiClient,
  CaseObjectionApiError,
} from "../src/lib/case-objection-api.ts";
import {
  CaseCorrectionApiClient,
  CaseCorrectionApiError,
} from "../src/lib/case-correction-api.ts";

test("CaseObjectionApiClient validates insecure URL and missing CSRF", async () => {
  assert.throws(
    () => new CaseObjectionApiClient({ baseUrl: "http://remote-api.kefe.org" }),
    (err: unknown) => {
      assert(err instanceof CaseObjectionApiError);
      assert.equal(err.code, "ADMIN_API_BASE_INSECURE");
      return true;
    }
  );

  const client = new CaseObjectionApiClient({ baseUrl: "http://localhost:8000" });
  await assert.rejects(
    () =>
      client.decideObjection("11111111-1111-4111-8111-111111111111", {
        objection_id: "22222222-2222-4222-8222-222222222222",
        decision: "REJECT_WITH_REASON",
        resolution_note: "Gerekçe yeterli ve doğrulanabilir değil.",
        csrf_token: "",
      }),
    (err: unknown) => {
      assert(err instanceof CaseObjectionApiError);
      assert.equal(err.code, "CSRF_TOKEN_REQUIRED");
      return true;
    }
  );
});

test("CaseCorrectionApiClient validates baseUrl and enforces summary/rationale length", async () => {
  const client = new CaseCorrectionApiClient({
    baseUrl: "http://localhost:8000",
    csrfToken: "valid-csrf-token",
  });

  await assert.rejects(
    () =>
      client.addCorrection("11111111-1111-4111-8111-111111111111", {
        correction_type: "TYPO_FIX",
        severity: "MINOR",
        summary: "a", // too short
        editorial_rationale: "Geçerli ve yeterli uzunlukta editoryal gerekçe.",
        csrf_token: "valid-csrf-token",
      }),
    (err: unknown) => {
      assert(err instanceof CaseCorrectionApiError);
      assert.equal(err.code, "SUMMARY_TOO_SHORT");
      return true;
    }
  );
});
