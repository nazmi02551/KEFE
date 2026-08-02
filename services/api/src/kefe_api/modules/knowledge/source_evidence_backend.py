from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from kefe_api.modules.knowledge.source_evidence import (
    MAX_EVIDENCE_BYTES,
    FinalRawSourceEvidenceError,
    RawSourceEvidenceRead,
    RawSourceEvidenceSeal,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
    canonical_storage_ref,
    content_hash_from_storage_ref,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

_NAMESPACE = re.compile(r"^[a-z0-9][a-z0-9/_-]{0,127}$")
_MEDIA_TYPE = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$"
)
_EVIDENCE_REFERENCE = re.compile(r"^(?:docref|evidence)://[A-Za-z0-9._/@:+-]+$")
_BACKEND_ERROR_CODE = re.compile(r"^RAW_EVIDENCE_BACKEND_[A-Z0-9_]{1,64}$")

MIN_BACKEND_TIMEOUT_MS = 50
MAX_BACKEND_TIMEOUT_MS = 30_000


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _canonical_namespace(value: str) -> str:
    if value != value.strip() or value != value.lower():
        raise ValueError("namespace must be exact lowercase text")
    if _NAMESPACE.fullmatch(value) is None:
        raise ValueError("namespace is invalid")
    if value.endswith("/") or "//" in value:
        raise ValueError("namespace must not contain empty path segments")
    segments = value.split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise ValueError("namespace traversal segments are forbidden")
    return value


def _canonical_media_type(value: str | None) -> str | None:
    if value is None:
        return None
    if value != value.strip() or value != value.lower():
        raise ValueError("media_type must be exact lowercase text")
    if _MEDIA_TYPE.fullmatch(value) is None:
        raise ValueError("media_type is invalid")
    return value


def _require_object_key(value: str) -> None:
    if not value or value != value.strip() or len(value) > 256:
        raise ValueError("object_key is invalid")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise ValueError("object_key must use visible ASCII")


@dataclass(frozen=True, slots=True)
class RawEvidenceBackendProfile:
    profile_code: str
    backend_code: str
    namespace: str
    max_object_bytes: int
    write_timeout_ms: int
    read_timeout_ms: int
    atomic_put_if_absent: bool
    immutable_objects: bool
    read_after_write_verification: bool
    capability_evidence_ref: str

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.profile_code)
        require_versioned_adapter_code(self.backend_code)
        if self.namespace != _canonical_namespace(self.namespace):
            raise ValueError("namespace must be canonical")
        if not 1 <= self.max_object_bytes <= MAX_EVIDENCE_BYTES:
            raise ValueError("max_object_bytes is outside the supported range")
        for value, field_name in (
            (self.write_timeout_ms, "write_timeout_ms"),
            (self.read_timeout_ms, "read_timeout_ms"),
        ):
            if not MIN_BACKEND_TIMEOUT_MS <= value <= MAX_BACKEND_TIMEOUT_MS:
                raise ValueError(f"{field_name} is outside the supported range")
        if self.atomic_put_if_absent is not True:
            raise ValueError("atomic put-if-absent is mandatory")
        if self.immutable_objects is not True:
            raise ValueError("immutable objects are mandatory")
        if self.read_after_write_verification is not True:
            raise ValueError("read-after-write verification is mandatory")
        if _EVIDENCE_REFERENCE.fullmatch(self.capability_evidence_ref) is None:
            raise ValueError("capability_evidence_ref must be opaque")

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.profile_code,
            self.backend_code,
            self.namespace,
            self.max_object_bytes,
            self.write_timeout_ms,
            self.read_timeout_ms,
            self.atomic_put_if_absent,
            self.immutable_objects,
            self.read_after_write_verification,
            self.capability_evidence_ref,
        )


class RawEvidenceBackendProfileRegistry(Protocol):
    def get(self, profile_code: str) -> RawEvidenceBackendProfile: ...


class InMemoryRawEvidenceBackendProfileRegistry:
    def __init__(self, profiles: tuple[RawEvidenceBackendProfile, ...] = ()) -> None:
        registered: dict[str, RawEvidenceBackendProfile] = {}
        for profile in profiles:
            existing = registered.get(profile.profile_code)
            if existing is not None:
                if existing.immutable_configuration != profile.immutable_configuration:
                    raise ValueError("conflicting raw evidence backend profile")
                raise ValueError("duplicate raw evidence backend profile")
            registered[profile.profile_code] = profile
        self._profiles = MappingProxyType(registered)

    def get(self, profile_code: str) -> RawEvidenceBackendProfile:
        require_versioned_adapter_code(profile_code)
        try:
            return self._profiles[profile_code]
        except KeyError as exc:
            raise KeyError(profile_code) from exc


class RawEvidencePutOutcome(StrEnum):
    CREATED = "CREATED"
    ALREADY_EXISTS = "ALREADY_EXISTS"


@dataclass(frozen=True, slots=True, repr=False)
class RawEvidenceWriteResult:
    outcome: RawEvidencePutOutcome
    object_key: str
    byte_length: int

    def __post_init__(self) -> None:
        if type(self.outcome) is not RawEvidencePutOutcome:
            raise ValueError("outcome must be exact RawEvidencePutOutcome")
        _require_object_key(self.object_key)
        if not 0 <= self.byte_length <= MAX_EVIDENCE_BYTES:
            raise ValueError("byte_length is outside the supported range")

    def __repr__(self) -> str:
        return (
            "RawEvidenceWriteResult("
            f"outcome={self.outcome.value!r}, object_key=<redacted>, "
            f"byte_length={self.byte_length})"
        )


@dataclass(frozen=True, slots=True, repr=False)
class RawEvidenceReadResult:
    object_key: str
    body: bytes
    media_type: str | None

    def __post_init__(self) -> None:
        _require_object_key(self.object_key)
        if type(self.body) is not bytes:
            raise ValueError("body must be exact bytes")
        if len(self.body) > MAX_EVIDENCE_BYTES:
            raise ValueError("body exceeds the supported range")
        if self.media_type != _canonical_media_type(self.media_type):
            raise ValueError("media_type must be canonical")

    def __repr__(self) -> str:
        return (
            "RawEvidenceReadResult("
            "object_key=<redacted>, "
            f"body=<redacted:{len(self.body)} bytes>, "
            f"media_type={self.media_type!r})"
        )


class RawEvidenceBackendError(Exception):
    def __init__(self, code: str) -> None:
        if _BACKEND_ERROR_CODE.fullmatch(code) is None:
            raise ValueError("raw evidence backend error code is invalid")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r})"


class RetryableRawEvidenceBackendError(RawEvidenceBackendError):
    pass


class FinalRawEvidenceBackendError(RawEvidenceBackendError):
    pass


class RawEvidenceBackend(Protocol):
    @property
    def backend_code(self) -> str: ...

    def put_if_absent(
        self,
        *,
        object_key: str,
        body: bytes,
        media_type: str | None,
        timeout_ms: int,
    ) -> RawEvidenceWriteResult: ...

    def read_exact(
        self,
        *,
        object_key: str,
        timeout_ms: int,
    ) -> RawEvidenceReadResult: ...


class RawEvidenceBackendRegistry(Protocol):
    def get(self, backend_code: str) -> RawEvidenceBackend: ...


class InMemoryRawEvidenceBackendRegistry:
    def __init__(self, backends: tuple[RawEvidenceBackend, ...] = ()) -> None:
        registered: dict[str, RawEvidenceBackend] = {}
        for backend in backends:
            require_versioned_adapter_code(backend.backend_code)
            if backend.backend_code in registered:
                raise ValueError("duplicate raw evidence backend")
            registered[backend.backend_code] = backend
        self._backends = MappingProxyType(registered)

    def get(self, backend_code: str) -> RawEvidenceBackend:
        require_versioned_adapter_code(backend_code)
        try:
            return self._backends[backend_code]
        except KeyError as exc:
            raise KeyError(backend_code) from exc


class DurableRawSourceEvidenceStore:
    def __init__(
        self,
        *,
        profile: RawEvidenceBackendProfile,
        backend: RawEvidenceBackend,
    ) -> None:
        if backend.backend_code != profile.backend_code:
            raise ValueError("raw evidence backend code mismatch")
        self._profile = profile
        self._backend = backend

    @property
    def profile_code(self) -> str:
        return self._profile.profile_code

    def _object_key(self, content_hash: str) -> str:
        digest = content_hash.removeprefix("sha256:")
        return f"{self._profile.namespace}/sha256/{digest[:2]}/{digest}"

    def seal(
        self,
        *,
        adapter_code: str,
        body: bytes,
        media_type: str | None,
        sealed_at: datetime,
    ) -> RawSourceEvidenceSeal:
        require_versioned_adapter_code(adapter_code)
        _require_utc(sealed_at, "sealed_at")
        canonical_media_type = _canonical_media_type(media_type)
        if type(body) is not bytes:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        if len(body) > self._profile.max_object_bytes:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        owned_body = memoryview(body).tobytes()
        content_hash = canonical_content_hash(owned_body)
        storage_ref = canonical_storage_ref(content_hash)
        object_key = self._object_key(content_hash)

        try:
            write_result = self._backend.put_if_absent(
                object_key=object_key,
                body=owned_body,
                media_type=canonical_media_type,
                timeout_ms=self._profile.write_timeout_ms,
            )
        except RetryableRawEvidenceBackendError as exc:
            raise RetryableRawSourceEvidenceError(exc.code) from exc
        except FinalRawEvidenceBackendError as exc:
            raise FinalRawSourceEvidenceError(exc.code) from exc
        except TimeoutError as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_TIMEOUT"
            ) from exc
        except OSError as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_UNAVAILABLE"
            ) from exc
        except Exception as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_UNAVAILABLE"
            ) from exc

        if type(write_result) is not RawEvidenceWriteResult:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        if (
            write_result.object_key != object_key
            or write_result.byte_length != len(owned_body)
        ):
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )

        read_result = self._read_backend(object_key=object_key)
        if (
            read_result.body != owned_body
            or read_result.media_type != canonical_media_type
        ):
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_READ_AFTER_WRITE_MISMATCH"
            )

        return RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=storage_ref,
            byte_length=len(owned_body),
            media_type=canonical_media_type,
            sealed_at=sealed_at,
        )

    def read(
        self,
        *,
        storage_ref: str,
        expected_content_hash: str,
    ) -> RawSourceEvidenceRead:
        derived_content_hash = content_hash_from_storage_ref(storage_ref)
        if derived_content_hash != expected_content_hash:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_REFERENCE_HASH_MISMATCH"
            )
        object_key = self._object_key(expected_content_hash)
        read_result = self._read_backend(object_key=object_key)
        owned_body = memoryview(read_result.body).tobytes()
        if len(owned_body) > self._profile.max_object_bytes:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        if canonical_content_hash(owned_body) != expected_content_hash:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_READ_DIGEST_MISMATCH"
            )
        return RawSourceEvidenceRead(
            content_hash=expected_content_hash,
            storage_ref=storage_ref,
            body=owned_body,
            media_type=read_result.media_type,
            byte_length=len(owned_body),
        )

    def _read_backend(self, *, object_key: str) -> RawEvidenceReadResult:
        try:
            read_result = self._backend.read_exact(
                object_key=object_key,
                timeout_ms=self._profile.read_timeout_ms,
            )
        except KeyError as exc:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_OBJECT_NOT_FOUND"
            ) from exc
        except RetryableRawEvidenceBackendError as exc:
            raise RetryableRawSourceEvidenceError(exc.code) from exc
        except FinalRawEvidenceBackendError as exc:
            raise FinalRawSourceEvidenceError(exc.code) from exc
        except TimeoutError as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_TIMEOUT"
            ) from exc
        except OSError as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_UNAVAILABLE"
            ) from exc
        except Exception as exc:
            raise RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_UNAVAILABLE"
            ) from exc

        if type(read_result) is not RawEvidenceReadResult:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        if read_result.object_key != object_key:
            raise FinalRawSourceEvidenceError(
                "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID"
            )
        return read_result


__all__ = [
    "DurableRawSourceEvidenceStore",
    "FinalRawEvidenceBackendError",
    "InMemoryRawEvidenceBackendProfileRegistry",
    "InMemoryRawEvidenceBackendRegistry",
    "MAX_BACKEND_TIMEOUT_MS",
    "MIN_BACKEND_TIMEOUT_MS",
    "RawEvidenceBackend",
    "RawEvidenceBackendError",
    "RawEvidenceBackendProfile",
    "RawEvidenceBackendProfileRegistry",
    "RawEvidenceBackendRegistry",
    "RawEvidencePutOutcome",
    "RawEvidenceReadResult",
    "RawEvidenceWriteResult",
    "RetryableRawEvidenceBackendError",
]
