from __future__ import annotations

from threading import RLock

from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    PublicFeedRuntimeProfile,
    PublicFeedRuntimeProfileRegistry,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ProviderAdoptionProfile,
    ProviderAdoptionRegistry,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    PublicSourceCaptureAdapter,
    PublicSourceCaptureRegistry,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code


class MutableProviderAdoptionRegistry(ProviderAdoptionRegistry):
    def __init__(self) -> None:
        self._lock = RLock()
        self._profiles: dict[str, ProviderAdoptionProfile] = {}

    def register_or_get(
        self,
        profile: ProviderAdoptionProfile,
    ) -> ProviderAdoptionProfile:
        with self._lock:
            existing = self._profiles.get(profile.adapter_code)
            if existing is None:
                self._profiles[profile.adapter_code] = profile
                return profile
            if existing.immutable_configuration != profile.immutable_configuration:
                raise ValueError("conflicting provider adoption profile")
            return existing

    def get(self, adapter_code: str) -> ProviderAdoptionProfile:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            try:
                return self._profiles[adapter_code]
            except KeyError as exc:
                raise KeyError(adapter_code) from exc

    def adapter_codes(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._profiles))


class MutablePublicSourceCaptureRegistry(PublicSourceCaptureRegistry):
    def __init__(self) -> None:
        self._lock = RLock()
        self._adapters: dict[str, PublicSourceCaptureAdapter] = {}

    def register_or_get(
        self,
        adapter: PublicSourceCaptureAdapter,
    ) -> PublicSourceCaptureAdapter:
        require_versioned_adapter_code(adapter.adapter_code)
        with self._lock:
            existing = self._adapters.get(adapter.adapter_code)
            if existing is None:
                self._adapters[adapter.adapter_code] = adapter
                return adapter
            if type(existing) is not type(adapter):
                raise ValueError("conflicting public source capture adapter")
            return existing

    def get(self, adapter_code: str) -> PublicSourceCaptureAdapter:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            try:
                return self._adapters[adapter_code]
            except KeyError as exc:
                raise KeyError("SOURCE_PUBLIC_ADAPTER_NOT_REGISTERED") from exc

    def adapter_codes(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._adapters))


class CanonicalPublicFeedRuntimeProfileRegistry(PublicFeedRuntimeProfileRegistry):
    def __init__(
        self,
        *,
        adoption: MutableProviderAdoptionRegistry,
        capture: MutablePublicSourceCaptureRegistry,
        adapter_factory: EvidenceBackedPublicHttpCaptureAdapterFactory,
    ) -> None:
        self._lock = RLock()
        self._adoption = adoption
        self._capture = capture
        self._adapter_factory = adapter_factory
        self._profiles: dict[str, PublicFeedRuntimeProfile] = {}

    def register_or_get(
        self,
        profile: PublicFeedRuntimeProfile,
    ) -> PublicFeedRuntimeProfile:
        adapter_code = profile.adoption_profile.adapter_code
        if profile.capture_definition.adapter_code != adapter_code:
            raise ValueError("public feed runtime adapter identity mismatch")
        if profile.acquisition_command.adapter_code != adapter_code:
            raise ValueError("public feed acquisition adapter identity mismatch")

        with self._lock:
            existing = self._profiles.get(adapter_code)
            if existing is not None:
                if existing != profile:
                    raise ValueError(
                        "public feed runtime profile conflicts with existing adapter"
                    )
                return existing

            self._adoption.register_or_get(profile.adoption_profile)
            adapter = self._adapter_factory.create(profile.capture_definition)
            self._capture.register_or_get(adapter)
            self._profiles[adapter_code] = profile
            return profile

    def get(self, adapter_code: str) -> PublicFeedRuntimeProfile | None:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            return self._profiles.get(adapter_code)

    def adapter_codes(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._profiles))


__all__ = [
    "CanonicalPublicFeedRuntimeProfileRegistry",
    "MutableProviderAdoptionRegistry",
    "MutablePublicSourceCaptureRegistry",
]
