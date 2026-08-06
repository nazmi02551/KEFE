# ADR-0118 — Production and Preview Surface Reachability Inventory

- **Status:** Accepted
- **Date:** 2026-08-06
- **Foundation wave:** F4
- **Capabilities:** CAP-092, CAP-123
- **Exit criterion:** `PRODUCTION_AND_PREVIEW_SURFACE_REACHABILITY_INVENTORIED`

## Context

KEFE has several different kinds of software surface, but their current evidence is not equivalent:

- the canonical API and Admin Studio can be run locally;
- the consumer web directory is a product placeholder rather than a runtime;
- the mobile production entrypoint compiles against a reserved `.invalid` API hostname;
- the explicit phone preview is built as an installable debug APK in GitHub Actions;
- the MVP workflow creates a transient Android host, inserts a hostless `kefe:` custom scheme, compiles the production shell and deliberately does not upload that APK;
- the mobile app has in-app `/case/:caseId` routing, while committed Android/iOS external-entry declarations and association evidence do not exist;
- web deeplinks have not been configured;
- the OTP provider receipt route is implemented as an internal API boundary but has no deployed provider binding.

A CI build, local process, generated APK or internal route can be useful engineering evidence without proving that a production or preview surface is reachable by its intended audience. Treating these as equivalent would falsely satisfy the F4 reachability exit criterion.

## Decision

KEFE maintains a machine-readable surface reachability inventory at `docs/contracts/surface-reachability-inventory.v1.json`.

Every surface records:

1. a stable surface identity and type;
2. environment and intended audience;
3. one bounded status from the canonical status catalog;
4. whether it is externally reachable;
5. endpoint or artifact identity when one exists;
6. the evidence kind and repository sources supporting the classification;
7. the next proof required to advance the status.

The inventory distinguishes these states:

- `REACHABLE_VERIFIED`: intended audience reachability has current external evidence;
- `CI_ARTIFACT_AVAILABLE`: CI produced a downloadable artifact, without distribution or store claims;
- `LOCAL_ONLY`: runnable only through local engineering configuration;
- `COMPILE_ONLY`: builds successfully but has no usable deployed endpoint or distribution path;
- `PLACEHOLDER_ONLY`: the repository declares the product surface but no runtime exists;
- `INTERNAL_ONLY`: an application route exists but no external/provider reachability is proven;
- `NOT_CONFIGURED`: required routing, hosting or platform association does not exist;
- `VERIFICATION_PENDING`: a configured surface lacks current acceptable evidence.

`REACHABLE_VERIFIED` is permitted only with one of these evidence kinds:

- `EXTERNAL_HTTP_PROBE`;
- `STORE_DISTRIBUTION`;
- `HUMAN_OPERATOR_ATTESTATION`.

Static configuration, a local probe or a CI build can never independently create a production reachability claim. Endpoints containing `.invalid`, `localhost`, `127.0.0.1`, `0.0.0.0` or the Android emulator alias `10.0.2.2` are forbidden as evidence for production reachability.

The executable checker compares the inventory to the repository. It verifies the production mobile placeholder, local API/Admin defaults, consumer web placeholder, installable CI phone artifact boundary, hostless/non-uploaded transient share-scheme compile candidate, absence of committed native deeplink hosts, in-app Case route semantics, and the internal-only provider callback boundary.

## Consequences

- The F4 exit criterion gains an honest, reviewable inventory rather than an inferred deployment claim.
- Product and engineering can see exactly which proof is missing for each surface.
- The transient `kefe:` scheme compile candidate is tracked independently from both the installable phone preview and production deeplinks.
- A future deployment changes inventory state only together with external evidence and the relevant configuration.
- The inventory can be complete while every production surface remains unverified; inventory completeness and production readiness are separate facts.
- The consumer OpenAPI and runtime behavior remain unchanged.

## Explicit non-claims

This decision does not prove:

- a deployed production API origin;
- a deployed consumer web or Admin Studio origin;
- Android App Links, iOS Universal Links or web association files;
- that the transient hostless `kefe:` scheme exists in a committed, signed or distributed application;
- public preview distribution, Play Store/App Store acceptance or a signed release artifact;
- production reachability of the internal OTP provider callback;
- real provider delivery, callback availability or network authenticity beyond the implemented HMAC boundary;
- availability, latency, deployed SLO compliance, alerting, incident response or recovery;
- operator usability, access approval or rollback execution.

A GitHub Actions APK artifact is not a public release. A compiled production shell is not a reachable mobile product. A local URL is not a production endpoint.
