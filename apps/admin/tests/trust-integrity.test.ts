import test from "node:test";
import assert from "node:assert/strict";
import { TrustIntegrityApiClient } from "../src/lib/trust-integrity-api";

test("inspects cluster and classifies as ISOLATED_QUARANTINE_SWARM when score >= 0.8 and entropy < 0.25", async () => {
  const client = new TrustIntegrityApiClient();
  const res = await client.inspectCluster({
    cluster_id: "swarm_test_99",
    target_case_id: "case_test_01",
    synthetic_probability_score: 0.92,
    quarantined_bot_payloads_count: 800,
    semantic_entropy_index: 0.14,
  });

  assert.equal(res.defense_state, "ISOLATED_QUARANTINE_SWARM");
  assert.equal(res.is_quarantined, true);
  assert.equal(res.quarantined_bot_payloads_count, 800);

  const clusters = await client.listClusters();
  const found = clusters.find((c) => c.cluster_id === "swarm_test_99");
  assert.ok(found);
  assert.equal(found?.quarantine_status, "ACTIVE");
});

test("inspects cluster and classifies as SUSPECTED_BOT_COORDINATION", async () => {
  const client = new TrustIntegrityApiClient();
  const res = await client.inspectCluster({
    cluster_id: "susp_test_88",
    target_case_id: "case_test_02",
    synthetic_probability_score: 0.55,
    quarantined_bot_payloads_count: 50,
    semantic_entropy_index: 0.40,
  });

  assert.equal(res.defense_state, "SUSPECTED_BOT_COORDINATION");
  assert.equal(res.is_quarantined, false);
});

test("evaluates agenda thresholding into NATIONAL_URGENCY_SPIKE", async () => {
  const client = new TrustIntegrityApiClient();
  const res = await client.evaluateAgenda({
    topic_id: "topic_national_debate",
    topic_title: "National Clean Energy Mandate",
    resonance_velocity_index: 0.85,
    viewpoint_diversity_entropy: 0.80,
  });

  assert.equal(res.priority_tier, "NATIONAL_URGENCY_SPIKE");
  assert.equal(res.is_featured_on_national_ballot, true);
});

test("updates cluster quarantine status", async () => {
  const client = new TrustIntegrityApiClient();
  const updated = await client.updateClusterStatus("bot_cls_001", "RESOLVED");
  assert.equal(updated.quarantine_status, "RESOLVED");
});
