from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from threading import Lock
from typing import Protocol

from kefe_api.modules.knowledge.provider_http_transport import MAX_RESPONSE_BYTES
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

_SHA256_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_STORAGE_REF = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
_MEDIA_TYPE = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$"
)
_ERROR_CODE = re.compile(r"^RAW_EVIDENCE_[A-Z0-9_]{1,80}$")

MAX_EVIDENCE_BYTES = MAX_RESPONSE_BYTES


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _normalize_media_type(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized != value or _MEDIA_TYPE.fullmatch(normalized) is None:
        raise ValueError("media_type must be an exact lowercase media type")
    return normalized


def canonical_content_hash(body: bytes) -> str:
    if type(body) is not bytes:
        raise ValueError("raw evidence body must be exact bytes")
    if len(body) > MAX_EVIDENCE_BYTES:
        raise ValueError("raw evidence body exceeds the supported byte budget")
    return f"sha256:{sha256(body).hexdigest()}"


def canonical_storage_ref(content_hash: str) -> str:
    if _SHA256_HASH.fullmatch(content_hash) is None:
        raise ValueError("content_hash must be canonical SHA-256")
    return f"evidence://sha256/{content_hash.removeprefix('sha256:')}"


@dataclass(frozen=True, slots=True, repr=False)
class RawSourceEvidenceSeal:
    content_hash: str
    storage_ref: str
    byte_length: int
    media_type: str | None
    sealed_at: datetime

    def __post_init__(self) -> None:
        if _SHA256_HASH.fullmatch(self.content_hash) is None:
            raise ValueError("content_hash must be canonical SHA-256")
        if _STORAGE_REF.fullmatch(self.storage_ref) is None:
            raise ValueError("storage_ref must be canonical evidence reference")
        if self.storage_ref != canonical_storage_ref(self.content_hash):
            raise ValueError("storage_ref must derive from content_hash")
        if not 0 <= self.byte_length <= MAX_EVIDENCE_BYTES:
            raise ValueError("byte_length exceeds the supported evidence budget")
        normalized_media_type = _normalize_media_type(self.media_type)
        if normalized_media_type != self.media_type:
            raise ValueError("media_type must be canonical")
        _require_utc(self.sealed_at, "sealed_at")

    def __repr__(self) -> str:
        return (
            "RawSourceEvidenceSeal("
            f"content_hash={self.content_hash!r}, storage_ref=<redacted>, "
            f"byte_length={self.byte_length}, media_type={self.media_type!r}, "
            f"sealed_at={self.sealed_at!r})"
        )


class RawSourceEvidenceError(Exception):
    def __init__(self, code: str) -> None:
        if _ERROR_CODE.fullmatch(code) is None:
            raise ValueError("raw evidence error code is invalid")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r})"


class RetryableRawSourceEvidenceError(RawSourceEvidenceError):
    pass


class FinalRawSourceEvidenceError(RawSourceEvidenceError):
    pass


class RawSourceEvidenceStore(Protocol):
    def seal(
        self,
        *,
        adapter_code: str,
        body: bytes,
        media_type: str | None,
        sealed_at: datetime,
    ) -> RawSourceEvidenceSeal: ...


class InMemoryRawSourceEvidenceStore:
    def __init__(self) -> None:
        self._bodies: dict[str, bytes] = {}
        self._lock = Lock()

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
        normalized_media_type = _normalize_media_type(media_type)
        content_hash = canonical_content_hash(body)
        storage_ref = canonical_storage_ref(content_hash)
        owned_body = memoryview(body).tobytes()
        with self._lock:
            existing = self._bodies.get(content_hash)
            if existing is not None and existing != owned_body:
                raise FinalRawSourceEvidenceError(
                    "RAW_EVIDENCE_DIGEST_COLLISION"
                )
            if existing is None:
                self._bodies[content_hash] = owned_body
        return RawSourceEvidenceSeal(
            content_hash=content_hash,
            storage_ref=storage_ref,
            byte_length=len(owned_body),
            media_type=normalized_media_type,
            sealed_at=sealed_at,
        )

    def read_owned_copy(self, storage_ref: str) -> bytes:
        if _STORAGE_REF.fullmatch(storage_ref) is None:
            raise ValueError("storage_ref must be canonical evidence reference")
        content_hash = f"sha256:{storage_ref.rsplit('/', 1)[-1]}"
        with self._lock:
            try:
                stored = self._bodies[content_hash]
            except KeyError as exc:
                raise KeyError(storage_ref) from exc
            return memoryview(stored).tobytes()

    @property
    def object_count(self) -> int:
        with self._lock:
            return len(self._bodies)


class UnconfiguredRawSourceEvidenceStore:
    def seal(
        self,
        *,
        adapter_code: str,
        body: bytes,
        media_type: str | None,
        sealed_at: datetime,
    ) -> RawSourceEvidenceSeal:
        del adapter_code, body, media_type, sealed_at
        raise RetryableRawSourceEvidenceError(
            "RAW_EVIDENCE_STORE_UNAVAILABLE"
        )


__all__ = [
    "FinalRawSourceEvidenceError",
    "InMemoryRawSourceEvidenceStore",
    "MAX_EVIDENCE_BYTES",
    "RawSourceEvidenceError",
    "RawSourceEvidenceSeal",
    "RawSourceEvidenceStore",
    "RetryableRawSourceEvidenceError",
    "UnconfiguredRawSourceEvidenceStore",
    "canonical_content_hash",
    "canonical_storage_ref",
]
