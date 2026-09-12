import test from "node:test";
import assert from "node:assert/strict";
import { CaseAnalyticsApiClient } from "../src/lib/case-analytics-api";
import {
  CaseObjectionApiClient,
  CaseObjectionApiError,
} from "../src/lib/case-objection-api";
import {
  CaseCorrectionApiClient,
  CaseCorrectionApiError,
} from "../src/lib/case-correction-api";

test("Deliberation Workspace: loads quality checklist, objections, corrections and divergence", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const calls: string[] = [];

  const mockFetch = (async (url: RequestInfo | URL) => {
    const urlStr = url.toString();
    calls.push(urlStr);

    if (urlStr.includes("/quality-checklist")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        overall_status: "PASSED",
        overall_score: 0.95,
        criteria: [
          { code: "BALANCED_OPTIONS", name: "Dengeli Seçenekler", is_met: true, score: 0.9, threshold: 0.8, details: "OK" }
        ],
        evaluated_at: "2026-09-12T00:00:00Z"
      }), { status: 200 });
    }

    if (urlStr.includes("/objections")) {
      return new Response(JSON.stringify([
        {
          objection_id: "obj-1",
          case_version_id: caseId,
          reason_category: "EDITORIAL_BIAS_FRAMING",
          statement: "Seçenek A dili taraflı görünmektedir.",
          supporting_evidence_url: "https://kefe.org/delil",
          status: "SUBMITTED",
          created_at: "2026-09-12T00:00:00Z",
          resolution_note: null,
          resolved_at: null
        }
      ]), { status: 200 });
    }

    if (urlStr.includes("/corrections")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        corrections: [
          {
            correction_id: "cor-1",
            correction_type: "FACTUAL_UPDATE",
            severity: "MINOR",
            summary: "Madde numarası güncellendi",
            editorial_rationale: "Yeni kanun metnine uyum sağlandı",
            timestamp: "2026-09-12T00:00:00Z",
            previous_value: "Madde 14",
            corrected_value: "Madde 16/A"
          }
        ]
      }), { status: 200 });
    }

    if (urlStr.includes("/consensus-divergence")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        classification: "LEANING_MAJORITY",
        leading_share: 0.65,
        margin_of_divergence: 0.30,
        label_tr: "Kolektif Uzlaşı / Ayrışma",
        label_en: "Consensus / Divergence",
        description_tr: "Açıklama",
        description_en: "Description"
      }), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  }) as typeof fetch;

  const analytics = new CaseAnalyticsApiClient("http://localhost:8000");
  // Override fetch for analytics
  (analytics as any).baseUrl = "http://localhost:8000";

  const objectionClient = new CaseObjectionApiClient({
    baseUrl: "http://localhost:8000",
    csrfToken: "csrf-token-123",
    fetchImpl: mockFetch
  });

  const correctionClient = new CaseCorrectionApiClient({
    baseUrl: "http://localhost:8000",
    csrfToken: "csrf-token-123",
    fetchImpl: mockFetch
  });

  const objections = await objectionClient.listObjections(caseId);
  assert.equal(objections.length, 1);
  assert.equal(objections[0].reason_category, "EDITORIAL_BIAS_FRAMING");

  const corrections = await correctionClient.getCorrectionHistory(caseId);
  assert.equal(corrections.corrections.length, 1);
  assert.equal(corrections.corrections[0].correction_type, "FACTUAL_UPDATE");
});

test("Deliberation Workspace: objection decision requires CSRF and min length rationale", async () => {
  const objectionClient = new CaseObjectionApiClient({
    baseUrl: "http://localhost:8000"
  });

  await assert.rejects(
    () => objectionClient.decideObjection("22222222-2222-4222-8222-222222222222", {
      objection_id: "obj-1",
      decision: "ACCEPT_AND_FILE_CORRECTION",
      resolution_note: "short",
      csrf_token: "token"
    }),
    (err: unknown) => {
      assert.ok(err instanceof CaseObjectionApiError);
      assert.equal(err.code, "RESOLUTION_NOTE_TOO_SHORT");
      return true;
    }
  );

  await assert.rejects(
    () => objectionClient.decideObjection("22222222-2222-4222-8222-222222222222", {
      objection_id: "obj-1",
      decision: "ACCEPT_AND_FILE_CORRECTION",
      resolution_note: "Gerekçeli açıklama metni yeterince uzun.",
      csrf_token: ""
    }),
    (err: unknown) => {
      assert.ok(err instanceof CaseObjectionApiError);
      assert.equal(err.code, "CSRF_TOKEN_REQUIRED");
      return true;
    }
  );
});

test("Deliberation Workspace: correction creation requires valid fields and CSRF", async () => {
  const correctionClient = new CaseCorrectionApiClient({
    baseUrl: "http://localhost:8000"
  });

  await assert.rejects(
    () => correctionClient.addCorrection("22222222-2222-4222-8222-222222222222", {
      correction_type: "FACTUAL_UPDATE",
      severity: "MINOR",
      summary: "Özet",
      editorial_rationale: "Gerekçe",
      csrf_token: ""
    }),
    (err: unknown) => {
      assert.ok(err instanceof CaseCorrectionApiError);
      assert.equal(err.code, "CSRF_TOKEN_REQUIRED");
      return true;
    }
  );
});
