from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.modules.knowledge.source_evidence import (
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

    return DurableRawSourceEvidenceStore(
        profile=profile,
        backend=backend,
    )


__all__ = ["build_raw_source_evidence_store"]
