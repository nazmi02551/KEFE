from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.source_evidence import (
    MAX_EVIDENCE_BYTES,
    FinalRawSourceEvidenceError,
    InMemoryRawSourceEvidenceStore,
    RawSourceEvidenceSeal,
    RetryableRawSourceEvidenceError,
    UnconfiguredRawSourceEvidenceStore,
    canonical_content_hash,
    canonical_storage_ref,
)

ADAPTER_CODE = "test.raw_evidence.v1"
AT = datetime(2026, 8, 2, 20, 20, tzinfo=UTC)
BODY = b'{"items":[1,2,3]}'
EXPECTED_HASH = (
    "sha256:7aff5dcbe562761bfd9d8569cdd3226d3944acad6539db5d62ad3f67d9a45d0a"
)


def test_canonical_hash_reference_and_redacted_immutable_seal() -> None:
    content_hash = canonical_content_hash(BODY)
    storage_ref = canonical_storage_ref(content_hash)
    seal = RawSourceEvidenceSeal(
        content_hash=content_hash,
        storage_ref=storage_ref,
        byte_length=len(BODY),
        media_type="application/json",
        sealed_at=AT,
    )

    assert content_hash == EXPECTED_HASH
    assert storage_ref == (
        "evidence://sha256/"
        "7aff5dcbe562761bfd9d8569cdd3226d3944acad6539db5d62ad3f67d9a45d0a"
    )
    assert BODY.decode() not in repr(seal)
    assert "storage_ref=<redacted>" in repr(seal)
    with pytest.raises(FrozenInstanceError):
        seal.byte_length = 0  # type: ignore[misc]


def test_in_memory_store_is_content_addressed_idempotent_and_owns_bytes() -> None:
    store = InMemoryRawSourceEvidenceStore()
    first = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type="application/json",
        sealed_at=AT,
    )
    second = store.seal(
        adapter_code=ADAPTER_CODE,
        body=memoryview(BODY).tobytes(),
        media_type="application/json",
        sealed_at=AT,
    )

    assert first == second
    assert first.content_hash == EXPECTED_HASH
    assert store.object_count == 1
    first_copy = store.read_owned_copy(first.storage_ref)
    second_copy = store.read_owned_copy(first.storage_ref)
    assert first_copy == BODY
    assert second_copy == BODY
    assert first_copy is not second_copy


def test_in_memory_store_fails_closed_on_injected_digest_collision() -> None:
    store = InMemoryRawSourceEvidenceStore()
    content_hash = canonical_content_hash(BODY)
    store._bodies[content_hash] = b"different-owned-bytes"  # noqa: SLF001

    with pytest.raises(FinalRawSourceEvidenceError) as caught:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type="application/json",
            sealed_at=AT,
        )

    assert caught.value.code == "RAW_EVIDENCE_DIGEST_COLLISION"
    assert BODY.decode() not in str(caught.value)


@pytest.mark.parametrize(
    ("body", "media_type", "sealed_at"),
    [
        (bytearray(BODY), "application/json", AT),
        (b"x" * (MAX_EVIDENCE_BYTES + 1), "application/json", AT),
        (BODY, "Application/JSON", AT),
        (BODY, "application/json; charset=utf-8", AT),
        (BODY, "application/json", datetime(2026, 8, 2, 20, 20)),
    ],
)
def test_invalid_evidence_inputs_fail_before_storage(
    body,
    media_type: str | None,
    sealed_at: datetime,
) -> None:
    store = InMemoryRawSourceEvidenceStore()

    with pytest.raises(ValueError):
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=body,
            media_type=media_type,
            sealed_at=sealed_at,
        )

    assert store.object_count == 0


def test_seal_rejects_hash_reference_length_media_and_time_drift() -> None:
    content_hash = canonical_content_hash(BODY)
    reference = canonical_storage_ref(content_hash)

    with pytest.raises(ValueError, match="derive"):
        RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=(
                "evidence://sha256/"
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            byte_length=len(BODY),
            media_type="application/json",
            sealed_at=AT,
        )
    with pytest.raises(ValueError, match="byte_length"):
        RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=reference,
            byte_length=MAX_EVIDENCE_BYTES + 1,
            media_type="application/json",
            sealed_at=AT,
        )
    with pytest.raises(ValueError, match="media_type"):
        RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=reference,
            byte_length=len(BODY),
            media_type="Application/JSON",
            sealed_at=AT,
        )
    with pytest.raises(ValueError, match="UTC"):
        RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=reference,
            byte_length=len(BODY),
            media_type="application/json",
            sealed_at=datetime(2026, 8, 2, 20, 20),
        )


def test_unconfigured_store_is_bounded_retryable_and_redacted() -> None:
    store = UnconfiguredRawSourceEvidenceStore()

    with pytest.raises(RetryableRawSourceEvidenceError) as caught:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type="application/json",
            sealed_at=AT,
        )

    assert caught.value.code == "RAW_EVIDENCE_STORE_UNAVAILABLE"
    assert BODY.decode() not in str(caught.value)
