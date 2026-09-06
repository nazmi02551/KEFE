# ADR-0259: Signal Target Registry and Institutional Binding (CAP-048)

## Status
ACCEPTED

## Context
A major shortcoming of online civic petitions and opinion polls is the absence of clear institutional targeting: signals demand vague outcomes without specifying the exact public body, municipality, regulator, or corporate board with the authority to act. Conversely, activist groups often mistakenly direct municipal complaints to federal ministries or national issues to local councils.

In the KEFE architecture:
1. Every civic signal reaching impact phase must map to a governed `Signal Target Registry`.
2. Targets are classified by type (`MUNICIPAL_GOVERNMENT`, `MINISTRY_DEPARTMENT`, `REGULATORY_BODY`, `PUBLIC_UTILITY`, etc.) and evaluated for jurisdictional congruence with the signal's measured scope (CAP-046).
3. The platform tracks the dispatch lifecycle (`PROPOSED_TARGET` -> `VERIFIED_TARGET` -> `DISPATCHED` -> `ACKNOWLEDGED` -> `ACTION_PLEDGED`) with cryptographic dispatch proofs.

## Decision
1. **Registry Model:**
   - Define `SignalTargetItem` capturing `target_id`, `target_name`, `target_type`, `jurisdiction_level`, `official_contact_channel`, `dispatch_status`, `dispatched_at`, `acknowledged_at`, and `response_due_days`.
   - Maintain a designated `primary_target_id` and list of secondary interested entities.
2. **Cryptographic Dispatch Audit:**
   - Create `registry_proof_hash` via SHA-256 over signal ID, case version ID, primary target, status, and timestamp.
3. **Backend & Mobile Parity:**
   - Expose `GET /v1/signals/{signal_id}/targets` in `kefe_api`.
   - Expose `SignalTargetRegistryCard` in mobile displaying target bodies, official statuses, response deadlines, and verification hashes.

## Invariants
- `DESIGNATED_INSTITUTIONAL_TARGET`: A signal entering the impact phase cannot have an empty target registry.
- `JURISDICTIONAL_SCOPE_MATCH`: Primary target authority must match signal scope level.
- `NON_COERCIVE_NOTIFICATION`: Transmissions are objective civic notifications, not partisan pressure campaigns.
- `LIFECYCLE_ACCOUNTABILITY`: Full visibility into acknowledgment and response timelines.

## Verification
- Executable Contract: `docs/contracts/signal-target-registry.v1.json`
- Pytest Unit: `services/api/tests/test_signal_target_registry.py`
- Pytest API: `services/api/tests/test_signal_target_registry_api.py`
- Flutter Domain & Tests: `apps/mobile/lib/features/impact/domain/signal_target_models.dart`, `apps/mobile/test/signal_target_registry_test.dart`
