# KEFE Capability Portfolio — WORKING Mirror

This directory contains the GitHub delivery mirror of the Product Bible Roadmap Capability Register.

## Authority

- Published documentation authority remains **KEFE Documentation Ecosystem v3.4 CURRENT** until explicit promotion.
- The complete reconciled v3.5 package is a **WORKING** candidate in Drive.
- `capability-portfolio.v1.tsv` does not create or promote product decisions. It preserves the lifecycle status already assigned by the owning documents and explicit decisions.

## Coverage

The mirror tracks **128 capabilities** across:

- ME and decision/revision/reflection;
- generic Case composition;
- WE, Signal and Impact;
- content ingestion, authoring and Admin operations;
- trust, privacy and integrity;
- consumer growth and AI-assisted experiences;
- commercial products and entitlement/billing architecture;
- analytics, statistical methodology, reporting and FinOps;
- governance and long-term validation candidates.

Every record includes a stable `CAP-*` ID, lifecycle status, phase, priority, owner-document IDs, dependencies, current evidence, source class and next gate.

## No-forgotten-feature rule

Before selecting a material implementation slice:

1. Read this register and audit unresolved P0/P1 entries against the live repository.
2. Reference one or more `CAP-*` IDs in the issue and PR, or explicitly declare `maintenance-only` scope.
3. Do not silently change Proposal/Test/Roadmap entries into Accepted work.
4. Update evidence and next gate when a capability advances.
5. Use `IMPLEMENTED_VERIFIED` only with exact contract-appropriate evidence.
6. Keep external/human gates distinct from CI.
7. Reconcile this mirror with the Product Bible at every documentation milestone with zero unexplained drift.

## Validation

Run:

```bash
python scripts/validate_capability_portfolio.py
```

CI also runs the validator whenever the portfolio, continuation instructions or related status records change.

## Current counts

- 128 capabilities
- 38 P0
- 68 P1
- 21 P2
- 1 P3

New ideas captured from the product review remain proposal/test/validation statuses unless explicitly accepted. This includes, among others, Decision Receipt, “what would change your mind,” insufficient-information response, Divergence Anatomy, Common Ground, Signal Health Card, Signal half-life, Institution Response Room, Local KEFE, embeddable cards, source diversity, open methodology and privacy-safe research export.
