import assert from "node:assert/strict";
import test from "node:test";

import { AdminApiError } from "../src/lib/admin-api";
import {
  getSignalHealthReport,
  listSignalConsensusCards,
} from "../src/lib/signal-api";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("Signal reads enforce the Admin transport boundary and pagination limits", async () => {
  let capturedUrl = "";
  let capturedInit: RequestInit | undefined;

  await listSignalConsensusCards("https://api.example.test/gateway/", {
    limit: 1000.8,
    offset: -4,
    fetchImpl: async (input, init) => {
      capturedUrl = String(input);
      capturedInit = init;
      return jsonResponse([]);
    },
  });

  assert.equal(
    capturedUrl,
    "https://api.example.test/gateway/v1/signals/consensus-cards?limit=100&offset=0",
  );
  assert.equal(capturedInit?.method, "GET");
  assert.equal(capturedInit?.credentials, "include");
  assert.equal(capturedInit?.cache, "no-store");
  assert.equal(capturedInit?.redirect, "error");
  assert.equal(new Headers(capturedInit?.headers).get("Accept"), "application/json");
  assert.ok(capturedInit?.signal instanceof AbortSignal);
});

test("Signal identifiers are encoded and insecure origins fail before network access", async () => {
  let capturedUrl = "";
  const unsafeId = "signal/with spaces?scope=internal";
  await getSignalHealthReport(
    "https://api.example.test",
    unsafeId,
    async (input) => {
      capturedUrl = String(input);
      return jsonResponse({});
    },
  );
  assert.equal(
    capturedUrl,
    `https://api.example.test/v1/signals/${encodeURIComponent(unsafeId)}/health`,
  );

  let calls = 0;
  await assert.rejects(
    listSignalConsensusCards("http://api.example.test", {
      fetchImpl: async () => {
        calls += 1;
        return jsonResponse([]);
      },
    }),
    (error: unknown) =>
      error instanceof AdminApiError && error.code === "ADMIN_API_BASE_INSECURE",
  );
  assert.equal(calls, 0);
});

test("Signal API error details are compact and bounded", async () => {
  await assert.rejects(
    listSignalConsensusCards("https://api.example.test", {
      fetchImpl: async () => jsonResponse({ detail: `failure ${"x".repeat(800)}` }, 502),
    }),
    (error: unknown) => {
      assert.ok(error instanceof AdminApiError);
      assert.equal(error.status, 502);
      assert.ok(error.message.length <= 500);
      return true;
    },
  );
});
