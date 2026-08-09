# F4 Context Source Trust Presentation — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #360  
Parent: PR #359 / `e594c555b294505d55069581b1a616ca57376fed`  
Capabilities: CAP-069, CAP-070, CAP-095  
ADR: ADR-0130  
Contract: `docs/contracts/context-source-trust-presentation.v1.json`

## Finding

Both consumer Context source presentations previously rendered `Icons.verified_outlined` for every `CaseContextSource`.

The domain model does not contain a source-verification state. It contains source provenance metadata only. Verification-like status belongs separately to `CaseContextBlock.claimStatus`.

The old icon therefore risked visually representing “this source is verified” without runtime evidence for that claim.

## Implemented candidate

- shared `_ContextSourceTile` used by both legacy and progressive Context views;
- neutral link/reference iconography replaces unconditional verified-source iconography;
- progressive Sources layer header also uses neutral reference iconography;
- explicit TR `Kaynak kaydı` and EN `Source reference` presentation copy;
- publisher and source-kind metadata remain visible;
- optional existing URL host may be rendered only as provenance metadata;
- block-level `VERIFIED / CLAIMED / DISPUTED / UNKNOWN` semantics remain unchanged;
- no source verification field, score or methodology is invented;
- focused widget tests preserve `Doğrulandı` at the claim/block level while requiring neutral source records;
- executable repository guard added;
- guard is folded into existing `Mobile CI`; no feature-specific workflow was added.

## Trust meaning

This candidate makes four non-equivalences explicit:

1. source exists != source is verified;
2. publisher/source type != source is verified;
3. URL exists != source is verified;
4. a linked information block being `VERIFIED` != every linked source being independently verified.

A future source-verification capability requires its own accepted methodology, explicit domain state and evidence lifecycle. It must not be inferred from provenance metadata.

## Architecture scope

No changes to:

- FastAPI or repository composition;
- public API/OpenAPI;
- PostgreSQL schema or migrations;
- Context API response shape;
- CaseVersion or Flow semantics;
- Commit First / pre-result isolation;
- Result / Signal / Impact semantics;
- Product Preview / production isolation;
- external URL launching/native platform dependencies.

## Verification state

GitHub Actions is currently disabled at account level. The candidate therefore makes no exact-head PASS claim.

After Actions access is restored, the existing Mobile CI must execute on the exact reviewed head and prove:

- Context source trust repository guard;
- Dart formatting;
- Flutter analyze;
- focused Context widget tests through the full mobile test suite;
- existing Connected Alpha and RAW-result presentation guards;
- Connected Alpha compile-only boundary;
- Product Preview build boundary.

Until then this remains an implemented candidate only.

## Lifecycle

No CAP lifecycle status is changed by this slice. CAP-069 and CAP-070 remain governed by the Product Bible/capability portfolio authority, and CAP-095 remains an ongoing mandatory quality boundary.
