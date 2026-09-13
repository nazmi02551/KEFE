import test from "node:test";
import assert from "node:assert/strict";
import { RadarLiveApiClient } from "../src/lib/radar-live-api";

test("RadarLiveApiClient publishes and retrieves context drift notices (CAP-076)", async () => {
  const client = new RadarLiveApiClient();
  const caseId = "00000000-0000-0000-0000-000000000001";

  const notice = await client.publishDriftNotice(caseId, {
    drift_type: "LEGAL_REFORM",
    summary: "İlgili yasa maddesi TBMM genel kurulunda değiştirilmiştir.",
    recommended_action: "CONTINUE_WITH_AWARENESS",
    source_reference_url: "https://resmigazete.gov.tr/2026/09/12",
  });

  assert.equal(notice.case_version_id, caseId);
  assert.equal(notice.drift_type, "LEGAL_REFORM");
  assert.equal(notice.recommended_action, "CONTINUE_WITH_AWARENESS");

  const notices = await client.getDriftNotices(caseId);
  assert.ok(notices.length >= 1);
  assert.equal(notices[0].drift_type, "LEGAL_REFORM");
});

test("RadarLiveApiClient retrieves live deliberation radar pulse", async () => {
  const client = new RadarLiveApiClient();
  const res = await client.getLiveRadar("00000000-0000-0000-0000-000000000001");

  assert.ok(res.deliberation_velocity_index > 0);
  assert.ok(res.live_participant_count > 0);
  assert.ok(res.shift_vectors.length >= 3);
  assert.ok(res.primary_consensus_momentum);
});
