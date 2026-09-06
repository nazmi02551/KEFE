# ADR-0258: MethodologyVersion-Pinned Signal History and Immutability Chain (CAP-047)

## Status
ACCEPTED

## Context
In civic deliberation and algorithmic governance platforms, a frequent epistemic failure is the retroactive alteration of past consensus records when underlying statistical, clustering, or weighting algorithms are upgraded. When a platform updates its entropy calculations, outlier exclusion criteria, or bot filtering algorithms, recalculating past signals silently rewrites history. This destroys legal and institutional accountability: an institution might act upon a "Gold Standard" signal certified at time $T$, only to find that months later the system displays a different percentage or status for that historical moment.

The KEFE Constitution establishes that:
1. Every Signal computation is an immutable factual event pinned to the exact `MethodologyVersion` active at calculation time.
2. Signal history must be append-only and cryptographically chained (Merkle-style parent hash linking).
3. If an upgraded methodology yields different numbers when run against the same raw dataset, the system must transparently compute and display a `MethodologyDelta`, distinguishing algorithmic refinements from genuine public opinion shifts.

## Decision
1. **Immutable Snapshot Architecture:**
   - Define `SignalSnapshot` recording `snapshot_id`, `methodology_version` (SemVer e.g. `v1.2.0-entropy`), `methodology_name`, `sample_size`, `confidence_score`, `consensus_distribution`, `calculated_at`, `parent_snapshot_hash`, and `snapshot_hash`.
2. **Cryptographic Chaining:**
   - `snapshot_hash` is computed as `SHA-256(parent_hash:methodology_version:sample_size:confidence:distribution:timestamp)`.
   - The chain validity can be verified independently by any auditor traversing snapshots from root to head.
3. **Transparent Methodology Delta:**
   - When a new snapshot is appended under an updated methodology version, a `MethodologyDelta` is computed tracking `distribution_shift`, `confidence_delta`, and explicit audit notes.
4. **Backend & Mobile Parity:**
   - Backend exposes `GET /v1/signals/{signal_id}/versioning`.
   - Mobile exposes `SignalVersioningCard` with version tags, hash chain verification badge, and methodology delta breakdown.

## Invariants
- `METHODOLOGY_VERSION_PINNING`: No signal exists without an explicit SemVer methodology string and hash.
- `APPEND_ONLY_SIGNAL_HISTORY`: Historical snapshots are write-once, read-many; no update or delete operations permitted.
- `CRYPTOGRAPHIC_PROVENANCE_CHAIN`: Every snapshot must verify against its parent hash.
- `METHODOLOGY_MIGRATION_TRANSPARENCY`: Discrepancies between methodology versions are isolated and explained.

## Verification
- Executable Contract: `docs/contracts/signal-versioning.v1.json`
- Pytest Unit: `services/api/tests/test_signal_versioning.py`
- Pytest API: `services/api/tests/test_signal_versioning_api.py`
- Flutter Domain & Tests: `apps/mobile/lib/features/signal/domain/signal_versioning_models.dart`, `apps/mobile/test/signal_versioning_test.dart`
