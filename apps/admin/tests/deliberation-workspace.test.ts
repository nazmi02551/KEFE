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

test("Deliberation Workspace: loads advanced deliberation capabilities (CAP-005, CAP-006, CAP-011, CAP-012, CAP-102)", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = input.toString();

    if (url.includes("/blind-variants")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        blind_mode: "ACTOR_BLIND",
        blinded_prompt: "Anonim bir kurum sübvansiyon talep ediyor.",
        real_identity_revealed: "Devlet Demiryolları İdaresi",
        neutrality_score: 0.88,
        capability_id: "CAP-005"
      }), { status: 200 });
    }

    if (url.includes("/principle-first")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        primary_principle: "COLLECTIVE_WELLBEING",
        secondary_principle: "PROCEDURAL_JUSTICE",
        consistency_score: 0.91,
        reflection_prompt: "Toplumsal fayda öncelenirken bireysel haklar nasıl korunur?",
        capability_id: "CAP-006"
      }), { status: 200 });
    }

    if (url.includes("/decision-receipt")) {
      return new Response(JSON.stringify({
        receipt_id: "RCPT-2222",
        case_version_id: caseId,
        committed_choice: "OPTION_A",
        integrity_digest: "sha256-abcdef123456",
        timestamp_utc: "2026-09-12T12:00:00Z",
        capability_id: "CAP-012"
      }), { status: 200 });
    }

    if (url.includes("/outcome-triangle")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        option_code: "OPTION_A",
        rules_weight: 0.45,
        empathy_weight: 0.35,
        utility_weight: 0.20,
        dominant_archetype: "RULES_FIRST",
        capability_id: "CAP-102"
      }), { status: 200 });
    }

    if (url.includes("/insufficient-info-report")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        contract_id: "KEFE-INSUFFICIENT-INFO-RESPONSE-001",
        capabilities: ["CAP-011"],
        total_opt_outs: 48,
        breakdown: [
          {
            code: "OPT_OUT_INSUFFICIENT_INFO",
            count: 32,
            percentage: 66.7,
            description_tr: "Yeterli bilgim olmadığı için tercih belirtmedim"
          }
        ],
        preserves_commit_first_isolation: true
      }), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    const bv = await client.getBlindVariants(caseId);
    assert.equal(bv.blind_mode, "ACTOR_BLIND");
    assert.equal(bv.capability_id, "CAP-005");

    const pf = await client.getPrincipleFirst(caseId);
    assert.equal(pf.primary_principle, "COLLECTIVE_WELLBEING");
    assert.equal(pf.capability_id, "CAP-006");

    const dr = await client.getDecisionReceipt(caseId);
    assert.equal(dr.committed_choice, "OPTION_A");
    assert.equal(dr.capability_id, "CAP-012");

    const ot = await client.getOutcomeTriangle(caseId);
    assert.equal(ot.dominant_archetype, "RULES_FIRST");
    assert.equal(ot.capability_id, "CAP-102");

    const ii = await client.getInsufficientInfoReport(caseId);
    assert.equal(ii.total_opt_outs, 48);
    assert.equal(ii.preserves_commit_first_isolation, true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Deliberation Workspace: loads Wave 5 synthesis and divergence capabilities (CAP-007, CAP-010, CAP-034, CAP-038, CAP-040)", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = input.toString();

    if (url.includes("/role-flip")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        initial_role: "Tesis Sahibi / Sanayici",
        flipped_role: "Bölge Sakini / Temiz Su Tüketicisi",
        flipped_scenario_prompt: "Şimdi fabrikanın atık boşalttığı nehir kıyısında yaşayan bir köylü olduğunuzu hayal edin.",
        perspective_shift_score: 0.74,
        capability_id: "CAP-007"
      }), { status: 200 });
    }

    if (url.includes("/change-mind-inquiry")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        flexibility_class: "HIGHLY_EPISTEMIC_OPEN",
        selected_conditions: [
          {
            condition_type: "EMPIRICAL_DATA_THRESHOLD",
            description: "Kaza ve arıza oranlarında %20'den fazla azalma kanıtlanırsa."
          }
        ],
        capability_id: "CAP-010"
      }), { status: 200 });
    }

    if (url.includes("/bridge-arguments")) {
      return new Response(JSON.stringify([
        {
          bridge_id: "BRG-01",
          case_version_id: caseId,
          synthesis_thesis: "Kademeli geçiş kamu mülkiyeti ile sürdürülebilirliği birleştirir.",
          connecting_values: ["kamusal_denetim", "ulasilabilirlik"],
          cross_group_support_rate: 0.62,
          sample_size: 120,
          capability_id: "CAP-034"
        }
      ]), { status: 200 });
    }

    if (url.includes("/stakeholder-gap")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        segment_key: "DIRECTLY_AFFECTED",
        target_option: "A",
        gap_points: 16,
        sample_size: 145,
        segment_distributions: { A: 0.74, B: 0.26 },
        k_anonymity_satisfied: true,
        capability_id: "CAP-038"
      }), { status: 200 });
    }

    if (url.includes("/divergence-anatomy")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        primary_driver: "NORMATIVE_VALUE_WEIGHT",
        drivers: [
          {
            driver_type: "NORMATIVE_VALUE_WEIGHT",
            share_percentage: 52.0,
            explanation: "Ahlaki önceliklendirme farkı."
          }
        ],
        capability_id: "CAP-040"
      }), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    const rf = await client.getRoleFlip(caseId);
    assert.equal(rf.initial_role, "Tesis Sahibi / Sanayici");
    assert.equal(rf.capability_id, "CAP-007");

    const cm = await client.getChangeMindInquiry(caseId);
    assert.equal(cm.flexibility_class, "HIGHLY_EPISTEMIC_OPEN");
    assert.equal(cm.capability_id, "CAP-010");

    const ba = await client.getBridgeArguments(caseId);
    assert.equal(ba.length, 1);
    assert.equal(ba[0].capability_id, "CAP-034");

    const sg = await client.getStakeholderGap(caseId);
    assert.equal(sg.gap_points, 16);
    assert.equal(sg.capability_id, "CAP-038");

    const da = await client.getDivergenceAnatomy(caseId);
    assert.equal(da.primary_driver, "NORMATIVE_VALUE_WEIGHT");
    assert.equal(da.capability_id, "CAP-040");
  } finally {
    globalThis.fetch = originalFetch;
  }
});


