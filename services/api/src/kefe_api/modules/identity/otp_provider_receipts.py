from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from typing import Protocol
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import Settings
from kefe_api.modules.identity.otp_secret_resolution import (
    default_otp_secret_resolver_registry,
)
from kefe_api.modules.knowledge.provider_control import require_secret_reference
from kefe_api.modules.knowledge.provider_secret_execution import (
    SecretLease,
    SecretResolutionFinalError,
    SecretResolutionRetryableError,
    SecretResolverRegistry,
)

OTP_PROVIDER_RECEIPT_ADAPTER_CODE = "otp.receipt.hmac.v1"
OTP_PROVIDER_RECEIPT_SECRET_PERMIT_ID = UUID(
    "23e94215-418a-47c5-b393-98b01dbb2a77"
)
_KEY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_EVENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
_SIGNATURE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^[1-9][0-9]{9,10}$")
_HEX_256 = re.compile(r"^[0-9a-f]{64}$")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


class OtpProviderReceiptOutcome(StrEnum):
    DELIVERED = "DELIVERED"
    UNDELIVERABLE = "UNDELIVERABLE"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class OtpProviderReceiptPolicy:
    maximum_clock_skew: timedelta = timedelta(minutes=5)
    maximum_body_bytes: int = 4_096
    retention: timedelta = timedelta(days=30)

    def __post_init__(self) -> None:
        if not timedelta(seconds=30) <= self.maximum_clock_skew <= timedelta(hours=1):
            raise ValueError("OTP receipt clock skew is outside the supported range")
        if not 256 <= self.maximum_body_bytes <= 65_536:
            raise ValueError("OTP receipt body budget is outside the supported range")
        if not timedelta(days=1) <= self.retention <= timedelta(days=90):
            raise ValueError("OTP receipt retention is outside the supported range")

    @classmethod
    def from_seconds(
        cls,
        *,
        maximum_clock_skew_seconds: int,
        maximum_body_bytes: int,
        retention_seconds: int,
    ) -> OtpProviderReceiptPolicy:
        return cls(
            maximum_clock_skew=timedelta(seconds=maximum_clock_skew_seconds),
            maximum_body_bytes=maximum_body_bytes,
            retention=timedelta(seconds=retention_seconds),
        )


@dataclass(frozen=True, slots=True)
class OtpProviderReceipt:
    provider_event_ref: str
    delivery_ref: str
    outcome: OtpProviderReceiptOutcome
    occurred_at: datetime
    received_at: datetime

    def __post_init__(self) -> None:
        if _HEX_256.fullmatch(self.provider_event_ref) is None:
            raise ValueError("OTP receipt provider_event_ref is invalid")
        if _HEX_256.fullmatch(self.delivery_ref) is None:
            raise ValueError("OTP receipt delivery_ref is invalid")
        _require_utc(self.occurred_at, "occurred_at")
        _require_utc(self.received_at, "received_at")


@dataclass(frozen=True, slots=True)
class OtpProviderReceiptAppendResult:
    receipt: OtpProviderReceipt
    duplicate: bool


@dataclass(frozen=True, slots=True)
class OtpProviderReceiptFacts:
    as_of: datetime
    window_started_at: datetime
    total_count: int
    delivered_count: int
    undeliverable_count: int
    expired_count: int
    latest_received_at: datetime | None

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        _require_utc(self.window_started_at, "window_started_at")
        if self.window_started_at > self.as_of:
            raise ValueError("OTP receipt facts window is invalid")
        counts = (
            self.total_count,
            self.delivered_count,
            self.undeliverable_count,
            self.expired_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("OTP receipt counts must be non-negative")
        if sum(counts[1:]) != self.total_count:
            raise ValueError("OTP receipt outcome counts must equal total_count")
        if self.latest_received_at is not None:
            _require_utc(self.latest_received_at, "latest_received_at")


class OtpProviderReceiptConflict(Exception):
    pass


class OtpProviderReceiptRepository(Protocol):
    def append_and_prune(
        self,
        receipt: OtpProviderReceipt,
        *,
        prune_before: datetime,
    ) -> OtpProviderReceiptAppendResult: ...

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpProviderReceiptFacts: ...


class InMemoryOtpProviderReceiptRepository:
    def __init__(self) -> None:
        self._receipts: dict[str, OtpProviderReceipt] = {}
        self._lock = RLock()

    def append_and_prune(
        self,
        receipt: OtpProviderReceipt,
        *,
        prune_before: datetime,
    ) -> OtpProviderReceiptAppendResult:
        _require_utc(prune_before, "prune_before")
        with self._lock:
            self._receipts = {
                event_ref: current
                for event_ref, current in self._receipts.items()
                if current.received_at >= prune_before
            }
            existing = self._receipts.get(receipt.provider_event_ref)
            if existing is not None:
                if _same_receipt_facts(existing, receipt):
                    return OtpProviderReceiptAppendResult(existing, duplicate=True)
                raise OtpProviderReceiptConflict()
            self._receipts[receipt.provider_event_ref] = receipt
            return OtpProviderReceiptAppendResult(receipt, duplicate=False)

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpProviderReceiptFacts:
        _require_utc(window_started_at, "window_started_at")
        _require_utc(as_of, "as_of")
        _require_utc(prune_before, "prune_before")
        with self._lock:
            self._receipts = {
                event_ref: current
                for event_ref, current in self._receipts.items()
                if current.received_at >= prune_before
            }
            receipts = tuple(
                current
                for current in self._receipts.values()
                if window_started_at <= current.received_at <= as_of
            )
        return _facts_from_receipts(
            receipts,
            window_started_at=window_started_at,
            as_of=as_of,
        )


class OtpProviderReceiptSecretLeaseResolver(Protocol):
    def resolve(self, *, key_id: str, at: datetime) -> SecretLease: ...


class RegistryBackedOtpProviderReceiptSecretLeaseResolver:
    __slots__ = ("_registry", "_secret_refs", "_lease_ttl_seconds")

    def __init__(
        self,
        *,
        registry: SecretResolverRegistry,
        secret_refs: dict[str, str],
        lease_ttl_seconds: int,
    ) -> None:
        if not secret_refs:
            raise ValueError("OTP receipt secret-reference map must not be empty")
        validated: dict[str, str] = {}
        for key_id, secret_ref in secret_refs.items():
            if _KEY_ID.fullmatch(key_id) is None:
                raise ValueError("OTP receipt key id is invalid")
            require_secret_reference(secret_ref)
            validated[key_id] = secret_ref
        if not 1 <= lease_ttl_seconds <= 300:
            raise ValueError("OTP receipt secret lease TTL is outside the supported range")
        self._registry = registry
        self._secret_refs = validated
        self._lease_ttl_seconds = lease_ttl_seconds

    def resolve(self, *, key_id: str, at: datetime) -> SecretLease:
        _require_utc(at, "at")
        secret_ref = self._secret_refs.get(key_id)
        if secret_ref is None:
            raise SecretResolutionFinalError()
        try:
            resolver = self._registry.get_for_reference(secret_ref)
        except KeyError as exc:
            raise SecretResolutionFinalError() from exc
        return resolver.resolve(
            secret_ref=secret_ref,
            adapter_code=OTP_PROVIDER_RECEIPT_ADAPTER_CODE,
            permit_id=OTP_PROVIDER_RECEIPT_SECRET_PERMIT_ID,
            at=at,
            expires_at=at + timedelta(seconds=self._lease_ttl_seconds),
        )

    def __repr__(self) -> str:
        return (
            "RegistryBackedOtpProviderReceiptSecretLeaseResolver("
            "registry=<redacted>, secret_refs=<redacted>, "
            f"lease_ttl_seconds={self._lease_ttl_seconds})"
        )


class OtpProviderReceiptService:
    def __init__(
        self,
        *,
        repository: OtpProviderReceiptRepository,
        secret_resolver: OtpProviderReceiptSecretLeaseResolver | None,
        policy: OtpProviderReceiptPolicy | None = None,
        enabled: bool,
    ) -> None:
        if enabled and secret_resolver is None:
            raise ValueError("enabled OTP receipt service requires a secret resolver")
        self._repository = repository
        self._secret_resolver = secret_resolver
        self._policy = policy or OtpProviderReceiptPolicy()
        self._enabled = enabled

    @property
    def policy(self) -> OtpProviderReceiptPolicy:
        return self._policy

    def receive(
        self,
        *,
        raw_body: bytes,
        timestamp: str,
        key_id: str,
        provider_event_id: str,
        signature: str,
        delivery_id: UUID,
        outcome: OtpProviderReceiptOutcome,
        occurred_at: datetime,
        received_at: datetime | None = None,
    ) -> OtpProviderReceiptAppendResult:
        now = received_at or datetime.now(UTC)
        _require_utc(now, "received_at")
        if not self._enabled or self._secret_resolver is None:
            raise DomainError(
                "AUTH_OTP_RECEIPT_DISABLED",
                "OTP provider receipts are not configured",
                404,
                retryable=False,
            )
        if not raw_body or len(raw_body) > self._policy.maximum_body_bytes:
            raise self._rejected_error()
        if _KEY_ID.fullmatch(key_id) is None:
            raise self._rejected_error()
        if _EVENT_ID.fullmatch(provider_event_id) is None:
            raise self._rejected_error()
        if _SIGNATURE.fullmatch(signature) is None:
            raise self._rejected_error()
        if _TIMESTAMP.fullmatch(timestamp) is None:
            raise self._rejected_error()

        issued_at = datetime.fromtimestamp(int(timestamp), tz=UTC)
        if abs(now - issued_at) > self._policy.maximum_clock_skew:
            raise self._rejected_error()
        _require_utc(occurred_at, "occurred_at")
        if occurred_at > now + self._policy.maximum_clock_skew:
            raise self._rejected_error()
        if occurred_at < now - self._policy.retention:
            raise self._rejected_error()
        if delivery_id.version != 4:
            raise self._rejected_error()

        canonical = (
            b"v1\n"
            + timestamp.encode("ascii")
            + b"\n"
            + key_id.encode("ascii")
            + b"\n"
            + provider_event_id.encode("ascii")
            + b"\n"
            + raw_body
        )
        try:
            lease = self._secret_resolver.resolve(key_id=key_id, at=now)
        except SecretResolutionRetryableError as exc:
            raise DomainError(
                "AUTH_OTP_RECEIPT_AUTH_UNAVAILABLE",
                "OTP receipt authentication is temporarily unavailable",
                503,
                retryable=True,
            ) from exc
        except (SecretResolutionFinalError, KeyError, ValueError) as exc:
            raise self._rejected_error() from exc
        except Exception as exc:
            raise self._rejected_error() from exc

        try:
            verified = lease.use_bytes(
                lambda secret: _verify_signature(
                    secret=secret,
                    canonical=canonical,
                    signature=signature,
                ),
                at=now,
            )
        except (RuntimeError, ValueError) as exc:
            raise self._rejected_error() from exc
        finally:
            lease.close()
        if not verified:
            raise self._rejected_error()

        receipt = OtpProviderReceipt(
            provider_event_ref=hashlib.sha256(
                provider_event_id.encode("ascii")
            ).hexdigest(),
            delivery_ref=hashlib.sha256(
                str(delivery_id).lower().encode("ascii")
            ).hexdigest(),
            outcome=outcome,
            occurred_at=occurred_at,
            received_at=now,
        )
        try:
            return self._repository.append_and_prune(
                receipt,
                prune_before=now - self._policy.retention,
            )
        except OtpProviderReceiptConflict as exc:
            raise DomainError(
                "AUTH_OTP_RECEIPT_EVENT_CONFLICT",
                "OTP provider receipt event conflicts with an earlier event",
                409,
                retryable=False,
            ) from exc

    def facts(
        self,
        *,
        window: timedelta = timedelta(days=1),
        as_of: datetime | None = None,
    ) -> OtpProviderReceiptFacts:
        if window < timedelta(minutes=1) or window > self._policy.retention:
            raise ValueError("OTP receipt facts window is outside the supported range")
        now = as_of or datetime.now(UTC)
        _require_utc(now, "as_of")
        return self._repository.read_facts(
            window_started_at=now - window,
            as_of=now,
            prune_before=now - self._policy.retention,
        )

    @staticmethod
    def _rejected_error() -> DomainError:
        return DomainError(
            "AUTH_OTP_RECEIPT_REJECTED",
            "OTP provider receipt authentication failed",
            401,
            retryable=False,
        )

    def __repr__(self) -> str:
        return (
            "OtpProviderReceiptService("
            "repository=<redacted>, secret_resolver=<redacted>, "
            f"policy={self._policy!r}, enabled={self._enabled!r})"
        )


def build_otp_provider_receipt_service(
    settings: Settings,
    *,
    repository: OtpProviderReceiptRepository,
    secret_resolver_registry: SecretResolverRegistry | None = None,
) -> OtpProviderReceiptService:
    enabled = settings.otp_receipt_mode == "HMAC_SHA256"
    resolver: OtpProviderReceiptSecretLeaseResolver | None = None
    if enabled:
        resolver = RegistryBackedOtpProviderReceiptSecretLeaseResolver(
            registry=secret_resolver_registry
            or default_otp_secret_resolver_registry(),
            secret_refs=settings.otp_receipt_secret_refs,
            lease_ttl_seconds=settings.otp_receipt_secret_lease_seconds,
        )
    return OtpProviderReceiptService(
        repository=repository,
        secret_resolver=resolver,
        policy=OtpProviderReceiptPolicy.from_seconds(
            maximum_clock_skew_seconds=settings.otp_receipt_max_skew_seconds,
            maximum_body_bytes=settings.otp_receipt_max_body_bytes,
            retention_seconds=settings.otp_receipt_retention_seconds,
        ),
        enabled=enabled,
    )


def _verify_signature(
    *,
    secret: memoryview,
    canonical: bytes,
    signature: str,
) -> bool:
    if len(secret) < 32:
        raise ValueError("OTP receipt secret must contain at least 32 bytes")
    expected = hmac.new(bytes(secret), canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _same_receipt_facts(
    left: OtpProviderReceipt,
    right: OtpProviderReceipt,
) -> bool:
    return (
        left.delivery_ref == right.delivery_ref
        and left.outcome is right.outcome
        and left.occurred_at == right.occurred_at
    )


def _facts_from_receipts(
    receipts: tuple[OtpProviderReceipt, ...],
    *,
    window_started_at: datetime,
    as_of: datetime,
) -> OtpProviderReceiptFacts:
    return OtpProviderReceiptFacts(
        as_of=as_of,
        window_started_at=window_started_at,
        total_count=len(receipts),
        delivered_count=sum(
            receipt.outcome is OtpProviderReceiptOutcome.DELIVERED
            for receipt in receipts
        ),
        undeliverable_count=sum(
            receipt.outcome is OtpProviderReceiptOutcome.UNDELIVERABLE
            for receipt in receipts
        ),
        expired_count=sum(
            receipt.outcome is OtpProviderReceiptOutcome.EXPIRED
            for receipt in receipts
        ),
        latest_received_at=max(
            (receipt.received_at for receipt in receipts),
            default=None,
        ),
    )


__all__ = [
    "InMemoryOtpProviderReceiptRepository",
    "OTP_PROVIDER_RECEIPT_ADAPTER_CODE",
    "OTP_PROVIDER_RECEIPT_SECRET_PERMIT_ID",
    "OtpProviderReceipt",
    "OtpProviderReceiptAppendResult",
    "OtpProviderReceiptConflict",
    "OtpProviderReceiptFacts",
    "OtpProviderReceiptOutcome",
    "OtpProviderReceiptPolicy",
    "OtpProviderReceiptRepository",
    "OtpProviderReceiptService",
    "RegistryBackedOtpProviderReceiptSecretLeaseResolver",
    "build_otp_provider_receipt_service",
]
