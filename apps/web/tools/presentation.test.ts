import assert from "node:assert/strict";
import { test } from "node:test";

import {
  clampPercentage,
  publicLoadErrorMessage,
  ratioToPercentage,
  safeCount,
} from "../src/lib/presentation";

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

test("normalized ratios convert to bounded display percentages", () => {
  assert.equal(ratioToPercentage(0.425), 42.5);
  assert.equal(ratioToPercentage(-0.1), 0);
  assert.equal(ratioToPercentage(1.1), 100);
  assert.equal(ratioToPercentage(Number.NaN), 0);
});

test("external counts are finite non-negative integers", () => {
  assert.equal(safeCount(1420.9), 1420);
  assert.equal(safeCount(-1), 0);
  assert.equal(safeCount(Number.POSITIVE_INFINITY), 0);
});

test("public load errors never reflect upstream error details", () => {
  const upstream = new Error("postgresql://admin:secret@internal-db/kefe");

  assert.equal(
    publicLoadErrorMessage(upstream, "İçerik şu anda yüklenemiyor."),
    "İçerik şu anda yüklenemiyor.",
  );
});

test("public load errors provide safe guidance for rate limiting", () => {
  const upstream = {
    status: 429,
    message: "internal quota key customer-123",
  };

  assert.equal(
    publicLoadErrorMessage(upstream, "İçerik şu anda yüklenemiyor."),
    "Çok fazla istek gönderildi. Lütfen kısa süre sonra yeniden deneyin.",
  );
});
