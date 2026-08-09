# F4 RAW Result Gap Interpretation — 2026-08-09

## State

Candidate implementation on top of PR #355. GitHub Actions is account-disabled and therefore exact-head CI is pending.

## Finding

The layer-aware methodology footer from PR #355 prevents RAW from being called a trusted sample, but the Result card still rendered `KEFE Gap` interpretation for any layer that had a selected option and a top option.

That could turn an early Connected Alpha RAW population into language such as community leader/majority/gap even though RAW explicitly carries no representativeness claim.

## Candidate change

- `RevealResultCard` now gates the interpretive gap surface on exact `layer == TRUSTED`.
- RAW keeps observed distribution, selected decision and methodology note.
- Unknown/future layers fail closed and do not receive the gap insight.
- No mobile sample-size threshold is introduced.
- TRUSTED behavior is preserved.

## Evidence added

- `docs/contracts/raw-result-gap-interpretation.v1.json`
- `docs/adr/0128-raw-result-gap-interpretation-boundary.md`
- `scripts/validate_raw_result_gap_interpretation.py`
- `apps/mobile/test/raw_result_gap_interpretation_test.dart`

## CI discipline change

No dedicated GitHub Actions workflow is added for this slice. The executable guard and focused Flutter test are wired into the existing `Mobile CI` gate. This is the first Connected Alpha child slice after the Actions account restriction where validation is deliberately consolidated instead of creating another standalone workflow.

## Preserved boundaries

- Commit First
- Blind First
- immutable published CaseVersion
- generic case-agnostic Flow
- Collective Result is not automatically Signal
- My KEFE descriptive-only
- Product Preview / production isolation
- no statistical or representativeness claim for RAW

## Verification pending

After GitHub restores Actions access, exact-head evidence must include:

1. existing Mobile CI created for this head;
2. repository guard PASS;
3. Dart format/analyze PASS;
4. focused RAW/TRUSTED/unknown-layer tests PASS;
5. normal mobile regression suite PASS.

No missing workflow run is treated as PASS.
