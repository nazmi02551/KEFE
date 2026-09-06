from __future__ import annotations

from kefe_api.modules.decision.merkle_audit_proof import (
    MerkleAuditProofResult,
    MerkleAuditProofService,
    MerkleProofStatus,
)


def test_merkle_audit_proof_verifies_inclusion() -> None:
    r = MerkleAuditProofService.verify_proof(
        leaf_id="leaf_receipt_9921",
        root_epoch_id="epoch_2026_09",
        merkle_root_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        proof_depth=8,
        status=MerkleProofStatus.INCLUSION_VERIFIED,
    )

    assert isinstance(r, MerkleAuditProofResult)
    assert r.status == MerkleProofStatus.INCLUSION_VERIFIED
    assert r.proof_depth == 8


def test_merkle_audit_invalid_depth() -> None:
    failed = False
    try:
        MerkleAuditProofService.verify_proof(
            leaf_id="leaf_err",
            root_epoch_id="ep_1",
            merkle_root_hash="short",  # < 32
            proof_depth=0,  # < 1
            status=MerkleProofStatus.PROOF_CHALLENGED_TAMPERED,
        )
    except ValueError:
        failed = True

    assert failed is True
