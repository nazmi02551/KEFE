# ADR-0130 — Verification-neutral Context source presentation

Status: CANDIDATE  
Date: 2026-08-09  
Issue: #360  
Capabilities: CAP-069, CAP-070, CAP-095  
Foundation wave: F4

## Context

Consumer Context currently distinguishes information blocks by `claimStatus` (`VERIFIED`, `CLAIMED`, `DISPUTED`, `UNKNOWN`). Linked `CaseContextSource` records, however, expose only provenance metadata: source id, title, publisher, source kind, optional URL and optional publication time.

The current legacy and progressive Sources presentations render `Icons.verified_outlined` for every source record. Because the source model has no verification state, that icon can visually project block-level verification semantics onto a source whose verification has not been established by the runtime contract.

This becomes more important for Connected Alpha, where real editorial, news, research or official source records may be shown rather than preview-only fixtures.

## Decision

Source rows are **verification-neutral provenance records** unless a future accepted methodology and explicit domain field establish otherwise.

1. Source existence does not imply source verification.
2. Publisher identity, source kind and URL presence do not imply source verification.
3. `claimStatus` remains attached to the Context information block and is not copied or inferred onto linked source rows.
4. Legacy and progressive Context presentations use one shared source-tile implementation.
5. The shared tile uses neutral reference iconography and explicit TR/EN “source reference” language.
6. Existing publisher and source-kind metadata remain visible. An existing URL host may be shown as provenance metadata, but its presence is not a trust signal.
7. This slice does not introduce URL launching, a source trust score, a source-verification method, a backend field, API change or schema migration.
8. Verification-neutral source presentation must remain covered by focused widget tests and an executable repository guard in the existing Mobile CI. No feature-specific workflow is added.

## Why not add a `verified` field now?

The repository has no accepted source-verification methodology defining who verifies a source, what evidence is sufficient, how verification expires, or whether verification applies to publisher identity, document authenticity, factual claims, or all of them. Adding a Boolean would collapse those distinct concepts into an unsupported trust claim.

The correct current behavior is therefore to display what KEFE actually knows: provenance metadata plus separately governed block-level information status.

## Consequences

- A source row can still say “Official source”, “News source”, “Research” or “Editorial source”; those are descriptive source kinds, not approval badges.
- A linked block may still display “Verified / Doğrulandı” while its source row remains neutral. This is intentional: the block status is the governed claim/information state.
- The same source tile is used by legacy and progressive Context views, reducing semantic drift.
- Future source verification may be added only through a separate accepted domain/methodology contract with an explicit field and evidence lifecycle.

## Preserved boundaries

- Commit First and pre-result isolation;
- immutable published CaseVersion;
- case-agnostic Flow runtime;
- Preview/production isolation;
- raw backend/source values remain unchanged by localization;
- Collective Result remains separate from Signal;
- CAP lifecycle status is not promoted by this implementation.

## Verification

The executable contract `docs/contracts/context-source-trust-presentation.v1.json` and repository guard must prove that:

- source rows do not use unconditional verified-source iconography;
- both Context presentation modes use the shared tile;
- the source-reference copy exists in TR and EN;
- existing claim-status semantics remain present;
- no new workflow is introduced for this slice.

Exact-head Mobile CI remains required before this candidate can be called PASS.
