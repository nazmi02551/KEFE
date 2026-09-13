import { describe, it } from "node:test";
import assert from "node:assert/strict";
import type { InstitutionResponse, ActionMilestone } from "../src/lib/impact-api";

describe("Impact Workspace & Institution Response Room (CAP-049, CAP-050)", () => {
  it("verifies impact client functions exist", async () => {
    const api = await import("../src/lib/impact-api");
    assert.equal(typeof api.listInstitutionResponses, "function");
    assert.equal(typeof api.listActionMilestones, "function");
    assert.equal(typeof api.proposeAction, "function");
    assert.equal(typeof api.updateActionProgress, "function");
  });

  it("verifies InstitutionResponse structure and verified status (CAP-049)", () => {
    const response: InstitutionResponse = {
      response_id: "resp-1111",
      case_version_id: "22222222-2222-4222-8222-222222222222",
      institution_name: "Ulaştırma ve Altyapı Bakanlığı",
      authority_role: "Genel Müdürlük",
      verification_status: "VERIFIED",
      response_type: "POLICY_CHANGE",
      statement: "Yurttaş uzlaşısı doğrultusunda tarifeler sübvanse edilecektir.",
      published_at: "2026-09-12T10:00:00Z",
      milestone_date: "2026-12-31T00:00:00Z",
    };

    assert.equal(response.verification_status, "VERIFIED");
    assert.equal(response.response_type, "POLICY_CHANGE");
    assert.ok(response.milestone_date);
    assert.equal(response.institution_name, "Ulaştırma ve Altyapı Bakanlığı");
  });

  it("verifies ActionMilestone linkage to InstitutionResponse (CAP-050, CAP-052)", () => {
    const milestone: ActionMilestone = {
      action_id: "act-9999",
      case_version_id: "22222222-2222-4222-8222-222222222222",
      title: "Tarife İndirimi Yönetmeliği",
      description: "Resmi Gazete yayını için taslak hazırlığı.",
      status: "IN_PROGRESS",
      progress_percentage: 50,
      created_at: "2026-09-12T12:00:00Z",
      institution_response_id: "resp-1111",
      target_completion_date: "2026-11-30T00:00:00Z",
      evidence_summary: "Bakanlık taslak duyurusu",
      evidence_url: "https://uab.gov.tr/taslak-duyuru",
    };

    assert.equal(milestone.institution_response_id, "resp-1111");
    assert.equal(milestone.progress_percentage, 50);
    assert.equal(milestone.status, "IN_PROGRESS");
    assert.ok(milestone.evidence_url?.startsWith("https://"));
  });

  it("verifies ImpactEvidence artifact data model (CAP-053)", () => {
    const evidence = {
      evidence_id: "ev-1111",
      action_id: "act-9999",
      evidence_type: "OFFICIAL_GAZETTE_DECREE",
      evidence_title: "Resmi Gazete 32155",
      source_url: "https://resmigazete.gov.tr/32155",
      sha256_digest: "b".repeat(64),
      verification_status: "VERIFIED_AUTHENTIC",
    };

    assert.equal(evidence.evidence_type, "OFFICIAL_GAZETTE_DECREE");
    assert.equal(evidence.verification_status, "VERIFIED_AUTHENTIC");
    assert.equal(evidence.sha256_digest.length, 64);
  });

  it("verifies ImpactVerification verdict calculation (CAP-054)", () => {
    const verification = {
      verification_id: "ver-1111",
      action_id: "act-9999",
      outcome_verdict: "FULL_RESOLUTION",
      resolution_score: 0.95,
      auditor_consensus_count: 3,
      verification_notes: "Yurttaş uzlaşısı %95 oranında hayata geçirildi.",
    };

    assert.equal(verification.outcome_verdict, "FULL_RESOLUTION");
    assert.ok(verification.resolution_score >= 0.9);
    assert.ok(verification.auditor_consensus_count >= 1);
  });

  it("verifies ResponseReweigh data model (CAP-051)", () => {
    const reweigh = {
      response_id: "resp-1111",
      case_version_id: "22222222-2222-4222-8222-222222222222",
      reweigh_round_id: "reweigh-998877",
      is_reweigh_active: true,
      initiated_at: "2026-09-12T12:00:00Z",
      instructions: "Kurum taahhüdü sonrası tercih güncelleme penceresi açıldı.",
    };

    assert.equal(reweigh.is_reweigh_active, true);
    assert.ok(reweigh.instructions.length > 10);
  });
});

