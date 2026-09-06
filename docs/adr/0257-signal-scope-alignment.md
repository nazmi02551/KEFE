# ADR-0257: Signal Scope Alignment Engine (CAP-046)

## Status
ACCEPTED

## Context
A fundamental invariant codified in `AGENTS.md` and constitutional authority (`KEFE-TIM-001`, `KEFE-RM-001`) is:
**"Signal/Impact do not silently broaden."**

In unprincipled survey research or activist discourse, local findings are routinely weaponized or overextended into sweeping national mandates (e.g. citing a survey of 500 tech professionals in an urban center as representing "the entire nation's will"). Such overextension distorts public policy and violates democratic legitimacy.

To enforce democratic accuracy, every Qualified Signal (`CAP-042`) must undergo explicit **Scope Alignment Verification** (`CAP-046`) before it can be presented to public decision-makers or institutional target desks (`CAP-048`, `CAP-050`).

## Decision
1. Implement the **Signal Scope Alignment Engine** (`KEFE-SIGNAL-SCOPE-001`):
   - Define four explicit `JurisdictionLevel` boundaries: `MUNICIPAL`, `REGIONAL`, `NATIONAL`, `TRANSNATIONAL`.
   - Evaluate alignment across 4 core scope dimensions:
     - `JURISDICTION`: Verifies declared authority level matches participant constituency.
     - `GEOGRAPHIC`: Binds locality and administrative borders.
     - `DEMOGRAPHIC_TARGET`: Ensures measured participants represent the affected group.
     - `TEMPORAL_WINDOW`: Imposes fixed validity windows (e.g. 90 or 180 days) after which signals decay.
   - Assign deterministic status:
     - `STRICTLY_ALIGNED`: Score $\ge 0.85$, no broadening leakage.
     - `OVERBROAD_WARNING`: Score $0.70$ - $0.84$, displays explicit boundary caveat.
     - `MISMATCH_DISQUALIFIED`: Score $< 0.70$, barred from institutional delivery.
   - Produce a cryptographic SHA-256 `scope_seal_hash` anchoring the boundaries.

2. Expose the alignment report via `GET /v1/signals/{signal_id}/scope-alignment`.
3. Provide a dedicated Flutter presentation widget (`SignalScopeAlignmentCard`) visualizing jurisdiction badges, dimensional alignment scores, and validity countdowns.

## Consequences
- Prevents special interest groups or media from misrepresenting local or specific cohort sentiments as universal mandates.
- Strictly upholds the constitutional invariant: "Signal/Impact do not silently broaden."
