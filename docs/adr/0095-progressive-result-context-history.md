# ADR-0095: Progressive Result, Context and Descriptive History Surfaces

- Status: Accepted for implementation
- Date: 2026-08-04
- Issue: #285
- Runtime base: PR #284 exact verified head `08b5c0b97fc0dd3402b2d86ee1422d9595031e58`
- Capabilities: CAP-001, CAP-008, CAP-009, CAP-031, CAP-035, CAP-095

## Context

ADR-0094 and PR #284 introduced a focused top-level Flow journey and a card-by-card sub-journey inside `DECISION`. Several adjacent surfaces still accumulate independent capabilities in one vertical column:

- `COLLECTIVE_RESULT` renders Reveal, Perspective, Consensus, Community Reasons, Progress and Share together;
- Context presents essential information, optional details and sources inside one dense card;
- My KEFE recent journeys are static summaries rather than inspectable observed timelines;
- repeated `DECISION` primitives are visually labelled like the first decision even when they represent a runtime-authoritative reweigh.

The product discussion already identified these as the remaining meaningful progressive transformations. Browse and comparison surfaces must not be converted into artificial wizards.

## Decision

### 1. Post-Commit presentation sub-journey

`COLLECTIVE_RESULT` remains the sole authoritative Flow primitive. The mobile presentation derives four local stages from capabilities already valid after Commit:

1. result — own decision and collective distribution;
2. perspectives — curated different perspectives and methodology;
3. participation — Consensus and Community Reasons;
4. completion — My KEFE progress, sharing and first-use continuation.

Only one stage is focused at a time. Back and forward navigation changes presentation state only; it never changes, resends or recommits the decision. Every enabled post-Commit capability remains reachable. Perspective retry keeps the existing bounded controller contract and never replays answer, private reason, Commit or Reveal.

### 2. Context progressive disclosure

Context remains server-authoritative and non-blocking. In the progressive Decision experience, Context derives these local layers from the existing snapshot:

1. essential summary and essential blocks;
2. optional details, when present;
3. sources, when present.

The user may explicitly continue the authoritative Flow after reviewing the essential layer. Details and sources remain reachable but do not become domain steps and do not block Decision. The legacy Context renderer remains unchanged by default.

### 3. Reweigh and Reflection semantics

Repeated `DECISION` primitives remain separate runtime steps. Presentation determines whether the active Decision has an earlier Decision in the same pinned runtime and labels it as a reweigh without Case-specific branching. `REFLECTION` remains one focused terminal card and keeps observed, descriptive and non-causal wording.

### 4. My KEFE descriptive journey detail

My KEFE remains a scrollable history/dashboard surface. Each recent journey becomes expandable and displays only fields already present in the read model:

- initial Commit time;
- observed decision update count and latest decision time;
- Reflection completed/not completed.

No answer reconstruction, private reason replay, personality, ideology, psychometric profile, bias, morality, social worth or causal explanation is introduced.

### 5. Explicit non-targets

Explore, Radar, Weigh hub and the current Atlas comparison remain browse/compare surfaces. Onboarding is already staged. No Admin Studio implementation is claimed.

## Invariants

- Commit First and applicable Blind First remain binding.
- Published CaseVersion remains immutable.
- Flow runtime remains generic and authoritative.
- No new API, migration, persistence schema or Flow primitive is introduced.
- Preview fixtures never become production fallback.
- Post-Commit capabilities remain post-Commit only.
- Private reasons are not replayed.
- My KEFE remains observed/descriptive only.
- Legacy rendering and build-time rollback remain available.

## Verification

One exact runtime SHA must pass API CI, Mobile CI, MVP Beta Gates, Global Readiness and the installable phone-artifact boundary. Tests cover post-Commit stage resolution and capability reachability, optional Context progression, repeated Decision labelling, Reflection continuity and My KEFE expansion.

Automated verification is not human visual or usability approval.
