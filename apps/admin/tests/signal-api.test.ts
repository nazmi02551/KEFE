import test from "node:test";
import assert from "node:assert/strict";
import {
  listSignalConsensusCards,
  getSignalHealthReport,
  getSignalQualificationReport,
  getContributionClassesReport,
  getSignalScopeAlignmentReport,
  getSignalVersioningReport,
  getSignalTargetRegistry
} from "../src/lib/signal-api";

test("listSignalConsensusCards calls GET endpoint with pagination", async () => {
  const calls: string[] = [];
  const mockFetch = (async (url: RequestInfo | URL) => {
    calls.push(url.toString());
    return new Response(JSON.stringify([
      {
        signal_id: "SIG-001",
        case_version_id: "CASE-001",
        case_title: "Toplu Taşıma Fiyatlandırması",
        consensus_statement: "Halk çoğunluğu sübvansiyonu destekliyor.",
        agreement_percentage: 78.5,
        sample_size: 450,
        confidence_tier: "GOLD_STANDARD",
        certified_at: "2026-09-12T00:00:00Z",
        qualification_tier: "CERTIFIED"
      }
    ]), { status: 200 });
  }) as typeof fetch;

  const cards = await listSignalConsensusCards("http://localhost:8000", { limit: 10, offset: 5, fetchImpl: mockFetch });
  assert.equal(calls.length, 1);
  assert.ok(calls[0].includes("/v1/signals/consensus-cards?limit=10&offset=5"));
  assert.equal(cards.length, 1);
  assert.equal(cards[0].signal_id, "SIG-001");
  assert.equal(cards[0].confidence_tier, "GOLD_STANDARD");
});

test("getSignalHealthReport returns dimension health scores", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      signal_id: "SIG-001",
      case_version_id: "CASE-001",
      overall_qualification: "HEALTHY",
      overall_health_score: 92,
      sample_size: 450,
      dimensions: [
        {
          dimension_id: "sample_sufficiency",
          title_tr: "Örneklem Yeterliliği",
          title_en: "Sample Sufficiency",
          score: 95,
          threshold: 80,
          is_passed: true,
          detail: "n >= 300 eşiği aşıldı."
        }
      ],
      certified_at: "2026-09-12T00:00:00Z",
      methodology_hash: "sha256:abc"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getSignalHealthReport("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.overall_health_score, 92);
  assert.equal(res.dimensions[0].is_passed, true);
});

test("getSignalQualificationReport returns qualification criteria", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      signal_id: "SIG-001",
      case_version_id: "CASE-001",
      case_title: "Test Case",
      qualification_status: "QUALIFIED",
      qualification_tier: "GOLD",
      overall_score: 94,
      sample_size: 500,
      criteria: [],
      eligible_channels: ["PUBLIC_OBSERVATORY", "DECISION_MAKERS"],
      certified_at: "2026-09-12T00:00:00Z",
      qualification_audit_hash: "sha256:qual"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getSignalQualificationReport("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.qualification_status, "QUALIFIED");
  assert.equal(res.qualification_tier, "GOLD");
});

test("getContributionClassesReport returns isolated classes", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      case_version_id: "CASE-001",
      total_contributions: 600,
      classes: [
        {
          class_id: "CORE_PRE_RESULT",
          name_tr: "Sonuç Öncesi Birincil Katkı",
          name_en: "Core Pre-Result Contribution",
          count: 450,
          percentage: 75.0,
          is_signal_eligible: true,
          description: "Kör karar aşamasında verilen kararlar."
        }
      ],
      contamination_risk_index: 0.0,
      isolation_audit_status: "VERIFIED_ISOLATED",
      certified_at: "2026-09-12T00:00:00Z",
      isolation_proof_hash: "sha256:iso"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getContributionClassesReport("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.total_contributions, 600);
  assert.equal(res.contamination_risk_index, 0.0);
  assert.equal(res.classes[0].is_signal_eligible, true);
});

test("getSignalScopeAlignmentReport returns scope dimensions", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      signal_id: "SIG-001",
      case_version_id: "CASE-001",
      jurisdiction_level: "MUNICIPAL",
      target_population: "İzmir Genel",
      geographic_scope: "TR-35",
      alignment_status: "ALIGNED",
      overall_alignment_score: 96,
      dimensions: [],
      validity_window_days: 90,
      certified_at: "2026-09-12T00:00:00Z",
      scope_seal_hash: "sha256:seal"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getSignalScopeAlignmentReport("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.alignment_status, "ALIGNED");
  assert.equal(res.validity_window_days, 90);
});

test("getSignalVersioningReport returns methodology versions and deltas", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      signal_id: "SIG-001",
      case_version_id: "CASE-001",
      current_version: "v2.0",
      current_methodology_hash: "sha256:v2",
      snapshots: [],
      latest_delta: null,
      audit_chain_valid: true,
      certified_at: "2026-09-12T00:00:00Z"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getSignalVersioningReport("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.current_version, "v2.0");
  assert.equal(res.audit_chain_valid, true);
});

test("getSignalTargetRegistry returns target institutions and channels", async () => {
  const mockFetch = (async () => {
    return new Response(JSON.stringify({
      signal_id: "SIG-001",
      case_version_id: "CASE-001",
      primary_target_id: "TGT-01",
      targets: [
        {
          target_id: "TGT-01",
          target_name: "Ulaşım Dairesi Başkanlığı",
          target_type: "MUNICIPAL_DEPARTMENT",
          jurisdiction_level: "MUNICIPAL",
          official_contact_channel: "kep@belediye.gov.tr",
          dispatch_status: "DISPATCHED",
          response_due_days: 15,
          dispatched_at: "2026-09-12T00:00:00Z",
          acknowledged_at: null
        }
      ],
      certified_at: "2026-09-12T00:00:00Z",
      registry_proof_hash: "sha256:reg"
    }), { status: 200 });
  }) as typeof fetch;

  const res = await getSignalTargetRegistry("http://localhost:8000", "SIG-001", mockFetch);
  assert.equal(res.primary_target_id, "TGT-01");
  assert.equal(res.targets[0].dispatch_status, "DISPATCHED");
});
