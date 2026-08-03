from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from threading import RLock
from types import MappingProxyType
from typing import Any, Protocol
from uuid import UUID, uuid4

from kefe_api.modules.knowledge.public_feed_activation import (
    PublicFeedActivationDefinition,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

MANIFEST_SCHEMA_VERSION = "kefe.public-feed-activation-manifest/1.0.0"
MAX_MANIFEST_BYTES = 131_072
MAX_CATALOG_PAGE_SIZE = 100

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_EVIDENCE_REF = re.compile(r"^(?:docref|evidence)://[A-Za-z0-9._/@:+-]+$")
_ADMIN_ACTOR = re.compile(r"^admin:[0-9a-f-]{36}$")
_SENSITIVE_KEY_TOKENS = (
    "authorization",
    "cookie",
    "password",
    "private_key",
    "client_secret",
    "access_token",
    "refresh_token",
)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def canonical_manifest_json(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise ValueError("activation manifest payload must be an exact dict")
    _validate_manifest_value(payload, path="manifest")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    if len(encoded.encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise ValueError("activation manifest exceeds the byte budget")
    return encoded


def canonical_manifest_hash(manifest_json: str) -> str:
    if not manifest_json or manifest_json != manifest_json.strip():
        raise ValueError("manifest_json must be exact nonblank text")
    try:
        payload = json.loads(manifest_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("manifest_json is invalid") from exc
    if type(payload) is not dict:
        raise ValueError("manifest_json must contain an object")
    if canonical_manifest_json(payload) != manifest_json:
        raise ValueError("manifest_json must use canonical JSON encoding")
    return f"sha256:{sha256(manifest_json.encode('utf-8')).hexdigest()}"


def _validate_manifest_value(value: Any, *, path: str) -> None:
    if value is None or type(value) in {bool, int, str}:
        if type(value) is str and len(value) > 16_384:
            raise ValueError(f"activation manifest string is too long at {path}")
        return
    if type(value) is float:
        if value != value or value in {float("inf"), float("-inf")}:
            raise ValueError(f"activation manifest number is invalid at {path}")
        return
    if type(value) is list or type(value) is tuple:
        if len(value) > 4096:
            raise ValueError(f"activation manifest list is too large at {path}")
        for index, item in enumerate(value):
            _validate_manifest_value(item, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        if len(value) > 4096:
            raise ValueError(f"activation manifest object is too large at {path}")
        for key, item in value.items():
            if type(key) is not str or not key or key != key.strip():
                raise ValueError(f"activation manifest key is invalid at {path}")
            lowered = key.lower()
            if any(token in lowered for token in _SENSITIVE_KEY_TOKENS):
                raise ValueError(f"sensitive activation manifest field is forbidden at {path}")
            if lowered == "secret_ref" and item is not None:
                raise ValueError("activation manifest cannot contain a secret reference")
            if lowered in {"object_key", "backend_object_key"}:
                raise ValueError("activation manifest cannot contain backend object keys")
            _validate_manifest_value(item, path=f"{path}.{key}")
        return
    raise ValueError(f"activation manifest type is invalid at {path}")


@dataclass(frozen=True, slots=True, repr=False)
class PublicFeedActivationCatalogEntry:
    id: UUID
    activation_code: str
    adapter_code: str
    configuration_hash: str
    manifest_schema_version: str
    manifest_json: str
    evidence_ref: str
    recorded_by: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if type(self.id) is not UUID:
            raise ValueError("catalog id must be exact UUID")
        require_versioned_adapter_code(self.activation_code)
        require_versioned_adapter_code(self.adapter_code)
        if _SHA256.fullmatch(self.configuration_hash) is None:
            raise ValueError("configuration_hash must be canonical SHA-256")
        if self.manifest_schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError("manifest schema version is unsupported")
        if canonical_manifest_hash(self.manifest_json) != self.configuration_hash:
            raise ValueError("manifest hash does not match configuration_hash")
        if _EVIDENCE_REF.fullmatch(self.evidence_ref) is None:
            raise ValueError("evidence_ref must be opaque")
        if _ADMIN_ACTOR.fullmatch(self.recorded_by) is None:
            raise ValueError("recorded_by must be an Admin actor reference")
        _require_utc(self.recorded_at, "recorded_at")

    @classmethod
    def from_definition(
        cls,
        definition: PublicFeedActivationDefinition,
        *,
        evidence_ref: str,
        recorded_by: str,
        recorded_at: datetime,
        entry_id: UUID | None = None,
    ) -> PublicFeedActivationCatalogEntry:
        if type(definition) is not PublicFeedActivationDefinition:
            raise ValueError("definition must be exact PublicFeedActivationDefinition")
        manifest_json = canonical_manifest_json(definition.configuration_payload)
        if canonical_manifest_hash(manifest_json) != definition.configuration_hash:
            raise ValueError("activation definition configuration hash drifted")
        return cls(
            id=entry_id or uuid4(),
            activation_code=definition.activation_code,
            adapter_code=definition.adapter_code,
            configuration_hash=definition.configuration_hash,
            manifest_schema_version=MANIFEST_SCHEMA_VERSION,
            manifest_json=manifest_json,
            evidence_ref=evidence_ref,
            recorded_by=recorded_by,
            recorded_at=recorded_at,
        )

    @property
    def catalog_content_identity(self) -> tuple[object, ...]:
        return (
            self.activation_code,
            self.adapter_code,
            self.configuration_hash,
            self.manifest_schema_version,
            self.manifest_json,
            self.evidence_ref,
        )

    def manifest_payload(self) -> dict[str, Any]:
        payload = json.loads(self.manifest_json)
        if type(payload) is not dict:
            raise ValueError("stored activation manifest is invalid")
        if canonical_manifest_hash(self.manifest_json) != self.configuration_hash:
            raise ValueError("stored activation manifest integrity failed")
        return payload

    def __repr__(self) -> str:
        return (
            "PublicFeedActivationCatalogEntry("
            f"id={self.id!r}, activation_code={self.activation_code!r}, "
            f"adapter_code={self.adapter_code!r}, "
            f"configuration_hash={self.configuration_hash!r}, "
            f"manifest_json=<redacted:{len(self.manifest_json)} chars>, "
            "evidence_ref=<redacted>, "
            f"recorded_by={self.recorded_by!r}, recorded_at={self.recorded_at!r})"
        )


class PublicFeedActivationCatalogRepository(Protocol):
    def create_or_get(
        self,
        entry: PublicFeedActivationCatalogEntry,
    ) -> PublicFeedActivationCatalogEntry: ...

    def get_by_activation_code(
        self,
        activation_code: str,
    ) -> PublicFeedActivationCatalogEntry | None: ...

    def get_by_adapter_code(
        self,
        adapter_code: str,
    ) -> PublicFeedActivationCatalogEntry | None: ...

    def list_entries(
        self,
        *,
        limit: int,
        after_activation_code: str | None = None,
    ) -> tuple[PublicFeedActivationCatalogEntry, ...]: ...


class InMemoryPublicFeedActivationCatalogRepository:
    def __init__(
        self,
        entries: tuple[PublicFeedActivationCatalogEntry, ...] = (),
    ) -> None:
        self._lock = RLock()
        self._by_activation: dict[str, PublicFeedActivationCatalogEntry] = {}
        self._by_adapter: dict[str, PublicFeedActivationCatalogEntry] = {}
        self._by_hash: dict[str, PublicFeedActivationCatalogEntry] = {}
        for entry in entries:
            self.create_or_get(entry)

    def create_or_get(
        self,
        entry: PublicFeedActivationCatalogEntry,
    ) -> PublicFeedActivationCatalogEntry:
        if type(entry) is not PublicFeedActivationCatalogEntry:
            raise ValueError("catalog entry must be exact PublicFeedActivationCatalogEntry")
        entry.manifest_payload()
        with self._lock:
            existing = self._by_activation.get(entry.activation_code)
            if existing is not None:
                if existing.catalog_content_identity == entry.catalog_content_identity:
                    return existing
                raise ValueError("conflicting public feed activation catalog entry")
            if entry.adapter_code in self._by_adapter:
                raise ValueError("public feed adapter is already cataloged")
            if entry.configuration_hash in self._by_hash:
                raise ValueError("public feed configuration hash is already cataloged")
            self._by_activation[entry.activation_code] = entry
            self._by_adapter[entry.adapter_code] = entry
            self._by_hash[entry.configuration_hash] = entry
            return entry

    def get_by_activation_code(
        self,
        activation_code: str,
    ) -> PublicFeedActivationCatalogEntry | None:
        require_versioned_adapter_code(activation_code)
        with self._lock:
            entry = self._by_activation.get(activation_code)
        if entry is not None:
            entry.manifest_payload()
        return entry

    def get_by_adapter_code(
        self,
        adapter_code: str,
    ) -> PublicFeedActivationCatalogEntry | None:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            entry = self._by_adapter.get(adapter_code)
        if entry is not None:
            entry.manifest_payload()
        return entry

    def list_entries(
        self,
        *,
        limit: int,
        after_activation_code: str | None = None,
    ) -> tuple[PublicFeedActivationCatalogEntry, ...]:
        if not 1 <= limit <= MAX_CATALOG_PAGE_SIZE:
            raise ValueError("catalog list limit is outside the supported range")
        if after_activation_code is not None:
            require_versioned_adapter_code(after_activation_code)
        with self._lock:
            ordered = tuple(
                self._by_activation[key]
                for key in sorted(self._by_activation)
                if after_activation_code is None or key > after_activation_code
            )[:limit]
        for entry in ordered:
            entry.manifest_payload()
        return ordered

    @property
    def immutable_snapshot(self) -> MappingProxyType:
        with self._lock:
            return MappingProxyType(dict(self._by_activation))


__all__ = [
    "InMemoryPublicFeedActivationCatalogRepository",
    "MANIFEST_SCHEMA_VERSION",
    "MAX_CATALOG_PAGE_SIZE",
    "MAX_MANIFEST_BYTES",
    "PublicFeedActivationCatalogEntry",
    "PublicFeedActivationCatalogRepository",
    "canonical_manifest_hash",
    "canonical_manifest_json",
]
