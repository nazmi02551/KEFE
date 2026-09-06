# ADR-0248: Signal Health Card (CAP-044)

## Status
ACCEPTED

## Context
A fundamental pillar of KEFE (`KEFE-MPD-001`, `KEFE-TIM-001`) is that a raw Collective Result is not automatically an authoritative Signal. In conventional polling, raw vote counts are treated as public sentiment even when astroturfed by bots, skewed by vocal minorities, or derived from split-second unreflective clicks.

To prevent democratic distortion and provide verified institutional standing (`CAP-042`, `CAP-044`), every deliberation aggregate must undergo a transparent multi-dimensional **Signal Health Audit** before it qualifies for institutional impact delivery or public consensus citation.

## Decision
1. Implement the **Signal Health Card** (`KEFE-SIGNAL-HEALTH-001`):
   - **Sample Size Sufficiency**: Minimum core deliberation threshold ($N \ge 100$).
   - **Bot & Astroturfing Shield**: Algorithmic inauthentic coordination audit ($\ge 0.85$ score).
   - **Demographic & Segment Entropy**: Representation diversity across backgrounds ($\ge 0.70$ score).
   - **Deliberation Depth**: Ratio of reflective deliberation, time-on-dilemma, and reason articulation ($\ge 0.65$ score).
   - **Temporal Freshness**: Half-life decay tracking confirming the signal is actively relevant and not stale.
2. Define 3 deterministic qualification states:
   - `QUALIFIED_SIGNAL`: Passes all core gates; eligible for institutional delivery.
   - `PROVISIONAL_TREND`: Emerging pattern; lacks full sample or diversity threshold.
   - `UNQUALIFIED_NOISE`: Fails integrity or bot thresholds; quarantined from Signal feeds.
3. Expose the health audit through `GET /v1/signals/{signal_id}/health`.
4. Provide a rich mobile component (`SignalHealthCard`) displaying health metrics and cryptographic methodology hash.

## Consequences
- Protects public debate from manufactured consensus.
- Clear, auditable gate separating raw participation from qualified civic Signal.
