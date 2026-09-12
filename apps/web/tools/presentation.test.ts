import assert from "node:assert/strict";
import { test } from "node:test";

import { clampPercentage } from "../src/lib/presentation";

test("percentage values inside the display range remain unchanged", () => {
  assert.equal(clampPercentage(0), 0);
  assert.equal(clampPercentage(42.5), 42.5);
  assert.equal(clampPercentage(100), 100);
});

test("percentage values are bounded to the zero-to-one-hundred display range", () => {
  assert.equal(clampPercentage(-0.01), 0);
  assert.equal(clampPercentage(100.01), 100);
});

test("non-finite percentage values fail closed to zero", () => {
  assert.equal(clampPercentage(Number.NaN), 0);
  assert.equal(clampPercentage(Number.POSITIVE_INFINITY), 0);
  assert.equal(clampPercentage(Number.NEGATIVE_INFINITY), 0);
});
