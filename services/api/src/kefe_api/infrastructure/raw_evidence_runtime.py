from __future__ import annotations

from datetime import datetime

from kefe_api.core.settings import Settings
from kefe_api.modules.knowledge.source_evidence import (
    RawSourceEvidenceRead,
    RawSourceEvidenceSeal,
    RawSourceEvidenceStore,
    UnconfiguredRawSourceEvidenceStore,
)
from kefe_api.modules.knowledge.source_evidence_backend import (
    DurableRawSourceEvidenceStore,
    InMemoryRawEvidenceBackendProfileRegistry,
    InMemoryRawEvidenceBackendRegistry,
    RawEvidenceBackendProfileRegistry,
    RawEvidenceBackendRegistry,
)


class ConfiguredRawSourceEvidenceStore:
    def __init__(
        self,
        *,
        delegate: DurableRawSourceEvidenceStore,
        capability_ref: str,
    ) -> None:
        self._delegate = delegate
        self._capability_ref = capability_ref

    @property
    def configured(self) -> bool:
        return True

    @property
    def capability_ref(self) -> str:
        return self._capability_ref

    def seal(
        self,
        *,
        adapter_code: str,
        body: bytes,
        media_type: str | None,
        sealed_at: datetime,
    ) -> RawSourceEvidenceSeal:
        return self._delegate.seal(
            adapter_code=adapter_code,
            body=body,
            media_type=media_type,
            sealed_at=sealed_at,
        )

    def read(
        self,
        *,
        storage_ref: str,
        expected_content_hash: str,
    ) -> RawSourceEvidenceRead:
        return self._delegate.read(
            storage_ref=storage_ref,
            expected_content_hash=expected_content_hash,
        )


def build_raw_source_evidence_store(
    settings: Settings,
    *,
    profiles: RawEvidenceBackendProfileRegistry | None = None,
    backends: RawEvidenceBackendRegistry | None = None,
) -> RawSourceEvidenceStore:
    profile_registry = profiles or InMemoryRawEvidenceBackendProfileRegistry()
    backend_registry = backends or InMemoryRawEvidenceBackendRegistry()

    if settings.raw_evidence_runtime_mode == "DISABLED":
        if settings.raw_evidence_backend_profile_code is not None:
            raise RuntimeError(
                "RAW_EVIDENCE_PROFILE_FORBIDDEN_WHEN_DISABLED"
            )
        return UnconfiguredRawSourceEvidenceStore()

    profile_code = settings.raw_evidence_backend_profile_code
    if profile_code is None:
        raise RuntimeError("RAW_EVIDENCE_BACKEND_PROFILE_REQUIRED")
    try:
        profile = profile_registry.get(profile_code)
    except KeyError as exc:
        raise RuntimeError(
            "RAW_EVIDENCE_BACKEND_PROFILE_NOT_REGISTERED"
        ) from exc
    try:
        backend = backend_registry.get(profile.backend_code)
    except KeyError as exc:
        raise RuntimeError("RAW_EVIDENCE_BACKEND_NOT_REGISTERED") from exc

    return ConfiguredRawSourceEvidenceStore(
        delegate=DurableRawSourceEvidenceStore(
            profile=profile,
            backend=backend,
        ),
        capability_ref=profile.capability_evidence_ref,
    )


__all__ = [
    "ConfiguredRawSourceEvidenceStore",
    "build_raw_source_evidence_store",
]
