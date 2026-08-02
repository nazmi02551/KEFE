from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLease,
    IngestionRunLeaseClaim,
    IngestionRunLeaseReleaseDisposition,
)


class IngestionRunLeaseRepository(Protocol):
    def claim_next(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
        pipeline_code: str | None = None,
        pipeline_version: str | None = None,
    ) -> IngestionRunLeaseClaim | None: ...

    def heartbeat(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> IngestionRunLease: ...

    def assert_active(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        at: datetime,
    ) -> IngestionRunLease: ...

    def release(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        released_at: datetime,
        disposition: IngestionRunLeaseReleaseDisposition,
    ) -> IngestionRunLease: ...

    def recover_expired(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[IngestionRunLease, ...]: ...

    def get_lease(self, lease_id: UUID) -> IngestionRunLease | None: ...
