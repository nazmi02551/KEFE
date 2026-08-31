# ADR-0144 — Privacy deletion completion confirmation

Status: CANDIDATE  
Date: 2026-08-31  
Issue: #399  
Capability: CAP-085  
Parent: PR #398 exact-green head `61928c36489feede0cd550ab64d4db98b7be27e6`

## Context

The mobile privacy flow already requires the exact typed `DELETE` token, sends
the actor-bound server confirmation, validates every required deletion result
field and clears local credentials only after that validation succeeds. The UI
then navigates directly to `/welcome`, so the user receives no explicit
confirmation of what completed.

Product Preview uses an isolated sample repository. A shared production-style
success message would incorrectly imply that Preview deleted a production
account or live user data.

## Decision

1. Mobile shows a completion dialog only after `PrivacyRepository.delete`
   returns a successfully validated receipt.
2. The production confirmation states only the two results that the HTTP
   repository has already validated: private product data was deleted and
   aggregate contributions were anonymized.
3. The dialog never renders receipt ID, actor ID, deletion timestamp, policy
   version, credentials or other internal metadata.
4. The completion dialog cannot be dismissed with the barrier or system back
   action. The user explicitly chooses Continue before the existing `/welcome`
   navigation occurs.
5. Product Preview marks its local receipt as sample-only. Its completion copy
   says that Preview sample data was reset and explicitly says that no
   production account or live data was deleted.
6. Presentation code uses typed receipt provenance rather than inspecting a
   policy-version string.
7. A cancelled or failed deletion never shows completion and never navigates.
8. The exact `DELETE` input, actor-bound request, fail-closed receipt
   validation, credential clearing order, privacy feature gate, API, OpenAPI,
   persistence and database semantics remain unchanged.

## Presentation and accessibility

- Turkish and English express the same bounded outcome.
- Stable widget keys identify the completion dialog and Continue action.
- The dialog has a clear success icon, title and single explicit action.
- Light/dark themes, compact phones, enlarged text and screen readers remain
  supported by the existing Material dialog composition.

## Security and methodology boundary

The confirmation does not constitute legal certification, retention proof,
deployed production proof or human usability approval. It introduces no
analytics, inference, ranking, recommendation, Signal or Impact behavior.

## Verification

The executable contract
`docs/contracts/privacy-deletion-completion-confirmation.v1.json`, repository
guard, Turkish/English widget tests, Preview-isolation test and full mobile
regression suite must pass. API CI, Mobile CI, MVP Beta Gates and Global
Readiness must all complete on the same exact PR head before this candidate is
called PASS.

## Lifecycle

This candidate does not promote CAP-085 and does not update
`docs/status/CURRENT.md`. Human review, legal review and capability governance
remain separate gates.
