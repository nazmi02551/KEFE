import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import {
  KefApiError,
  getCaseVersionHistory,
  getPublicCase,
  getPublicShare,
  getSignalHealth,
  getSignalQualification,
  listActionMilestones,
  listCaseSignalCards,
  listInstitutionResponses,
  listPublicCases,
  listSignalConsensusCards,
  normalizeApiBase,
} from "../src/lib/kefe-api";

const originalFetch = globalThis.fetch;
const originalApiBase = process.env.KEFE_API_BASE_URL;

interface CapturedRequest {
  url: string;
  init?: RequestInit;
}

function installFetch(responses: Response[]): CapturedRequest[] {
  const requests: CapturedRequest[] = [];
  globalThis.fetch = (async (input: string | URL | Request, init?: RequestInit) => {
    requests.push({ url: String(input), init });
    const response = responses.shift();
    assert(response, "Unexpected extra fetch call");
    return response;
  }) as typeof fetch;
  return requests;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalApiBase === undefined) {
    delete process.env.KEFE_API_BASE_URL;
  } else {
    process.env.KEFE_API_BASE_URL = originalApiBase;
  }
});

test("list endpoints use the server base, bounded query parameters and GET semantics", async () => {
  process.env.KEFE_API_BASE_URL = "https://api.example.test/gateway/";
  const requests = installFetch([
    jsonResponse([]),
    jsonResponse([]),
    jsonResponse([]),
  ]);

  await listSignalConsensusCards(25, 5);
  await listPublicCases(30, 10);
  await listInstitutionResponses();

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      "https://api.example.test/gateway/v1/signals/consensus-cards?limit=25&offset=5",
      "https://api.example.test/gateway/v1/cases?limit=30&offset=10",
      "https://api.example.test/gateway/v1/impact/institution-responses",
    ],
  );
  for (const request of requests) {
    assert.equal(request.init?.method, undefined, "Public readers must use HTTP GET");
    assert.equal(request.init?.cache, "no-store");
    assert.equal((request.init?.headers as Record<string, string>).Accept, "application/json");
  }
});

test("list pagination is bounded to each public endpoint contract", async () => {
  process.env.KEFE_API_BASE_URL = "https://api.example.test";
  const requests = installFetch([jsonResponse([]), jsonResponse([])]);

  await listSignalConsensusCards(1000.9, -8);
  await listPublicCases(100, Number.POSITIVE_INFINITY);

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      "https://api.example.test/v1/signals/consensus-cards?limit=100&offset=0",
      "https://api.example.test/v1/cases?limit=50&offset=0",
    ],
  );
});

test("API base validation normalizes paths and permits explicit server HTTP", () => {
  assert.equal(
    normalizeApiBase("https://api.example.test/gateway///", { allowInsecureHttp: false }),
    "https://api.example.test/gateway",
  );
  assert.equal(
    normalizeApiBase("http://api.internal:8000/", { allowInsecureHttp: true }),
    "http://api.internal:8000",
  );
  assert.equal(
    normalizeApiBase("http://localhost:8000/", { allowInsecureHttp: false }),
    "http://localhost:8000",
  );
});

test("browser-visible API bases reject unsafe or ambiguous URLs", () => {
  for (const rawBase of [
    "not a URL",
    "ftp://api.example.test",
    "http://api.example.test",
    "https://user:secret@api.example.test",
    "https://api.example.test?tenant=internal",
    "https://api.example.test#fragment",
  ]) {
    assert.throws(
      () => normalizeApiBase(rawBase, { allowInsecureHttp: false }),
      TypeError,
      rawBase,
    );
  }
});

test("dynamic path and query identifiers are URL encoded", async () => {
  process.env.KEFE_API_BASE_URL = "http://localhost:9999";
  const requests = installFetch([
    jsonResponse({}),
    jsonResponse({}),
    jsonResponse({}),
    jsonResponse([]),
    jsonResponse([]),
    jsonResponse([]),
  ]);
  const unsafeId = "id/with spaces?and=query";

  await getPublicCase(unsafeId);
  await getPublicShare(unsafeId);
  await getSignalHealth(unsafeId);
  await listCaseSignalCards(unsafeId);
  await listInstitutionResponses(unsafeId);
  await listActionMilestones(unsafeId);

  const encoded = encodeURIComponent(unsafeId);
  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      `http://localhost:9999/v1/cases/${encoded}`,
      `http://localhost:9999/v1/shares/${encoded}`,
      `http://localhost:9999/v1/signals/${encoded}/health`,
      `http://localhost:9999/v1/signals/consensus-cards?case_version_id=${encoded}&limit=10`,
      `http://localhost:9999/v1/impact/institution-responses?case_version_id=${encoded}`,
      `http://localhost:9999/v1/impact/actions?case_version_id=${encoded}`,
    ],
  );
});

test("optional resources translate only 404 responses to their documented empty value", async () => {
  const requests = installFetch([
    jsonResponse({ error: { code: "NOT_FOUND", message: "missing" } }, 404),
    jsonResponse({ error: { code: "NOT_FOUND", message: "missing" } }, 404),
    jsonResponse({ error: { code: "NOT_FOUND", message: "missing" } }, 404),
    jsonResponse({ error: { code: "NOT_FOUND", message: "missing" } }, 404),
  ]);

  assert.equal(await getSignalHealth("missing"), null);
  assert.equal(await getSignalQualification("missing"), null);
  assert.equal(await getCaseVersionHistory("missing"), null);
  assert.deepEqual(await listCaseSignalCards("missing"), []);
  assert.equal(requests.length, 4);
});

test("structured API failures retain their code, message and HTTP status", async () => {
  installFetch([
    jsonResponse({ error: { code: "RATE_LIMITED", message: "Try later" } }, 429),
  ]);

  await assert.rejects(
    () => listActionMilestones(),
    (error: unknown) => {
      assert(error instanceof KefApiError);
      assert.equal(error.code, "RATE_LIMITED");
      assert.equal(error.message, "Try later");
      assert.equal(error.status, 429);
      return true;
    },
  );
});

test("malformed error bodies fall back to a stable generic error", async () => {
  installFetch([new Response("not-json", { status: 502 })]);

  await assert.rejects(
    () => listInstitutionResponses(),
    (error: unknown) => {
      assert(error instanceof KefApiError);
      assert.equal(error.code, "API_ERROR");
      assert.equal(error.message, "HTTP 502");
      assert.equal(error.status, 502);
      return true;
    },
  );
});
