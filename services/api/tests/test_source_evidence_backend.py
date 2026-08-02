from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.source_evidence import (
    FinalRawSourceEvidenceError,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
    canonical_storage_ref,
)
from kefe_api.modules.knowledge.source_evidence_backend import (
    DurableRawSourceEvidenceStore,
    FinalRawEvidenceBackendError,
    InMemoryRawEvidenceBackendProfileRegistry,
    InMemoryRawEvidenceBackendRegistry,
    RawEvidenceBackendProfile,
    RawEvidencePutOutcome,
    RawEvidenceReadResult,
    RawEvidenceWriteResult,
    RetryableRawEvidenceBackendError,
)

PROFILE_CODE = "test.raw_profile.v1"
BACKEND_CODE = "test.raw_backend.v1"
ADAPTER_CODE = "test.provider.v1"
AT = datetime(2026, 8, 2, 20, 40, tzinfo=UTC)
BODY = b'{"items":[1,2,3]}'
MEDIA_TYPE = "application/json"


def _profile(**overrides) -> RawEvidenceBackendProfile:
    values = {
        "profile_code": PROFILE_CODE,
        "backend_code": BACKEND_CODE,
        "namespace": "kefe/raw-evidence",
        "max_object_bytes": 1024,
        "write_timeout_ms": 1500,
        "read_timeout_ms": 1700,
        "atomic_put_if_absent": True,
        "immutable_objects": True,
        "read_after_write_verification": True,
        "capability_evidence_ref": "evidence://capability/raw-backend-v1",
    }
    values.update(overrides)
    return RawEvidenceBackendProfile(**values)


class FakeDurableBackend:
    def __init__(self, backend_code: str = BACKEND_CODE) -> None:
        self._backend_code = backend_code
        self.objects: dict[str, tuple[bytes, str | None]] = {}
        self.events: list[str] = []
        self.put_calls: list[tuple[str, bytes, str | None, int]] = []
        self.read_calls: list[tuple[str, int]] = []
        self.put_error: BaseException | None = None
        self.read_error: BaseException | None = None
        self.write_result_override = None
        self.read_result_override = None

    @property
    def backend_code(self) -> str:
        return self._backend_code

    def put_if_absent(
        self,
        *,
        object_key: str,
        body: bytes,
        media_type: str | None,
        timeout_ms: int,
    ):
        self.events.append("put")
        owned = memoryview(body).tobytes()
        self.put_calls.append((object_key, owned, media_type, timeout_ms))
        if self.put_error is not None:
            raise self.put_error
        if self.write_result_override is not None:
            return self.write_result_override
        outcome = RawEvidencePutOutcome.ALREADY_EXISTS
        if object_key not in self.objects:
            self.objects[object_key] = (owned, media_type)
            outcome = RawEvidencePutOutcome.CREATED
        return RawEvidenceWriteResult(
            outcome=outcome,
            object_key=object_key,
            byte_length=len(owned),
        )

    def read_exact(self, *, object_key: str, timeout_ms: int):
        self.events.append("read")
        self.read_calls.append((object_key, timeout_ms))
        if self.read_error is not None:
            raise self.read_error
        if self.read_result_override is not None:
            return self.read_result_override
        body, media_type = self.objects[object_key]
        return RawEvidenceReadResult(
            object_key=object_key,
            body=memoryview(body).tobytes(),
            media_type=media_type,
        )


def _store(backend: FakeDurableBackend | None = None):
    resolved_backend = backend or FakeDurableBackend()
    return (
        DurableRawSourceEvidenceStore(
            profile=_profile(),
            backend=resolved_backend,
        ),
        resolved_backend,
    )


def test_profile_is_immutable_exact_and_requires_all_capabilities() -> None:
    profile = _profile()

    assert profile.namespace == "kefe/raw-evidence"
    assert profile.atomic_put_if_absent is True
    assert profile.immutable_objects is True
    assert profile.read_after_write_verification is True
    with pytest.raises(FrozenInstanceError):
        profile.namespace = "changed"  # type: ignore[misc]

    for field_name in (
        "atomic_put_if_absent",
        "immutable_objects",
        "read_after_write_verification",
    ):
        with pytest.raises(ValueError):
            _profile(**{field_name: False})

    for namespace in (
        "Kefe/raw",
        " padded",
        "kefe//raw",
        "kefe/raw/",
        "kefe/../raw",
    ):
        with pytest.raises(ValueError):
            _profile(namespace=namespace)


def test_profile_and_backend_registries_reject_duplicates_and_conflicts() -> None:
    profile = _profile()
    profiles = InMemoryRawEvidenceBackendProfileRegistry((profile,))
    backend = FakeDurableBackend()
    backends = InMemoryRawEvidenceBackendRegistry((backend,))

    assert profiles.get(PROFILE_CODE) is profile
    assert backends.get(BACKEND_CODE) is backend

    with pytest.raises(ValueError, match="duplicate raw evidence backend profile"):
        InMemoryRawEvidenceBackendProfileRegistry((profile, profile))
    with pytest.raises(ValueError, match="conflicting raw evidence backend profile"):
        InMemoryRawEvidenceBackendProfileRegistry(
            (profile, _profile(read_timeout_ms=1800))
        )
    with pytest.raises(ValueError, match="duplicate raw evidence backend"):
        InMemoryRawEvidenceBackendRegistry((backend, backend))


def test_results_are_immutable_and_redact_object_keys_and_bodies() -> None:
    write = RawEvidenceWriteResult(
        outcome=RawEvidencePutOutcome.CREATED,
        object_key="kefe/raw/sha256/aa/digest",
        byte_length=12,
    )
    read = RawEvidenceReadResult(
        object_key="kefe/raw/sha256/aa/digest",
        body=b"private-body",
        media_type=MEDIA_TYPE,
    )

    assert "kefe/raw" not in repr(write)
    assert "private-body" not in repr(read)
    assert "<redacted" in repr(write)
    assert "<redacted" in repr(read)
    with pytest.raises(FrozenInstanceError):
        write.byte_length = 13  # type: ignore[misc]


def test_store_orders_atomic_put_read_verification_and_returns_canonical_seal() -> None:
    store, backend = _store()

    seal = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )

    expected_hash = canonical_content_hash(BODY)
    digest = expected_hash.removeprefix("sha256:")
    expected_key = f"kefe/raw-evidence/sha256/{digest[:2]}/{digest}"
    assert backend.events == ["put", "read"]
    assert backend.put_calls == [(expected_key, BODY, MEDIA_TYPE, 1500)]
    assert backend.read_calls == [(expected_key, 1700)]
    assert seal.content_hash == expected_hash
    assert seal.storage_ref == canonical_storage_ref(expected_hash)
    assert seal.byte_length == len(BODY)
    assert seal.media_type == MEDIA_TYPE
    assert seal.sealed_at == AT
    assert expected_key not in repr(seal)


def test_existing_object_is_idempotent_and_still_read_back_verified() -> None:
    store, backend = _store()

    first = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )
    second = store.seal(
        adapter_code=ADAPTER_CODE,
        body=BODY,
        media_type=MEDIA_TYPE,
        sealed_at=AT,
    )

    assert first == second
    assert backend.events == ["put", "read", "put", "read"]
    assert len(backend.objects) == 1


def test_missing_or_mismatched_read_after_write_fails_closed() -> None:
    backend = FakeDurableBackend()
    backend.read_error = KeyError("private-object-key")
    store, _ = _store(backend)

    with pytest.raises(RetryableRawSourceEvidenceError) as missing:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )
    assert missing.value.code == "RAW_EVIDENCE_READ_AFTER_WRITE_MISSING"
    assert "private-object-key" not in str(missing.value)

    backend = FakeDurableBackend()
    backend.read_result_override = RawEvidenceReadResult(
        object_key="kefe/raw-evidence/sha256/aa/other",
        body=b"different",
        media_type=MEDIA_TYPE,
    )
    store, _ = _store(backend)
    with pytest.raises(FinalRawSourceEvidenceError) as mismatched_key:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )
    assert mismatched_key.value.code == "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"

    backend = FakeDurableBackend()
    backend.read_result_override = RawEvidenceReadResult(
        object_key=(
            "kefe/raw-evidence/sha256/"
            f"{canonical_content_hash(BODY)[7:9]}/"
            f"{canonical_content_hash(BODY).removeprefix('sha256:')}"
        ),
        body=b"different",
        media_type=MEDIA_TYPE,
    )
    store, _ = _store(backend)
    with pytest.raises(FinalRawSourceEvidenceError) as mismatched_body:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )
    assert mismatched_body.value.code == "RAW_EVIDENCE_READ_AFTER_WRITE_MISMATCH"


@pytest.mark.parametrize(
    ("error", "expected_type", "expected_code"),
    [
        (
            RetryableRawEvidenceBackendError(
                "RAW_EVIDENCE_BACKEND_RATE_LIMITED"
            ),
            RetryableRawSourceEvidenceError,
            "RAW_EVIDENCE_BACKEND_RATE_LIMITED",
        ),
        (
            FinalRawEvidenceBackendError(
                "RAW_EVIDENCE_BACKEND_POLICY_BLOCKED"
            ),
            FinalRawSourceEvidenceError,
            "RAW_EVIDENCE_BACKEND_POLICY_BLOCKED",
        ),
        (
            TimeoutError("private endpoint"),
            RetryableRawSourceEvidenceError,
            "RAW_EVIDENCE_BACKEND_TIMEOUT",
        ),
        (
            OSError("private endpoint"),
            RetryableRawSourceEvidenceError,
            "RAW_EVIDENCE_BACKEND_UNAVAILABLE",
        ),
    ],
)
def test_backend_errors_remain_bounded_without_private_exception_text(
    error: BaseException,
    expected_type: type[BaseException],
    expected_code: str,
) -> None:
    backend = FakeDurableBackend()
    backend.put_error = error
    store, _ = _store(backend)

    with pytest.raises(expected_type) as caught:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )

    assert caught.value.code == expected_code
    assert "private endpoint" not in str(caught.value)
    assert backend.events == ["put"]


def test_invalid_backend_results_and_backend_code_mismatch_fail_final() -> None:
    with pytest.raises(ValueError, match="backend code mismatch"):
        DurableRawSourceEvidenceStore(
            profile=_profile(),
            backend=FakeDurableBackend("test.other_backend.v1"),
        )

    backend = FakeDurableBackend()
    backend.write_result_override = object()
    store, _ = _store(backend)
    with pytest.raises(FinalRawSourceEvidenceError) as invalid_write:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )
    assert invalid_write.value.code == "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
    assert backend.events == ["put"]

    backend = FakeDurableBackend()
    backend.read_result_override = object()
    store, _ = _store(backend)
    with pytest.raises(FinalRawSourceEvidenceError) as invalid_read:
        store.seal(
            adapter_code=ADAPTER_CODE,
            body=BODY,
            media_type=MEDIA_TYPE,
            sealed_at=AT,
        )
    assert invalid_read.value.code == "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
    assert backend.events == ["put", "read"]
