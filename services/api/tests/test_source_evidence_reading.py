from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.source_evidence import (
    FinalRawSourceEvidenceError,
    InMemoryRawSourceEvidenceStore,
    RawSourceEvidenceRead,
    RetryableRawSourceEvidenceError,
    UnconfiguredRawSourceEvidenceStore,
    canonical_content_hash,
    canonical_storage_ref,
)
from kefe_api.modules.knowledge.source_evidence_backend import (
    DurableRawSourceEvidenceStore,
    RawEvidenceBackendProfile,
    RawEvidencePutOutcome,
    RawEvidenceReadResult,
    RawEvidenceWriteResult,
)

ADAPTER_CODE = "test.feed_evidence.v1"
BACKEND_CODE = "test.feed_backend.v1"
PROFILE_CODE = "test.feed_profile.v1"
AT = datetime(2026, 8, 3, 2, 0, tzinfo=UTC)
BODY = b"<rss version='2.0'><channel><title>Feed</title></channel></rss>"
MEDIA_TYPE = "application/rss+xml"


class FakeBackend:
    backend_code = BACKEND_CODE

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str | None]] = {}
        self.read_calls: list[tuple[str, int]] = []
        self.read_override = None

    def put_if_absent(
        self,
        *,
        object_key: str,
        body: bytes,
        media_type: str | None,
        timeout_ms: int,
    ) -> RawEvidenceWriteResult:
        del timeout_ms
        outcome = RawEvidencePutOutcome.ALREADY_EXISTS
        if object_key not in self.objects:
            self.objects[object_key] = (memoryview(body).tobytes(), media_type)
            outcome = RawEvidencePutOutcome.CREATED
        return RawEvidenceWriteResult(
            outcome=outcome,
            object_key=object_key,
            byte_length=len(body),
        )

    def read_exact(
        self,
        *,
        object_key: str,
        timeout_ms: int,
    ) -> RawEvidenceReadResult:
        self.read_calls.append((object_key, timeout_ms))
        if self.read_override is not None:
            return self.read_override
        body, media_type = self.objects[object_key]
        return RawEvidenceReadResult(
            object_key=object_key,
            body=memoryview(body).tobytes(),
            media_type=media_type,
        )


def _durable_store() -> tuple[DurableRawSourceEvidenceStore, FakeBackend]:
    backend = FakeBackend()
    profile = RawEvidenceBackendProfile(
        profile_code=PROFILE_CODE,
        backend_code=BACKEND_CODE,
        namespace="kefe/feed-evidence",
        max_object_bytes=1024 * 1024,
        write_timeout_ms=1000,
        read_timeout_ms=1200,
        atomic_put_if_absent=True,
        immutable_objects=True,
        read_after_write_verification=True,
        capability_evidence_ref="evidence://capability/feed-reader-v1",
    )
    return DurableRawSourceEvidenceStore(profile=profile, backend=backend), backend


def test_in_memory_read_returns_owned_integrity_verified_record() -> None:
    store = InMemoryRawSourceEvidenceStore()
    seal = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )

    first = store.read(
        storage_ref=seal.storage_ref,
        expected_content_hash=seal.content_hash,
    )
    second = store.read(
        storage_ref=seal.storage_ref,
        expected_content_hash=seal.content_hash,
    )

    assert type(first) is RawSourceEvidenceRead
    assert first.content_hash == canonical_content_hash(BODY)
    assert first.storage_ref == canonical_storage_ref(first.content_hash)
    assert first.body == BODY
    assert first.body is not second.body
    assert first.media_type == MEDIA_TYPE
    assert first.byte_length == len(BODY)
    assert BODY.decode() not in repr(first)
    assert seal.storage_ref not in repr(first)


def test_reference_hash_mismatch_rejected_before_object_lookup() -> None:
    store = InMemoryRawSourceEvidenceStore()
    seal = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )
    other_hash = canonical_content_hash(b"different")

    with pytest.raises(FinalRawSourceEvidenceError) as caught:
        store.read(
            storage_ref=seal.storage_ref,
            expected_content_hash=other_hash,
        )

    assert caught.value.code == "RAW_EVIDENCE_REFERENCE_HASH_MISMATCH"


def test_in_memory_read_recomputes_digest_and_detects_tampering() -> None:
    store = InMemoryRawSourceEvidenceStore()
    seal = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )
    store._bodies[seal.content_hash] = b"tampered"  # noqa: SLF001

    with pytest.raises(FinalRawSourceEvidenceError) as caught:
        store.read(
            storage_ref=seal.storage_ref,
            expected_content_hash=seal.content_hash,
        )

    assert caught.value.code == "RAW_EVIDENCE_READ_DIGEST_MISMATCH"


def test_durable_read_derives_object_key_and_recomputes_digest() -> None:
    store, backend = _durable_store()
    seal = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )
    backend.read_calls.clear()

    read = store.read(
        storage_ref=seal.storage_ref,
        expected_content_hash=seal.content_hash,
    )

    digest = seal.content_hash.removeprefix("sha256:")
    expected_key = f"kefe/feed-evidence/sha256/{digest[:2]}/{digest}"
    assert backend.read_calls == [(expected_key, 1200)]
    assert read.body == BODY
    assert read.content_hash == seal.content_hash
    assert read.storage_ref == seal.storage_ref
    assert read.media_type == MEDIA_TYPE

    backend.read_override = RawEvidenceReadResult(
        object_key=expected_key,
        body=b"tampered",
        media_type=MEDIA_TYPE,
    )
    with pytest.raises(FinalRawSourceEvidenceError) as mismatch:
        store.read(
            storage_ref=seal.storage_ref,
            expected_content_hash=seal.content_hash,
        )
    assert mismatch.value.code == "RAW_EVIDENCE_READ_DIGEST_MISMATCH"


def test_unconfigured_reader_is_bounded_retryable() -> None:
    reader = UnconfiguredRawSourceEvidenceStore()
    content_hash = canonical_content_hash(BODY)

    with pytest.raises(RetryableRawSourceEvidenceError) as caught:
        reader.read(
            storage_ref=canonical_storage_ref(content_hash),
            expected_content_hash=content_hash,
        )

    assert caught.value.code == "RAW_EVIDENCE_READER_UNAVAILABLE"
    assert BODY.decode() not in str(caught.value)
