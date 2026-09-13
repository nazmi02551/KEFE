import test from "node:test";
import assert from "node:assert/strict";
import { CaseAnalyticsApiClient } from "../src/lib/case-analytics-api";
import { AdminApiError } from "../src/lib/admin-api";

test("CaseAnalyticsApiClient validates baseUrl securely", () => {
  // Valid local URLs
  assert.doesNotThrow(() => new CaseAnalyticsApiClient("http://localhost:8000"));
  assert.doesNotThrow(() => new CaseAnalyticsApiClient("http://127.0.0.1:8000"));
  assert.doesNotThrow(() => new CaseAnalyticsApiClient("https://api.kefe.org"));

  // Insecure remote HTTP throws
  assert.throws(
    () => new CaseAnalyticsApiClient("http://insecure-remote.kefe.org"),
    (err: unknown) => err instanceof AdminApiError && err.status === 400
  );
});

test("CaseAnalyticsApiClient validates policy evaluation input parameters", async () => {
  const client = new CaseAnalyticsApiClient("http://localhost:8000");

  await assert.rejects(
    () => client.evaluatePolicySimulation("test-case", "Knob", -5),
    (err: unknown) => err instanceof AdminApiError && err.message.includes("between 0.0 and 100.0")
  );

  await assert.rejects(
    () => client.evaluatePolicySimulation("test-case", "Knob", 105),
    (err: unknown) => err instanceof AdminApiError && err.message.includes("between 0.0 and 100.0")
  );

  await assert.rejects(
    () => client.evaluatePolicySimulation("test-case", "ab", 50),
    (err: unknown) => err instanceof AdminApiError && err.message.includes("at least 3 characters")
  );
});

test("CaseAnalyticsApiClient mocked GET and POST requests", async () => {
  const originalFetch = globalThis.fetch;
  const calls: Array<{ url: string; method: string; body?: string }> = [];

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = input.toString();
    const method = init?.method ?? "GET";
    const body = init?.body ? String(init.body) : undefined;
    calls.push({ url, method, body });

    if (url.includes("/quality-checklist")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        overall_status: "PASSED",
        overall_score: 95,
        criteria: [],
        evaluated_at: "2026-09-12T00:00:00Z"
      }), { status: 200 });
    }

    if (url.includes("/consensus-divergence")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        classification: "BROAD_CONSENSUS",
        leading_share: 0.75,
        margin_of_divergence: 0.50,
        label_tr: "Kolektif Uzlaşı",
        label_en: "Collective Consensus",
        description_tr: "Açıklama",
        description_en: "Description"
      }), { status: 200 });
    }

    if (url.includes("/expert-public-gap")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        gap_classification: "CONVERGENT",
        gap_score: 0.15,
        expert_consensus_share: 0.80,
        public_consensus_share: 0.75,
        friction_points: [],
        divergence_drivers: []
      }), { status: 200 });
    }

    if (url.includes("/incentive-map")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        incentives: []
      }), { status: 200 });
    }

    if (url.includes("/normative-models")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        evaluations: [],
        philosophies_explained_tr: {},
        philosophies_explained_en: {}
      }), { status: 200 });
    }

    if (url.includes("/perspective-clusters")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        total_arguments_clustered: 1000,
        clusters: []
      }), { status: 200 });
    }

    if (url.includes("/policy-simulations/evaluate")) {
      return new Response(JSON.stringify({
        simulation_id: "SIM-test",
        case_version_id: "test-case",
        policy_knob_name: "Subsidies",
        knob_value: 60,
        fiscal_score: 0.6,
        social_score: 0.8,
        environmental_score: 0.7,
        equilibrium_state: "BALANCED"
      }), { status: 200 });
    }

    if (url.includes("/policy-simulations")) {
      return new Response(JSON.stringify({
        simulation_id: "SIM-default",
        case_version_id: "test-case",
        policy_knob_name: "Default",
        knob_value: 50,
        fiscal_score: 0.7,
        social_score: 0.8,
        environmental_score: 0.6,
        equilibrium_state: "STABLE"
      }), { status: 200 });
    }

    if (url.includes("/process-analysis")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        procedural_fairness_score: 0.9,
        stakeholder_inclusion_score: 0.85,
        institutional_transparency_score: 0.88,
        deliberation_verdict: "FAIR"
      }), { status: 200 });
    }

    if (url.includes("/responsibility-analysis")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        duty_bearers: []
      }), { status: 200 });
    }

    if (url.includes("/segment-distributions")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        k_anonymity_floor: 30,
        cohorts: []
      }), { status: 200 });
    }

    if (url.includes("/stakeholder-distributions")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        stakeholder_groups: []
      }), { status: 200 });
    }

    if (url.includes("/budget-tradeoff/evaluate")) {
      return new Response(JSON.stringify({
        tradeoff_id: "TRD-test",
        case_version_id: "test-case",
        healthcare_pct: 30,
        education_pct: 25,
        infrastructure_pct: 25,
        green_transition_pct: 20,
        unallocated_pct: 0,
        tradeoff_profile: "BALANCED_ALLOCATION"
      }), { status: 200 });
    }

    if (url.includes("/budget-tradeoff")) {
      return new Response(JSON.stringify({
        tradeoff_id: "TRD-default",
        case_version_id: "test-case",
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
        case_version_id: "test-case",
        historical_era: "INDUSTRIAL_ERA",
        historical_year: 1888,
        historical_event_name: "Demiryolu Kamulaştırması",
        actual_historical_decision: "Kamu mülkiyeti seçildi.",
        historical_consequence_summary: "Maliyetler düştü."
      }), { status: 200 });
    }

    if (url.includes("/observe-session")) {
      return new Response(JSON.stringify({
        session_id: "OBS-01",
        case_version_id: "test-case",
        exploration_mode: "OBSERVE_ONLY",
        is_binding_vote: false,
        viewed_argument_count: 0,
        viewed_evidence_count: 0
      }), { status: 200 });
    }

    if (url.includes("/community-proposals") && method === "POST") {
      return new Response(JSON.stringify({
        proposal_id: "PROP-02",
        proposed_title: "Yeni Yaya Yolu",
        proposed_context: "Yayalaştırma projesi teklifi.",
        curation_state: "DRAFT_SUBMITTED",
        neutrality_score: 0.75,
        supporter_count: 1
      }), { status: 201 });
    }

    if (url.includes("/community-proposals")) {
      return new Response(JSON.stringify([
        {
          proposal_id: "PROP-01",
          proposed_title: "Gece Seferleri",
          proposed_context: "Ücretsiz sefer talebi.",
          curation_state: "COMMUNITY_PEER_REVIEW",
          neutrality_score: 0.85,
          supporter_count: 142
        }
      ]), { status: 200 });
    }

    if (url.includes("/blind-variants")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        blind_mode: "ACTOR_BLIND",
        blinded_prompt: "A generic entity...",
        real_identity_revealed: "Rail Authority",
        neutrality_score: 0.88,
        capability_id: "CAP-005"
      }), { status: 200 });
    }

    if (url.includes("/principle-first")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
        primary_principle: "COLLECTIVE_WELLBEING",
        secondary_principle: "PROCEDURAL_JUSTICE",
        consistency_score: 0.91,
        reflection_prompt: "Does prioritizing wellbeing compromise autonomy?",
        capability_id: "CAP-006"
      }), { status: 200 });
    }

    if (url.includes("/decision-receipt")) {
      return new Response(JSON.stringify({
        receipt_id: "RCPT-001",
        case_version_id: "test-case",
        committed_choice: "OPTION_A",
        integrity_digest: "sha256-abc123",
        timestamp_utc: "2026-09-12T00:00:00Z",
        capability_id: "CAP-012"
      }), { status: 200 });
    }

    if (url.includes("/outcome-triangle")) {
      return new Response(JSON.stringify({
        case_version_id: "test-case",
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
        case_version_id: "test-case",
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

    return new Response(JSON.stringify({ error: "Not found" }), { status: 404 });
  };

  try {
    const client = new CaseAnalyticsApiClient("http://localhost:8000");

    const q = await client.getQualityChecklist("test-case");
    assert.equal(q.overall_status, "PASSED");

    const cd = await client.getConsensusDivergence("test-case", JSON.stringify({ a: 0.6, b: 0.4 }));
    assert.equal(cd.classification, "BROAD_CONSENSUS");

    const epg = await client.getExpertPublicGap("test-case");
    assert.equal(epg.gap_classification, "CONVERGENT");

    const inc = await client.getIncentiveMap("test-case");
    assert.ok(Array.isArray(inc.incentives));

    const norm = await client.getNormativeModels("test-case");
    assert.ok(norm.case_version_id);

    const pc = await client.getPerspectiveClusters("test-case");
    assert.equal(pc.total_arguments_clustered, 1000);

    const defSim = await client.getDefaultPolicySimulation("test-case");
    assert.equal(defSim.equilibrium_state, "STABLE");

    const evalSim = await client.evaluatePolicySimulation("test-case", "Subsidies", 60);
    assert.equal(evalSim.knob_value, 60);

    const pa = await client.getProcessAnalysis("test-case");
    assert.equal(pa.deliberation_verdict, "FAIR");

    const resp = await client.getResponsibilityAnalysis("test-case");
    assert.ok(Array.isArray(resp.duty_bearers));

    const seg = await client.getSegmentDistributions("test-case");
    assert.equal(seg.k_anonymity_floor, 30);

    const st = await client.getStakeholderDistributions("test-case");
    assert.ok(Array.isArray(st.stakeholder_groups));

    const bt = await client.getBudgetTradeoff("test-case");
    assert.equal(bt.tradeoff_profile, "BALANCED_ALLOCATION");

    const evalBt = await client.evaluateBudgetTradeoff("test-case", {
      healthcare_pct: 30,
      education_pct: 25,
      infrastructure_pct: 25,
      green_transition_pct: 20
    });
    assert.equal(evalBt.healthcare_pct, 30);

    const retro = await client.getHistoricalRetrospective("test-case");
    assert.equal(retro.historical_era, "INDUSTRIAL_ERA");

    const obs = await client.createObserveSession("test-case");
    assert.equal(obs.is_binding_vote, false);

    const props = await client.listCommunityProposals("test-case");
    assert.equal(props.length, 1);

    const newProp = await client.createCommunityProposal(
      "test-case",
      "Yeni Yaya Yolu",
      "Yayalaştırma projesi teklifi."
    );
    assert.equal(newProp.curation_state, "DRAFT_SUBMITTED");

    const bv = await client.getBlindVariants("test-case");
    assert.equal(bv.blind_mode, "ACTOR_BLIND");
    assert.equal(bv.capability_id, "CAP-005");

    const pf = await client.getPrincipleFirst("test-case");
    assert.equal(pf.primary_principle, "COLLECTIVE_WELLBEING");
    assert.equal(pf.capability_id, "CAP-006");

    const dr = await client.getDecisionReceipt("test-case");
    assert.equal(dr.committed_choice, "OPTION_A");
    assert.equal(dr.capability_id, "CAP-012");

    const ot = await client.getOutcomeTriangle("test-case");
    assert.equal(ot.dominant_archetype, "RULES_FIRST");
    assert.equal(ot.capability_id, "CAP-102");

    const ii = await client.getInsufficientInfoReport("test-case");
    assert.equal(ii.total_opt_outs, 48);
    assert.equal(ii.preserves_commit_first_isolation, true);

    assert.equal(calls.length, 23);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
