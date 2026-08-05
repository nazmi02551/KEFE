import assert from "node:assert/strict";
import test from "node:test";

import {
  operationalReasonText,
  operationalSignalText,
  sortedCountEntries,
  totalOperationalCount
} from "../src/lib/operational-reports";

test("operational reports helpers keep signals and reasons explainable", () => {
  assert.equal(operationalSignalText("ATTENTION"), "Dikkat");
  assert.match(
    operationalReasonText("MODERATION_BACKLOG"),
    /moderasyon/i
  );
  assert.equal(operationalReasonText("UNKNOWN_CODE"), "UNKNOWN_CODE");
});

test("aggregate entries are deterministic and totalled without inference", () => {
  const values = { REPORTED: 2, PENDING: 3 };
  assert.deepEqual(sortedCountEntries(values), [
    ["PENDING", 3],
    ["REPORTED", 2]
  ]);
  assert.equal(totalOperationalCount(values), 5);
});
