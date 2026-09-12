import test from "node:test";
import assert from "node:assert/strict";
import { AnalyticsMetricsApiClient } from "../src/lib/analytics-metrics-api";

test("AnalyticsMetricsApiClient retrieves North Star WAU metric (CAP-114)", async () => {
  const client = new AnalyticsMetricsApiClient();
  const res = await client.getNorthStar(7);

  assert.ok(res.meaningful_weigh_count > 0);
  assert.ok(res.weekly_active_weighers > 0);
  assert.ok(res.distinct_cases_weighed > 0);
  assert.ok(res.window_start);
  assert.ok(res.window_end);
});

test("AnalyticsMetricsApiClient retrieves activation funnel stages (CAP-115)", async () => {
  const client = new AnalyticsMetricsApiClient();
  const res = await client.getActivationFunnel(14);

  assert.equal(res.total_sessions, 5000);
  assert.equal(res.stages.length, 5);
  assert.equal(res.stages[0].stage_name, "WEIGH_STARTED");
  assert.equal(res.stages[1].stage_name, "DECISION_COMMITTED");
  assert.equal(res.stages[2].stage_name, "RESULT_REVEALED");
  assert.equal(res.stages[3].stage_name, "PERSPECTIVE_VIEWED");
  assert.equal(res.stages[4].stage_name, "DECISION_REVISED");
});

test("AnalyticsMetricsApiClient retrieves quality resilience metrics (CAP-116)", async () => {
  const client = new AnalyticsMetricsApiClient();
  const res = await client.getQualityMetrics(7);

  assert.ok(res.total_exposed_sessions > 0);
  assert.ok(res.resilience_index > 0);
  assert.ok(res.attitude_shift_rate > 0);
  assert.equal(
    res.stable_decisions_count + res.shifted_decisions_count,
    res.total_exposed_sessions
  );
});

test("AnalyticsMetricsApiClient evaluates depolarization into HIGH_DEPOLARIZATION (CAP-117)", async () => {
  const client = new AnalyticsMetricsApiClient();
  const res = await client.evaluateDepolarization({
    case_version_id: "00000000-0000-0000-0000-000000000001",
    pre_deliberation_distance: 0.80,
    post_deliberation_distance: 0.30,
  });

  assert.equal(res.bridge_efficacy_state, "HIGH_DEPOLARIZATION");
  assert.ok(res.depolarization_score >= 0.5);
});

test("AnalyticsMetricsApiClient evaluates depolarization into PERSISTENT_POLARIZATION", async () => {
  const client = new AnalyticsMetricsApiClient();
  const res = await client.evaluateDepolarization({
    case_version_id: "00000000-0000-0000-0000-000000000001",
    pre_deliberation_distance: 0.85,
    post_deliberation_distance: 0.80,
  });

  assert.equal(res.bridge_efficacy_state, "PERSISTENT_POLARIZATION");
  assert.ok(res.depolarization_score < 0.20);
});
