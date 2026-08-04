import assert from "node:assert/strict";
import test from "node:test";

import { projectionIdempotencyKey } from "../src/lib/idempotency";

const CANDIDATE = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const REVIEW = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb";

test("projection key is stable for the exact selected lineage", () => {
  const first = projectionIdempotencyKey(CANDIDATE, REVIEW);
  const retry = projectionIdempotencyKey(CANDIDATE, REVIEW);

  assert.equal(first, retry);
  assert.equal(
    first,
    `admin-studio:projection:v1:${CANDIDATE}:${REVIEW}`
  );
  assert.ok(first.length <= 200);
});

test("projection key changes only when lineage changes", () => {
  const original = projectionIdempotencyKey(CANDIDATE, REVIEW);
  const changed = projectionIdempotencyKey(
    "cccccccc-cccc-cccc-cccc-cccccccccccc",
    REVIEW
  );

  assert.notEqual(original, changed);
});

test("invalid lineage fails closed", () => {
  assert.throws(() => projectionIdempotencyKey("", REVIEW));
  assert.throws(() => projectionIdempotencyKey(CANDIDATE, "not-a-review"));
});
