import assert from "node:assert/strict";
import test from "node:test";

import {
  CaseMediaApiClient,
  CaseMediaApiError
} from "../src/lib/case-media-api";
import type {
  MediaAsset,
  MediaAssetWriteResponse,
  MediaAuditTrail,
  MediaBindingWriteResponse,
  MediaInventory,
  RegisterMediaRequest
} from "../src/lib/case-media";

const MEDIA_ID = "11111111-1111-1111-1111-111111111111";
const CASE_VERSION_ID = "22222222-2222-2222-2222-222222222222";

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

const asset = {
  media_asset_id: MEDIA_ID,
  asset_key: "case-hero-one",
  kind: "IMAGE",
  delivery_ref: "media-ref:catalog/case-hero-one/v1",
  content_hash: "a".repeat(64),
  byte_length: 2048,
  media_type: "image/webp",
  title: "Case hero",
  alt_text: "Abstract balance scale.",
  caption: null,
  credit_label: "KEFE Editorial",
  source_label: "Internal licensed media catalog",
  poster_asset_key: null,
  state: "REGISTERED",
  registered_by: "admin:subject",
  registered_at: "2026-08-05T09:00:00Z"
} satisfies MediaAsset;
const inventory: MediaInventory = { items: [asset] };
const writeResponse: MediaAssetWriteResponse = { asset, replayed: false };
const audit: MediaAuditTrail = { items: [] };
const binding = {
  binding: {
    binding_id: "33333333-3333-3333-3333-333333333333",
    case_version_id: CASE_VERSION_ID,
    media_asset_id: MEDIA_ID,
    slot: "HERO",
    priority: 100,
    autoplay: false,
    muted: false,
    looping: false,
    bound_by: "admin:subject",
    bound_at: "2026-08-05T09:00:00Z"
  },
  replayed: false
} satisfies MediaBindingWriteResponse;

const registration: RegisterMediaRequest = {
  asset_key: asset.asset_key,
  kind: asset.kind,
  delivery_ref: asset.delivery_ref,
  content_hash: asset.content_hash,
  byte_length: asset.byte_length,
  media_type: asset.media_type,
  title: asset.title,
  alt_text: asset.alt_text,
  caption: null,
  credit_label: asset.credit_label,
  source_label: asset.source_label,
  poster_asset_key: null
};

test("client construction starts no request and reads omit csrf", async () => {
  const calls: Array<{ method: string; path: string; search: string; csrf: string | null }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      search: url.search,
      csrf: headers.get("X-KEFE-CSRF")
    });
    if (url.pathname.endsWith("/audit")) return jsonResponse(audit);
    if (url.pathname.endsWith(MEDIA_ID)) return jsonResponse(asset);
    return jsonResponse(inventory);
  };
  const client = new CaseMediaApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl
  });

  assert.equal(calls.length, 0);
  await client.inventory("READY");
  await client.detail(MEDIA_ID);
  await client.audit(MEDIA_ID);

  assert.deepEqual(calls, [
    {
      method: "GET",
      path: "/internal/admin/v1/case-media",
      search: "?state=READY",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/case-media/${MEDIA_ID}`,
      search: "",
      csrf: null
    },
    {
      method: "GET",
      path: `/internal/admin/v1/case-media/${MEDIA_ID}/audit`,
      search: "",
      csrf: null
    }
  ]);
});

test("writes fail closed before network without csrf", async () => {
  let networkCalls = 0;
  const client = new CaseMediaApiClient({
    baseUrl: "https://api.example.test",
    fetchImpl: async () => {
      networkCalls += 1;
      return jsonResponse(writeResponse);
    }
  });

  await assert.rejects(
    client.register(registration),
    (error: unknown) =>
      error instanceof CaseMediaApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  await assert.rejects(
    client.markReady(MEDIA_ID),
    (error: unknown) =>
      error instanceof CaseMediaApiError && error.code === "ADMIN_CSRF_REQUIRED"
  );
  assert.equal(networkCalls, 0);
});

test("explicit writes carry same-session csrf and exact bodies", async () => {
  const calls: Array<{
    method: string;
    path: string;
    csrf: string | null;
    body: string | null;
  }> = [];
  const fetchImpl: typeof fetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const headers = new Headers(init.headers);
    calls.push({
      method: String(init.method),
      path: url.pathname,
      csrf: headers.get("X-KEFE-CSRF"),
      body: typeof init.body === "string" ? init.body : null
    });
    if (url.pathname.endsWith("/bindings")) return jsonResponse(binding);
    return jsonResponse(writeResponse);
  };
  const client = new CaseMediaApiClient({
    baseUrl: "https://api.example.test",
    csrfToken: "same-session-token",
    fetchImpl
  });
  const bindingBody = {
    case_version_id: CASE_VERSION_ID,
    slot: "HERO" as const,
    priority: 100,
    autoplay: false as const,
    muted: false,
    looping: false
  };

  await client.register(registration);
  await client.markReady(MEDIA_ID);
  await client.bind(MEDIA_ID, bindingBody);
  await client.retire(MEDIA_ID);

  assert.deepEqual(calls, [
    {
      method: "POST",
      path: "/internal/admin/v1/case-media",
      csrf: "same-session-token",
      body: JSON.stringify(registration)
    },
    {
      method: "POST",
      path: `/internal/admin/v1/case-media/${MEDIA_ID}/ready`,
      csrf: "same-session-token",
      body: null
    },
    {
      method: "POST",
      path: `/internal/admin/v1/case-media/${MEDIA_ID}/bindings`,
      csrf: "same-session-token",
      body: JSON.stringify(bindingBody)
    },
    {
      method: "POST",
      path: `/internal/admin/v1/case-media/${MEDIA_ID}/retire`,
      csrf: "same-session-token",
      body: null
    }
  ]);
});

test("insecure remote API base fails before network", () => {
  assert.throws(
    () => new CaseMediaApiClient({ baseUrl: "http://api.example.test" }),
    (error: unknown) =>
      error instanceof CaseMediaApiError && error.code === "ADMIN_API_BASE_INSECURE"
  );
});
