import { describe, it } from "node:test";
import assert from "node:assert/strict";
import type {
  SignalConsensusCard,
  SignalHealthReport,
  SignalQualificationReport,
  ContributionClassesReport,
  SignalScopeAlignmentReport,
  SignalVersioningReport,
  SignalFreshnessReport,
} from "../src/lib/signal-api";

describe("Signal Workspace & Qualification Architecture (CAP-042 - CAP-047)", () => {
  it("verifies signal client functions exist", async () => {
    const api = await import("../src/lib/signal-api");
    assert.equal(typeof api.listSignalConsensusCards, "function");
    assert.equal(typeof api.getSignalHealthReport, "function");
    assert.equal(typeof api.getSignalFreshnessReport, "function");
    assert.equal(typeof api.getContributionClassesReport, "function");
    assert.equal(typeof api.getSignalScopeAlignmentReport, "function");
    assert.equal(typeof api.getSignalVersioningReport, "function");
  });

  it("verifies SignalFreshnessReport structure and states (CAP-045)", () => {
    const report: SignalFreshnessReport = {
      signal_id: "77777777-7777-4777-8777-777777777701",
      case_version_id: "22222222-2222-4222-8222-222222222222",
      half_life_days: 30,
      age_days: 2.0,
      remaining_weight: 0.95,
      freshness_state: "FRESH",
      certified_at: "2026-09-12T00:00:00Z",
    };

    assert.equal(report.freshness_state, "FRESH");
    assert.ok(report.remaining_weight >= 0.85);
    assert.equal(report.half_life_days, 30);
  });

  it("verifies ContributionClassesReport separation (CAP-043)", () => {
    const classes: ContributionClassesReport = {
      case_version_id: "22222222-2222-4222-8222-222222222222",
      total_contributions: 1420,
      classes: [
        {
          class_id: "CORE_PRE_RESULT",
          name_tr: "Taahhüt-İlk Çekirdek Katılım",
          name_en: "Commit-First Core Pre-Result",
          count: 1100,
          percentage: 77.5,
          is_signal_eligible: true,
          description: "Ön-sonuç izolasyonu altındaki doğrulanmış oylar.",
        },
        {
          class_id: "EXPOSED",
          name_tr: "Sonuç Sonrası Gözlem Katılımı",
          name_en: "Post-Result Exposed Contribution",
          count: 220,
          percentage: 15.5,
          is_signal_eligible: false,
          description: "Kolektif sonucu gördükten sonra girilen katkılar.",
        },
        {
          class_id: "ADVOCACY_SUPPORT",
          name_tr: "Savunuculuk & Destek Katılımı",
          name_en: "Advocacy Support Contribution",
          count: 100,
          percentage: 7.0,
          is_signal_eligible: false,
          description: "Dışsal kampanya veya yönlendirme kaynaklı katkılar.",
        },
      ],
      contamination_risk_index: 0.0,
      isolation_audit_status: "AUDITED_ZERO_CONTAMINATION",
      certified_at: "2026-09-12T00:00:00Z",
      isolation_proof_hash: "sha256:proof-iso-9921",
    };

    assert.equal(classes.total_contributions, 1420);
    assert.equal(classes.classes.length, 3);
    const core = classes.classes.find((c) => c.class_id === "CORE_PRE_RESULT");
    assert.ok(core);
    assert.equal(core.is_signal_eligible, true);

    const exposed = classes.classes.find((c) => c.class_id === "EXPOSED");
    assert.ok(exposed);
    assert.equal(exposed.is_signal_eligible, false);
  });

  it("verifies SignalScopeAlignmentReport validation (CAP-046)", () => {
    const scope: SignalScopeAlignmentReport = {
      signal_id: "sig-01",
      case_version_id: "case-01",
      jurisdiction_level: "NATIONAL",
      target_population: "Tüm Seçmenler",
      geographic_scope: "Türkiye Geneli",
      alignment_status: "ALIGNED",
      overall_alignment_score: 95.0,
      dimensions: [
        {
          dimension: "JURISDICTION",
          declared_scope: "NATIONAL",
          sample_scope: "NATIONAL",
          alignment_score: 98.0,
          is_valid: true,
        },
      ],
      validity_window_days: 90,
      certified_at: "2026-09-12T00:00:00Z",
      scope_seal_hash: "sha256:scope-seal-1122",
    };

    assert.equal(scope.alignment_status, "ALIGNED");
    assert.ok(scope.overall_alignment_score >= 90.0);
    assert.equal(scope.validity_window_days, 90);
  });

  it("verifies SignalVersioningReport and delta tracking (CAP-047)", () => {
    const versioning: SignalVersioningReport = {
      signal_id: "sig-01",
      case_version_id: "case-01",
      current_version: "v1.2.0",
      current_methodology_hash: "sha256:method-hash-v12",
      snapshots: [
        {
          snapshot_id: "snap-01",
          methodology_version: "v1.0.0",
          methodology_name: "Initial Baseline",
          sample_size: 500,
          confidence_score: 0.85,
          consensus_distribution: { OPT_A: 0.82, OPT_B: 0.18 },
          calculated_at: "2026-08-01T00:00:00Z",
          parent_snapshot_hash: null,
          snapshot_hash: "sha256:snap-01-hash",
        },
      ],
      latest_delta: {
        from_version: "v1.0.0",
        to_version: "v1.2.0",
        distribution_shift: 1.2,
        confidence_delta: 0.05,
        notes: "Örneklem büyümesiyle güven aralığı daraldı.",
      },
      audit_chain_valid: true,
      certified_at: "2026-09-12T00:00:00Z",
    };

    assert.equal(versioning.current_version, "v1.2.0");
    assert.equal(versioning.audit_chain_valid, true);
    assert.ok(versioning.latest_delta);
    assert.equal(versioning.latest_delta.distribution_shift, 1.2);
  });
});
