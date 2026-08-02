from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.lease_ports import (
    IngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLease,
    IngestionRunLeaseClaim,
    IngestionRunLeaseReleaseDisposition,
)
from kefe_api.modules.ingestion_orchestration.models import require_text, utcnow

MINIMUM_LEASE_TTL_SECONDS = 5
MAXIMUM_LEASE_TTL_SECONDS = 900
MAXIMUM_RECOVERY_BATCH = 1000


@dataclass(frozen=True, slots=True)
class IngestionRunLeaseError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return self.message


class IngestionRunLeaseService:
    def __init__(self, repository: IngestionRunLeaseRepository) -> None:
        self._repository = repository

    def claim_next(
        self,
        *,
        worker_ref: str,
        ttl_seconds: int,
        pipeline_code: str | None = None,
        pipeline_version: str | None = None,
        now=None,
    ) -> IngestionRunLeaseClaim | None:
        self._validate_worker_ref(worker_ref)
        self._validate_ttl(ttl_seconds)
        if pipeline_code is not None:
            require_text(pipeline_code, "pipeline_code")
        if pipeline_version is not None:
            require_text(pipeline_version, "pipeline_version")
        if (pipeline_code is None) != (pipeline_version is None):
            raise ValueError(
                "pipeline_code and pipeline_version must be provided together"
            )
        claimed_at = now or utcnow()
        return self._repository.claim_next(
            worker_ref=worker_ref,
            claimed_at=claimed_at,
            expires_at=claimed_at + timedelta(seconds=ttl_seconds),
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
        )

    def heartbeat(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        ttl_seconds: int,
        now=None,
    ) -> IngestionRunLease:
        self._validate_worker_ref(worker_ref)
        self._validate_ttl(ttl_seconds)
        heartbeat_at = now or utcnow()
        try:
            return self._repository.heartbeat(
                lease_id=lease_id,
                worker_ref=worker_ref,
                heartbeat_at=heartbeat_at,
                expires_at=heartbeat_at + timedelta(seconds=ttl_seconds),
            )
        except KeyError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_NOT_FOUND",
                "Ingestion run lease was not found",
            ) from exc
        except ValueError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_NOT_ACTIVE",
                "Ingestion run lease is not active for this worker",
            ) from exc

    def assert_active(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        now=None,
    ) -> IngestionRunLease:
        self._validate_worker_ref(worker_ref)
        try:
            return self._repository.assert_active(
                lease_id=lease_id,
                worker_ref=worker_ref,
                at=now or utcnow(),
            )
        except KeyError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_NOT_FOUND",
                "Ingestion run lease was not found",
            ) from exc
        except ValueError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_NOT_ACTIVE",
                "Ingestion run lease is not active for this worker",
            ) from exc

    def release(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        disposition: IngestionRunLeaseReleaseDisposition,
        now=None,
    ) -> IngestionRunLease:
        self._validate_worker_ref(worker_ref)
        try:
            return self._repository.release(
                lease_id=lease_id,
                worker_ref=worker_ref,
                released_at=now or utcnow(),
                disposition=disposition,
            )
        except KeyError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_NOT_FOUND",
                "Ingestion run lease was not found",
            ) from exc
        except ValueError as exc:
            raise IngestionRunLeaseError(
                "INGESTION_RUN_LEASE_RELEASE_INVALID",
                "Ingestion run lease release is invalid for its owner or run state",
            ) from exc

    def recover_expired(
        self,
        *,
        limit: int = 100,
        now=None,
    ) -> tuple[IngestionRunLease, ...]:
        if limit < 1 or limit > MAXIMUM_RECOVERY_BATCH:
            raise ValueError(
                f"recovery limit must be between 1 and {MAXIMUM_RECOVERY_BATCH}"
            )
        return self._repository.recover_expired(at=now or utcnow(), limit=limit)

    @staticmethod
    def _validate_worker_ref(worker_ref: str) -> None:
        require_text(worker_ref, "worker_ref")

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if ttl_seconds < MINIMUM_LEASE_TTL_SECONDS:
            raise ValueError(
                f"lease TTL must be >= {MINIMUM_LEASE_TTL_SECONDS} seconds"
            )
        if ttl_seconds > MAXIMUM_LEASE_TTL_SECONDS:
            raise ValueError(
                f"lease TTL must be <= {MAXIMUM_LEASE_TTL_SECONDS} seconds"
            )
