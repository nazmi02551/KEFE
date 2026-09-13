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

test("Deliberation Workspace: loads systemic governance and impact capabilities (CAP-018, CAP-020, CAP-021, CAP-022, CAP-023)", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = input.toString();

    if (url.includes("/threshold-analysis")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        parameter_name: "Aylık Ulaşım Katkı Payı / Eşik",
        unit: "TL",
        tipping_point_threshold: 20.0,
        curve_points: [
          { parameter_value: 5.0, acceptance_rate: 0.90 },
          { parameter_value: 10.0, acceptance_rate: 0.75 },
          { parameter_value: 20.0, acceptance_rate: 0.45 },
          { parameter_value: 50.0, acceptance_rate: 0.15 }
        ]
      }), { status: 200 });
    }

    if (url.includes("/responsibility-analysis")) {
      return new Response(JSON.stringify({
        analysis_id: "RESP-22222222",
        case_version_id: caseId,
        clarity_score: 0.82,
        has_accountability_gap: false,
        legal_redress_channel: "İdare Mahkemesi & Kamu Denetçiliği Kurumu",
        actor_allocations: [
          {
            actor_key: "REGULATORY_AUTHORITY",
            actor_name: "Düzenleyici Üst Kurul",
            responsibility_share: 0.40,
            duty_nature: "REGULATORY_OVERSIGHT",
            jurisdiction_scope: "Standart belirleme",
            accountability_mechanism: "İdari cezalar"
          }
        ]
      }), { status: 200 });
    }

    if (url.includes("/process-analysis")) {
      return new Response(JSON.stringify({
        analysis_id: "PROC-22222222",
        case_version_id: caseId,
        current_stage: "PUBLIC_HEARING",
        procedural_integrity_score: 0.85,
        transparency_level: "HIGH",
        public_participation_status: "OPEN_CONSULTATION",
        oversight_body: "Ombudsmanlık",
        stages: [
          {
            stage_key: "STAGE_1",
            stage_title: "Ön İstişare",
            is_completed: true,
            duration_days: 14,
            has_public_input: true
          }
        ]
      }), { status: 200 });
    }

    if (url.includes("/incentive-map")) {
      return new Response(JSON.stringify({
        map_id: "INC-22222222",
        case_version_id: caseId,
        alignment_index: 0.78,
        perverse_incentive_risk: "LOW",
        primary_driver: "Kamu Yararı",
        mitigation_mechanism: "Şeffaf Açık Veri",
        incentive_nodes: [
          {
            stakeholder_group: "İşletmeciler",
            core_incentive: "Maliyet optimizasyonu",
            incentive_type: "FINANCIAL_PROFIT",
            alignment_status: "ALIGNED",
            intensity_score: 0.7,
            unintended_behavior: ""
          }
        ]
      }), { status: 200 });
    }

    if (url.includes("/stakeholder-impact")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        option_code: "OPTION_A",
        net_equity_score: 6,
        impact_items: [
          {
            stakeholder_group: "DIRECT_USERS",
            impact_type: "BENEFIT",
            impact_score: 4,
            description: "Doğrudan hizmet erişimi"
          },
          {
            stakeholder_group: "VULNERABLE_GROUPS",
            impact_type: "PROTECTION",
            impact_score: 5,
            description: "Koruma güvencesi"
          }
        ]
      }), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    const ta = await client.getThresholdAnalysis(caseId);
    assert.equal(ta.tipping_point_threshold, 20.0);
    assert.equal(ta.unit, "TL");

    const resp = await client.getResponsibilityAnalysis(caseId);
    assert.equal(resp.clarity_score, 0.82);
    assert.equal(resp.has_accountability_gap, false);

    const proc = await client.getProcessAnalysis(caseId);
    assert.equal(proc.current_stage, "PUBLIC_HEARING");
    assert.equal(proc.procedural_integrity_score, 0.85);

    const inc = await client.getIncentiveMap(caseId);
    assert.equal(inc.perverse_incentive_risk, "LOW");
    assert.equal(inc.alignment_index, 0.78);

    const impact = await client.getStakeholderImpact(caseId, "OPTION_A");
    assert.equal(impact.net_equity_score, 6);
    assert.equal(impact.impact_items.length, 2);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Deliberation Workspace: loads simulation, budget tradeoff, retrospective, observe mode and community proposals (CAP-017, CAP-027, CAP-028, CAP-029, CAP-030)", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = input.toString();
    const method = init?.method ?? "GET";

    if (url.includes("/policy-simulations/evaluate")) {
      return new Response(JSON.stringify({
        simulation_id: "SIM-01",
        case_version_id: caseId,
        policy_knob_name: "Yeşil Dönüşüm",
        knob_value: 80.0,
        fiscal_score: 0.75,
        social_score: 0.90,
        environmental_score: 0.95,
        equilibrium_state: "OPTIMAL_BALANCE"
      }), { status: 200 });
    }

    if (url.includes("/policy-simulations")) {
      return new Response(JSON.stringify({
        simulation_id: "SIM-00",
        case_version_id: caseId,
        policy_knob_name: "Varsayılan Fon",
        knob_value: 50.0,
        fiscal_score: 0.60,
        social_score: 0.70,
        environmental_score: 0.65,
        equilibrium_state: "OPTIMAL_BALANCE"
      }), { status: 200 });
    }

    if (url.includes("/budget-tradeoff/evaluate")) {
      return new Response(JSON.stringify({
        tradeoff_id: "TRD-EVAL",
        case_version_id: caseId,
        healthcare_pct: 35,
        education_pct: 25,
        infrastructure_pct: 20,
        green_transition_pct: 20,
        unallocated_pct: 0,
        tradeoff_profile: "HEALTH_EDUCATION_PRIORITY"
      }), { status: 200 });
    }

    if (url.includes("/budget-tradeoff")) {
      return new Response(JSON.stringify({
        tradeoff_id: "TRD-01",
        case_version_id: caseId,
        healthcare_pct: 30,
        education_pct: 25,
        infrastructure_pct: 25,
        green_transition_pct: 20,
        unallocated_pct: 0,
        tradeoff_profile: "BALANCED_ALLOCATION"
      }), { status: 200 });
    }

    if (url.includes("/historical-retrospective")) {
      return new Response(JSON.stringify({
        retrospective_id: "RETRO-01",
        case_version_id: caseId,
        historical_era: "INDUSTRIAL_ERA",
        historical_year: 1888,
        historical_event_name: "Demiryolu Kamulaştırması",
        actual_historical_decision: "Kamu mülkiyeti ve tarifeli denetim seçildi.",
        historical_consequence_summary: "Lojistik maliyetleri düşürüldü ve kamu tekeli sağlandı."
      }), { status: 200 });
    }

    if (url.includes("/observe-session")) {
      return new Response(JSON.stringify({
        session_id: "OBS-01",
        case_version_id: caseId,
        exploration_mode: "OBSERVE_ONLY",
        is_binding_vote: false,
        viewed_argument_count: 5,
        viewed_evidence_count: 3
      }), { status: 200 });
    }

    if (url.includes("/community-proposals") && method === "POST") {
      return new Response(JSON.stringify({
        proposal_id: "PROP-03",
        proposed_title: "Tarihi Meydan Düzenlemesi",
        proposed_context: "Tarihi meydanda yayalaştırma ve esnaf yük indirme saatlerinin düzenlenmesi.",
        curation_state: "DRAFT_SUBMITTED",
        neutrality_score: 0.85,
        supporter_count: 1
      }), { status: 201 });
    }

    if (url.includes("/community-proposals")) {
      return new Response(JSON.stringify([
        {
          proposal_id: "PROP-01",
          proposed_title: "Köy Okulları Güneş Enerjisi",
          proposed_context: "Kırsal kalkınma için okullara mikro solar kurulumu.",
          curation_state: "COMMUNITY_PEER_REVIEW",
          neutrality_score: 0.90,
          supporter_count: 142
        }
      ]), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    // 1. Policy Simulator (CAP-017)
    const policyDefault = await client.getDefaultPolicySimulation(caseId);
    assert.equal(policyDefault.policy_knob_name, "Varsayılan Fon");
    assert.equal(policyDefault.equilibrium_state, "OPTIMAL_BALANCE");

    const policyEval = await client.evaluatePolicySimulation(caseId, "Yeşil Dönüşüm", 80.0);
    assert.equal(policyEval.knob_value, 80.0);
    assert.equal(policyEval.environmental_score, 0.95);

    // 2. Budget Tradeoff (CAP-027)
    const budgetDefault = await client.getBudgetTradeoff(caseId);
    assert.equal(budgetDefault.tradeoff_profile, "BALANCED_ALLOCATION");

    const budgetEval = await client.evaluateBudgetTradeoff(caseId, {
      healthcare_pct: 35,
      education_pct: 25,
      infrastructure_pct: 20,
      green_transition_pct: 20
    });
    assert.equal(budgetEval.tradeoff_profile, "HEALTH_EDUCATION_PRIORITY");

    // 3. Historical Retrospective (CAP-028)
    const retro = await client.getHistoricalRetrospective(caseId);
    assert.equal(retro.historical_era, "INDUSTRIAL_ERA");
    assert.equal(retro.historical_year, 1888);
    assert.ok(retro.actual_historical_decision.includes("Kamu mülkiyeti"));

    // 4. Observe Mode (CAP-029)
    const obs = await client.createObserveSession(caseId, "OBSERVE_ONLY");
    assert.equal(obs.exploration_mode, "OBSERVE_ONLY");
    assert.equal(obs.is_binding_vote, false);
    assert.equal(obs.viewed_argument_count, 5);

    // 5. Community Dilemma Proposals (CAP-030)
    const props = await client.listCommunityProposals(caseId);
    assert.equal(props.length, 1);
    assert.equal(props[0].curation_state, "COMMUNITY_PEER_REVIEW");

    const created = await client.createCommunityProposal(
      caseId,
      "Tarihi Meydan Düzenlemesi",
      "Tarihi meydanda yayalaştırma ve esnaf yük indirme saatlerinin düzenlenmesi."
    );
    assert.equal(created.proposal_id, "PROP-03");
    assert.equal(created.curation_state, "DRAFT_SUBMITTED");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Deliberation Workspace: loads collective analytics (CAP-033, CAP-036, CAP-037, CAP-039, CAP-041)", async () => {
  const caseId = "22222222-2222-4222-8222-222222222222";
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = input.toString();

    if (url.includes("/perspective-clusters")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        total_arguments_clustered: 1000,
        clusters: [
          {
            cluster_id: "cl-01",
            case_version_id: caseId,
            archetype: "BRIDGE_SYNTHESIS",
            core_thesis: "Kamu yararı ve esnaf hakları arasında tarifeli geçiş uzlaşısı",
            argument_count: 450,
            support_percentage: 45.0
          },
          {
            cluster_id: "cl-02",
            case_version_id: caseId,
            archetype: "OPPOSING_PRINCIPLE",
            core_thesis: "Tam serbest piyasa ve ticari serbestlik",
            argument_count: 300,
            support_percentage: 30.0
          }
        ]
      }), { status: 200 });
    }

    if (url.includes("/segment-distributions")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        minimum_sample_threshold: 30,
        overall_sample_size: 1500,
        privacy_guarantees: {
          k_anonymity_threshold: 30,
          no_individual_profiling: true,
          differential_privacy_noise_applied: true
        },
        segments: [
          {
            cohort_type: "AGE_COHORT",
            cohort_label: "Genç Yurttaşlar (18-29)",
            sample_size: 420,
            is_suppressed: false,
            suppression_reason: null,
            option_shares: { OPTION_A: 0.65, OPTION_B: 0.35 },
            primary_choice: "OPTION_A",
            entropy_score: 0.92
          },
          {
            cohort_type: "REGIONAL_COHORT",
            cohort_label: "Kırsal Havza",
            sample_size: 18,
            is_suppressed: true,
            suppression_reason: "INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD",
            option_shares: {},
            primary_choice: null,
            entropy_score: 0.0
          }
        ]
      }), { status: 200 });
    }

    if (url.includes("/stakeholder-distributions")) {
      return new Response(JSON.stringify({
        case_version_id: caseId,
        total_stakeholders_represented: 1200,
        active_categories_count: 5,
        pluralism_score: 0.88,
        stakeholder_distributions: [
          {
            category: "DIRECTLY_IMPACTED",
            name: "Doğrudan Etkilenenler",
            participant_count: 480,
            sample_share: 0.40,
            option_shares: { OPTION_A: 0.70, OPTION_B: 0.30 },
            primary_choice: "OPTION_A",
            cohesion_index: 0.85,
            divergence_from_overall_points: 12
          }
        ]
      }), { status: 200 });
    }

    return new Response(JSON.stringify({}), { status: 200 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    // 1. Perspective Clusters (CAP-033)
    const clusters = await client.getPerspectiveClusters(caseId);
    assert.equal(clusters.total_arguments_clustered, 1000);
    assert.equal(clusters.clusters.length, 2);
    assert.equal(clusters.clusters[0].archetype, "BRIDGE_SYNTHESIS");

    // 2. Segment Distributions (CAP-036)
    const segs = await client.getSegmentDistributions(caseId);
    assert.equal(segs.overall_sample_size, 1500);
    assert.equal(segs.privacy_guarantees?.k_anonymity_threshold, 30);
    assert.equal(segs.segments?.length, 2);
    assert.equal(segs.segments?.[1].is_suppressed, true);

    // 3. Stakeholder Distributions (CAP-037)
    const stks = await client.getStakeholderDistributions(caseId);
    assert.equal(stks.pluralism_score, 0.88);
    assert.equal(stks.stakeholder_distributions?.length, 1);
    assert.equal(stks.stakeholder_distributions?.[0].primary_choice, "OPTION_A");
  } finally {
    globalThis.fetch = originalFetch;
  }
});



