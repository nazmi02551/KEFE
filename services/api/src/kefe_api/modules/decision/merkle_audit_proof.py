from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class MerkleProofStatus(StrEnum):
    INCLUSION_VERIFIED = "INCLUSION_VERIFIED"
    CONSISTENCY_PROVEN = "CONSISTENCY_PROVEN"
    PROOF_CHALLENGED_TAMPERED = "PROOF_CHALLENGED_TAMPERED"


@dataclass(frozen=True, slots=True)
class MerkleAuditProofResult:
    leaf_id: str
    root_epoch_id: str
    merkle_root_hash: str
    proof_depth: int
    status: MerkleProofStatus
    verified_timestamp: str


class MerkleAuditProofService:
    @staticmethod
    def verify_proof(
        *,
        leaf_id: str,
        root_epoch_id: str,
        merkle_root_hash: str,
        proof_depth: int,
        status: MerkleProofStatus,
        verified_timestamp: str | None = None,
    ) -> MerkleAuditProofResult:
        if len(merkle_root_hash.strip()) < 32:
            raise ValueError("merkle_root_hash must have at least 32 characters")
        if proof_depth < 1:
            raise ValueError(f"proof_depth must be >= 1, got {proof_depth}")

        ts = verified_timestamp or datetime.now(UTC).isoformat()

        return MerkleAuditProofResult(
            leaf_id=leaf_id.strip(),
            root_epoch_id=root_epoch_id.strip(),
            merkle_root_hash=merkle_root_hash.strip(),
            proof_depth=proof_depth,
            status=status,
            verified_timestamp=ts,
        )
