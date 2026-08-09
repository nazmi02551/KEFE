# F4 RAW Result Methodology Presentation — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #354

Parent: PR #352 / `6cbf19b9a855bf5531ed74bbf4362696281ebbaf`

## Finding

The live RAW Collective Result backend candidate returns `layer=RAW` and `confidence=INSUFFICIENT`, while the mobile Result methodology footer previously ignored `layer` and always used the existing TRUSTED formulation. In Turkish this included `Güvenilir örneklem`; in English, `Trusted sample`. The confidence resolver also rendered unknown codes literally.

That would overstate the methodology of a live alpha participation aggregate.

## Implemented candidate

- dedicated Result-methodology localization catalog for RAW and unknown layers;
- layer-aware `resultMethodologyForLayer()` resolver;
- TRUSTED delegates to the existing Internal Alpha methodology copy unchanged;
- RAW Turkish copy uses `Gözlenen kaydedilmiş katılım`, `Güven düzeyi hesaplanmadı`, and `Temsiliyet iddiası yok`;
- RAW English copy uses `Observed committed participation`, `Confidence not assessed`, and `No representativeness claim`;
- unknown future layers use a neutral layer label and never silently become TRUSTED;
- `RevealResultCard` now passes the actual `reveal.layer` into methodology resolution;
- Result layout, percentages, animations, selected option, KEFE Gap and semantics are otherwise unchanged;
- focused TR/EN tests cover RAW, TRUSTED backward compatibility and unknown-layer fallback;
- executable repository checker binds the presentation boundary.

## Methodology meaning

This is a presentation correction, not a new methodology. RAW remains observed committed participation only. The copy explicitly avoids representative-sample, statistical-confidence, Signal, Impact, truth and normative claims.

## Verification state

GitHub Actions remains unavailable for recent exact heads under Issue #353. The slice therefore remains candidate/pending even though its static contract and focused test design are present.

No human visual/usability approval, store evidence or CAP lifecycle promotion is inferred.

## Next evidence

- exact Dart format;
- Flutter analyze;
- focused RAW methodology copy tests;
- existing Result/Decision regressions;
- Mobile CI, MVP Beta Gates and Global Readiness on the exact head once Actions execution is restored.
