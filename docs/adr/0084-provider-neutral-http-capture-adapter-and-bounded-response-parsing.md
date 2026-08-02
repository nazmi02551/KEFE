# ADR-0084 — Provider-neutral HTTP capture adapter and bounded response parsing

- Status: Accepted
- Date: 2026-08-02
- Issue: #221
- Parent: ADR-0080, ADR-0081, ADR-0082, ADR-0083

## Context

KEFE now has provider admission permits, callback-scoped secret resolution, controlled HTTPS transport, exact-IP TLS runtime and origin-bound ephemeral HTTP authentication. The remaining bridge to a real source provider is the capture adapter.

The existing credential-aware adapter port receives `SecretAccess`. Allowing every provider-specific adapter to read that secret, construct auth headers, perform network calls or implement retries would recreate the security and observability risks that the previous slices removed.

KEFE therefore needs one generic HTTP capture wrapper. Provider-specific code must be limited to two deterministic responsibilities: build one public request plan and parse one bounded HTTP response into `CapturedSource`.

## Decision

1. A provider-specific `ProviderHttpCaptureDefinition` exposes only:
   - `build_plan(external_locator, trace_id, at)`; and
   - `parse_response(plan, response, trace_id, at)`.
2. Definition ports do not expose `SecretAccess`, `SecretLease`, sensitive-header access, DNS, pinned backends, sockets, TLS contexts or retry controls.
3. `ProviderHttpCapturePlan` is immutable and redacted. It contains exactly one `OutboundHttpRequest`, and its versioned `adapter_code` must match both the definition and request.
4. `ProviderHttpCaptureAdapter` is the generic credential-aware wrapper. It alone receives `SecretAccess` and passes it directly to `SecureProviderHttpExecutor`; it never reads secret bytes itself.
5. Planning completes and is validated before any secret callback or HTTP execution begins.
6. The authenticated executor remains solely responsible for secret use, credential decoration, exact-origin binding and transport execution. DNS, public-IP validation, TLS, response byte limits and redirects remain in their existing layers.
7. The parser receives only the validated redacted plan and bounded `ProviderHttpResponse`. It does not receive credentials or raw transport internals.
8. Provider HTTP retryable/final errors retain their classification when mapped to source-capture errors. Raw exception text is never included.
9. Malformed plans, adapter-code drift, unexpected planning failures, malformed parser results and unexpected parser failures map to bounded final source-capture codes.
10. No autonomous retry occurs in this adapter. Retry decisions remain above capture execution.
11. A generic factory may construct wrappers for future provider definitions. Production composition registers zero provider definitions and zero credential-aware HTTP adapters in this slice.

## Error boundary

The adapter may emit only bounded operational codes:

- `SOURCE_PROVIDER_HTTP_PLAN_INVALID`
- `SOURCE_PROVIDER_HTTP_ADAPTER_MISMATCH`
- `SOURCE_PROVIDER_HTTP_EXECUTION_INVALID`
- `SOURCE_PROVIDER_HTTP_RESPONSE_INVALID`
- or `SOURCE_` followed by a validated existing `PROVIDER_HTTP_*` code while preserving retryable/final classification.

No exception message, URL, request target, response body, secret reference or credential value may be included in these errors.

## Consequences

A later provider-adoption slice can add an exact provider definition without gaining direct access to secrets or network primitives. The definition remains testable with bounded request/response values. This slice does not prove any real provider integration, parser correctness for a real format, live network access, raw-body persistence or production operations evidence.
