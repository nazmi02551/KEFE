# F4 Provider-Neutral OTP HTTP Delivery — 2026-08-05

## Scope

- Foundation wave: F4 — Consumer identity, privacy, reachability and production readiness
- Capability: CAP-084 — Guest-to-account conversion and data merge
- Issue: #320
- Parent runtime: PR #319 / `991b877103b5cf8ac439026a38c51a29d56d34ac`
- Branch: `feature/f4-otp-http-delivery`

## Bounded advancement

This slice replaces the permanently disabled production OTP composition with an explicit provider-neutral HTTP delivery boundary while preserving all existing public identity APIs.

Implemented boundary:

- explicit `CAPTURE`, `DISABLED` and `HTTP` runtime modes;
- production startup requires `HTTP` mode and rejects capture/disabled adapters;
- production HTTP mode requires an HTTPS endpoint and secret-managed bearer credential;
- persisted `OtpChallenge.id` is used as both payload delivery id and `Idempotency-Key`;
- challenge channel, normalized recipient, code and expiry are sent in deterministic JSON;
- bounded timeout, response bytes and attempt count;
- redirects, userinfo, query, fragment, IP literals, localhost, `.local`, single-label hosts, root-only paths and non-443 endpoints are rejected;
- network failures and bounded retryable statuses reuse the exact request object;
- exhausted retryable outcomes return `AUTH_OTP_DELIVERY_UNAVAILABLE`;
- final provider rejection returns `AUTH_OTP_DELIVERY_REJECTED` without response-body exposure;
- endpoint, credential, recipient, OTP code and delivery identity are excluded from representations and operational results;
- no new database table, plaintext OTP persistence, provider response persistence or public OpenAPI field.

## Contract evidence

- ADR-0112: `docs/adr/0112-provider-neutral-production-otp-delivery.md`
- Contract: `docs/contracts/otp-http-delivery.v1.json`
- Executable checker: `services/api/tools/check_otp_http_delivery_contract.py`
- Adapter/runtime proof: `services/api/tests/test_otp_http_delivery.py`
- Dedicated workflow: `.github/workflows/otp-http-delivery.yml`

## Evidence required before review-ready

The same exact head must pass:

- OTP HTTP Delivery CI, memory and PostgreSQL jobs;
- Guest Merge Key Rotation CI;
- Guest Merge Replay CI;
- API CI;
- MVP Beta Gates;
- Global Readiness;
- all other workflows triggered by the exact head.

## Explicit non-claims and remaining F4 gates

Repository evidence from this slice does not prove:

- real email or SMS provider deliverability;
- production provider account, sender identity, template or regional compliance;
- production credential deployment or rotation;
- deployed DNS egress and firewall policy;
- deployed delivery metrics, alerting, SLO or incident response;
- operator-validated rollback or provider switch;
- Apple/Google store identity-flow acceptance.

CAP-084 and F4 remain partial until the relevant external deployment and operational evidence exists.