# ADR-0247: User-Controlled Discovery Profile (CAP-077)

## Status
ACCEPTED

## Context
Mainstream social and media platforms employ algorithmic engagement-maximization engines (optimizing for anger, polarization, time-on-screen, and dopamine loops). These systems operate as black boxes, eroding user agency and creating ideological echo chambers.

KEFE's product constitution (`KEFE-PB-001`, `KEFE-SEC-001`, `KEFE-TIM-001`) strictly prohibits engagement-maximizing algorithms. Exploration of ethical dilemmas must remain transparent, educational, and under the explicit intentional control of the citizen.

## Decision
1. Implement a **User-Controlled Discovery Profile** (`KEFE-USER-DISCOVERY-001`):
   - **Preferred Domains**: Explicitly chosen fields of interest (`CIVIC`, `TECHNOLOGY`, `BIOETHICS`, `ENVIRONMENT`, `JUSTICE`, `ECONOMIC`).
   - **Complexity Level**: User-calibrated intellectual depth (`INTRODUCTORY`, `BALANCED`, `DEEP_DELIBERATION`).
   - **Freshness Preference**: Dial between breaking civic events vs timeless normative foundations (`CURRENT_EVENTS`, `BALANCED`, `TIMELESS_FOUNDATIONS`).
   - **Real Event Balance**: Ratio of real historical/ongoing controversies vs distilled hypothetical dilemmas (`REAL_EVENTS_FIRST`, `BALANCED`, `HYPOTHETICALS_FIRST`).
   - **Diversification Boost**: A user-controlled slider (`0.0` to `1.0`) that intentionally exposes counter-intuitive, cross-domain dilemmas to prevent filter bubbles.
2. Expose the profile through governed API endpoints:
   - `GET /v1/discovery/profile`: Read the current user's profile with safe default fallback.
   - `PUT /v1/discovery/profile`: Idempotently update discovery preferences.
3. Provide an intuitive mobile configuration sheet (`UserDiscoveryProfileSheet`) accessible from the Explore feed.
4. Guarantee surveillance-free storage: preferences are strictly associated with the anonymous actor ID or stored locally, never commercialized or shared.

## Consequences
- Total elimination of addictive engagement algorithms.
- Full citizen agency over their deliberation curriculum.
- Clear separation between discovery preferences and constitutional neutrality invariants.
