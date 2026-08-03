# ADR-0091: Admin RSS/Atom subscription inventory and step-up activation

- Status: Accepted
- Date: 2026-08-03
- Slice: 55
- Extends: ADR-0090

## Context

Slice 54 introduced immutable RSS/Atom subscription manifests and an explicit activation service, but intentionally exposed no HTTP control surface. Operational staff need to inspect configured subscriptions and activate an approved manifest without gaining the ability to mutate the immutable manifest registry or bypass existing provider and scheduler controls.

## Decision

KEFE adds an internal Admin-only RSS/Atom subscription surface with exactly two operations:

1. list the immutable registered subscription manifests;
2. activate one manifest through the existing `RssAtomSubscriptionActivationService`.

No create, update, delete, import, bulk activation or dynamic registration endpoint is introduced.

Two explicit Admin capabilities are added:

- `SOURCE_SUBSCRIPTION_READ` permits deterministic inventory reads;
- `SOURCE_SUBSCRIPTION_ACTIVATE` permits activation.

The Reviewer and Access Admin roles receive read access. Only Access Admin receives activation access. Activation is included in the step-up capability set. HTTP activation also uses the existing write principal dependency, so same-session CSRF validation is mandatory before service invocation.

An activation request contains only:

- the expected exact manifest configuration hash;
- the requested first due timestamp.

The service resolves the immutable manifest, compares the expected configuration hash using constant-time comparison and fails with a bounded conflict before provider capability or schedule mutation if it does not match. It then delegates to the existing Slice 54 activation service. No alternate provider or scheduler path is allowed.

Inventory output is deterministic and bounded. It exposes the subscription code, adapter code, public locator, locale/jurisdiction, fixed interval, dispatch attempt limit, quota/circuit/permit/HTTP budgets and exact configuration hash. It does not expose terms evidence references, rate-limit evidence references, credentials, secret references, auth headers, raw evidence, storage references, backend object keys, private exception text or provider response bodies.

Activation output exposes only the manifest identity/configuration hash and bounded capability/schedule operational fields. It does not expose permit identifiers, evidence payloads, credentials or internal backend information.

Production continues to compose an empty manifest registry, so the inventory is empty and no provider or schedule is activated by startup.

## Consequences

- Subscription operations follow the existing Admin session, MFA, CSRF, capability and step-up controls.
- Stale Admin screens cannot activate a different manifest revision because the exact configuration hash is required.
- Manifest governance remains code/configuration controlled; an Admin user cannot alter provider policy through HTTP.
- A later slice may add audited manifest lifecycle management, but it requires a separate ADR and persistence model.

## Rejected alternatives

### Reuse `SOURCE_VERIFY` for activation

Rejected because verification is an editorial/source-assessment privilege, while activation creates an external operational schedule.

### Grant activation to Reviewer

Rejected because editorial review should not implicitly authorize external provider operations.

### Add manifest CRUD now

Rejected because dynamic mutation requires versioned persistence, audit, review and deployment semantics that are outside this slice.

### Omit the expected configuration hash

Rejected because a stale Admin client could activate configuration different from the one it reviewed.
