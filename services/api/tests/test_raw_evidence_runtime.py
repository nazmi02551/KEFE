from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.raw_evidence_runtime import (
    build_raw_source_evidence_store,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    RetryableRawSourceEvidenceError,
    UnconfiguredRawSourceEvidenceStore,
)
from kefe_api.modules.knowledge.source_evidence_backend import (
    DurableRawSourceEvidenceStore,
    InMemoryRawEvidenceBackendProfileRegistry,
    InMemoryRawEvidenceBackendRegistry,
    RawEvidenceBackendProfile,
    RawEvidencePutOutcome,
    RawEvidenceReadResult,
    RawEvidenceWriteResult,
)

PROFILE_CODE = "test.raw_profile.v1"
BACKEND_CODE = "test.raw_backend.v1"
AT = datetime(2026, 8, 2, 20, 50, tzinfo=UTC)


def _profile() -> RawEvidenceBackendProfile:
    return RawEvidenceBackendProfile(
        profile_code=PROFILE_CODE,
        backend_code=BACKEND_CODE,
        namespace="kefe/raw-evidence",
        max_object_bytes=1024,
        write_timeout_ms=500,
        read_timeout_ms=500,
        atomic_put_if_absent=True,
        immutable_objects=True,
        read_after_write_verification=True,
        capability_evidence_ref="evidence://capability/test-raw-backend",
    )


class FakeBackend:
    backend_code = BACKEND_CODE

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str | None]] = {}

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
        del timeout_ms
        body, media_type = self.objects[object_key]
        return RawEvidenceReadResult(
            object_key=object_key,
            body=memoryview(body).tobytes(),
            media_type=media_type,
        )


def test_disabled_mode_returns_only_bounded_unconfigured_store() -> None:
    store = build_raw_source_evidence_store(Settings())

    assert type(store) is UnconfiguredRawSourceEvidenceStore
    assert not isinstance(store, InMemoryRawSourceEvidenceStore)
    with pytest.raises(RetryableRawSourceEvidenceError) as caught:
        store.seal(
            adapter_code="test.provider.v1",
            body=b"body",
            media_type="application/json",
            sealed_at=AT,
        )
    assert caught.value.code == "RAW_EVIDENCE_STORE_UNAVAILABLE"


def test_disabled_mode_rejects_ambiguous_profile_selection() -> None:
    settings = Settings(
        raw_evidence_runtime_mode="DISABLED",
        raw_evidence_backend_profile_code=PROFILE_CODE,
    )

    with pytest.raises(
        RuntimeError,
        match="RAW_EVIDENCE_PROFILE_FORBIDDEN_WHEN_DISABLED",
    ):
        build_raw_source_evidence_store(settings)


def test_external_mode_requires_exact_registered_profile_and_backend() -> None:
    with pytest.raises(
        RuntimeError,
        match="RAW_EVIDENCE_BACKEND_PROFILE_REQUIRED",
    ):
        build_raw_source_evidence_store(
            Settings(raw_evidence_runtime_mode="EXTERNAL_DURABLE")
        )

    settings = Settings(
        raw_evidence_runtime_mode="EXTERNAL_DURABLE",
        raw_evidence_backend_profile_code=PROFILE_CODE,
    )
    with pytest.raises(
        RuntimeError,
        match="RAW_EVIDENCE_BACKEND_PROFILE_NOT_REGISTERED",
    ):
        build_raw_source_evidence_store(settings)

    profiles = InMemoryRawEvidenceBackendProfileRegistry((_profile(),))
    with pytest.raises(
        RuntimeError,
        match="RAW_EVIDENCE_BACKEND_NOT_REGISTERED",
    ):
        build_raw_source_evidence_store(
            settings,
            profiles=profiles,
        )


def test_external_mode_builds_only_exact_durable_store_without_fallback() -> None:
    settings = Settings(
        environment="production",
        raw_evidence_runtime_mode="EXTERNAL_DURABLE",
        raw_evidence_backend_profile_code=PROFILE_CODE,
    )
    backend = FakeBackend()
    store = build_raw_source_evidence_store(
        settings,
        profiles=InMemoryRawEvidenceBackendProfileRegistry((_profile(),)),
        backends=InMemoryRawEvidenceBackendRegistry((backend,)),
    )

    assert type(store) is DurableRawSourceEvidenceStore
    assert not isinstance(store, InMemoryRawSourceEvidenceStore)
    assert not isinstance(store, UnconfiguredRawSourceEvidenceStore)
    seal = store.seal(
        adapter_code="test.provider.v1",
        body=b"body",
        media_type="application/json",
        sealed_at=AT,
    )
    assert seal.byte_length == 4
    assert len(backend.objects) == 1


def test_profile_selector_rejects_blank_or_padded_values() -> None:
    for value in ("", " padded "):
        with pytest.raises(ValidationError):
            Settings(raw_evidence_backend_profile_code=value)
