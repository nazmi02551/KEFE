import test from "node:test";
import assert from "node:assert/strict";
import { FinOpsApiClient } from "../src/lib/finops-api";

test("FinOpsApiClient retrieves unit economics summary (CAP-124)", async () => {
  const client = new FinOpsApiClient();
  const res = await client.getSummary();

  assert.ok(res.cost_per_weigh_usd > 0);
  assert.ok(res.total_monthly_spend_usd > 0);
  assert.ok(res.total_tokens_consumed > 0);
  assert.ok(res.p95_latency_ms > 0);
});

test("FinOpsApiClient retrieves provider spend breakdown", async () => {
  const client = new FinOpsApiClient();
  const res = await client.getBreakdown();

  assert.ok(res.items.length >= 4);
  assert.equal(res.currency, "USD");
  assert.ok(res.total_spend_usd > 0);
  const categories = res.items.map((i) => i.category);
  assert.ok(categories.includes("LLM_INFERENCE"));
  assert.ok(categories.includes("SMS_OTP"));
});

test("FinOpsApiClient simulates unit economics at scale", async () => {
  const client = new FinOpsApiClient();
  const res = await client.simulateScale(100000, 4);

  assert.equal(res.projected_monthly_wau, 100000);
  assert.equal(res.total_projected_weighs, 400000);
  assert.ok(res.projected_monthly_cost_usd > 0);
  assert.ok(res.projected_cost_per_weigh_usd < 0.05);
  assert.ok(res.breakdown_projection["LLM_INFERENCE"] > 0);
});
