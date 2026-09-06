# ADR-0255: Methodology-Qualified Signal Qualification Engine (CAP-042)

## Status
ACCEPTED

## Context
Under KEFE's constitutional foundation (`KEFE-MPD-001`, `KEFE-TIM-001`, `KEFE-RM-001`), a fundamental distinction exists between a **Raw Collective Result** and an **Authoritative Public Signal**:
1. **Raw Collective Result**: The mere count, percentage split, and distribution of participant votes after blind commit. Raw results are vulnerable to inorganic brigading, temporary viral spikes, and shallow click-throughs.
2. **Methodology-Qualified Signal**: An epistemic artifact that has passed multi-dimensional integrity, diversity, and deliberation depth gates. Only Qualified Signals are permitted into institutional impact delivery, civic dashboards, and media feeds.

To implement `CAP-042` with absolute mathematical predictability and prevent arbitrary curation, the platform requires an auditable, multi-gate **Signal Qualification Engine**.

## Decision
1. Implement the **Methodology-Qualified Signal Engine** (`KEFE-SIGNAL-QUALIFICATION-001`):
   - **Sample Sufficiency Gate**: Evaluates core pre-result sample size ($N \ge 100$ for Bronze, $N \ge 250$ for Silver, $N \ge 500$ for Gold).
   - **Contribution Integrity Gate**: Verifies contributions originate exclusively from `CORE_PRE_RESULT` sessions prior to result reveal (`Blind First` invariant).
   - **Entropy & Perspective Diversity Gate**: Measures Shannon diversity index ($\ge 0.65$) across viewpoints to disqualify monolithic echo chambers.
   - **Deliberation Depth Gate**: Enforces a minimum cognitive engagement threshold ($\ge 0.60$) based on reflection dwell time, reason consideration, and counter-argument engagement.
   - **Astroturfing & Sybil Immunity Gate**: Algorithmic inauthentic coordination audit ($\ge 0.80$) preventing bot farms and coordinated brigading.

2. Classify signals into deterministic tiers:
   - `GOLD_STANDARD`: $N \ge 500$, all gates passed, eligible for all distribution channels including `POLICY_DELIBERATION_REPORT`.
   - `SILVER_VALIDATED`: $N \ge 250$, all gates passed, eligible for `CIVIC_PUBLIC_DASHBOARD` and `INSTITUTIONAL_IMPACT_DESK`.
   - `BRONZE_OBSERVED`: $N \ge 100$, all gates passed, eligible for `CIVIC_PUBLIC_DASHBOARD`.
   - `UNQUALIFIED`: Fails sample or integrity gates; barred from institutional channels.

3. Calculate deterministic SHA-256 `qualification_audit_hash` over the certificate payload.
4. Expose the qualification report via `GET /v1/signals/{signal_id}/qualification`.
5. Deliver a Flutter presentation component (`SignalQualificationCard`) visualizing tiers, criteria scores, and eligible dissemination channels.

## Consequences
- Guarantees that public policy and institutions only receive deeply deliberated, organic, and representative civic signals.
- Invariant "Collective Result is not automatically Signal" is strictly enforced programmatically.
