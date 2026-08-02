from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionOutcome,
    ProviderAdmissionResult,
    ProviderCapabilityLifecycle,
    ProviderCapturePermit,
    ProviderCapturePermitState,
    ProviderCircuitState,
    ProviderCredentialMode,
    SourceProviderCapability,
)


class PostgresSourceProviderAdmissionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get(
        self,
        capability: SourceProviderCapability,
    ) -> SourceProviderCapability:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO knowledge.source_provider_capability (
                        adapter_code, credential_mode, secret_ref, lifecycle_state,
                        quota_limit, quota_window_seconds,
                        failure_threshold, circuit_open_seconds,
                        permit_ttl_seconds, window_started_at,
                        window_request_count, consecutive_failure_count,
                        circuit_state, circuit_opened_at,
                        created_at, updated_at
                    ) VALUES (
                        :adapter_code, :credential_mode, :secret_ref, :lifecycle_state,
                        :quota_limit, :quota_window_seconds,
                        :failure_threshold, :circuit_open_seconds,
                        :permit_ttl_seconds, :window_started_at,
                        :window_request_count, :consecutive_failure_count,
                        :circuit_state, :circuit_opened_at,
                        :created_at, :updated_at
                    )
                    ON CONFLICT (adapter_code) DO NOTHING
                    """
                ),
                self._capability_params(capability),
            )
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": capability.adapter_code},
            ).mappings().one()
            stored = self._capability_from_row(row)
            if stored.immutable_configuration != capability.immutable_configuration:
                raise ValueError("provider capability configuration is immutable")
            return stored

    def get(self, adapter_code: str) -> SourceProviderCapability | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            ).mappings().one_or_none()
        return self._capability_from_row(row) if row is not None else None

    def transition_lifecycle(
        self,
        *,
        adapter_code: str,
        target: ProviderCapabilityLifecycle,
        at: datetime,
    ) -> SourceProviderCapability:
        with self._engine.begin() as connection:
            capability = self._lock_capability(connection, adapter_code)
            updated = capability.transition_lifecycle(target, at=at)
            return self._update_capability(connection, updated)

    def admit(
        self,
        *,
        adapter_code: str,
        at: datetime,
    ) -> ProviderAdmissionResult:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    FOR UPDATE
                    """
                ),
                {"adapter_code": adapter_code},
            ).mappings().one_or_none()
            if row is None:
                return ProviderAdmissionResult(
                    outcome=ProviderAdmissionOutcome.NOT_REGISTERED,
                    adapter_code=adapter_code,
                    permit_id=None,
                    circuit_state=None,
                    retry_after_seconds=None,
                    reason_code="SOURCE_PROVIDER_NOT_REGISTERED",
                )
            capability = self._capability_from_row(row)
            capability = self._recover_expired(
                connection,
                capability=capability,
                at=at,
            )
            capability = capability.roll_quota_window(at=at)
            capability = capability.prepare_circuit_for_admission(at=at)

            if capability.lifecycle_state is ProviderCapabilityLifecycle.PAUSED:
                self._update_capability(connection, capability)
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.PAUSED,
                    reason_code="SOURCE_PROVIDER_PAUSED",
                )
            if capability.lifecycle_state is ProviderCapabilityLifecycle.RETIRED:
                self._update_capability(connection, capability)
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.RETIRED,
                    reason_code="SOURCE_PROVIDER_RETIRED",
                )
            if capability.circuit_state is ProviderCircuitState.OPEN:
                self._update_capability(connection, capability)
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.CIRCUIT_OPEN,
                    reason_code="SOURCE_PROVIDER_CIRCUIT_OPEN",
                    retry_after_seconds=capability.retry_after_for_open_circuit(at=at),
                )

            active_probe = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM knowledge.source_provider_capture_permit
                    WHERE adapter_code = :adapter_code
                      AND state = 'ACTIVE'
                      AND was_half_open_probe
                    LIMIT 1
                    """
                ),
                {"adapter_code": adapter_code},
            ).scalar_one_or_none()
            if (
                capability.circuit_state is ProviderCircuitState.HALF_OPEN
                and active_probe is not None
            ):
                self._update_capability(connection, capability)
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.CIRCUIT_OPEN,
                    reason_code="SOURCE_PROVIDER_HALF_OPEN_PROBE_ACTIVE",
                    retry_after_seconds=capability.permit_ttl_seconds,
                )
            if capability.window_request_count >= capability.quota_limit:
                self._update_capability(connection, capability)
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.RATE_LIMITED,
                    reason_code="SOURCE_PROVIDER_RATE_LIMITED",
                    retry_after_seconds=capability.retry_after_for_quota(at=at),
                )

            is_probe = capability.circuit_state is ProviderCircuitState.HALF_OPEN
            permit = ProviderCapturePermit.create(
                adapter_code=adapter_code,
                admitted_at=at,
                expires_at=at + timedelta(seconds=capability.permit_ttl_seconds),
                was_half_open_probe=is_probe,
            )
            capability = capability.count_admission(at=at)
            self._update_capability(connection, capability)
            connection.execute(
                text(
                    """
                    INSERT INTO knowledge.source_provider_capture_permit (
                        id, adapter_code, state, was_half_open_probe,
                        admitted_at, expires_at, completed_at, failure_code
                    ) VALUES (
                        :id, :adapter_code, :state, :was_half_open_probe,
                        :admitted_at, :expires_at, :completed_at, :failure_code
                    )
                    """
                ),
                self._permit_params(permit),
            )
            return ProviderAdmissionResult(
                outcome=ProviderAdmissionOutcome.ADMITTED,
                adapter_code=adapter_code,
                permit_id=permit.id,
                circuit_state=capability.circuit_state,
                retry_after_seconds=None,
                reason_code="SOURCE_PROVIDER_ADMITTED",
            )

    def complete_success(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderCapturePermit:
        with self._engine.begin() as connection:
            capability = self._lock_capability(connection, adapter_code)
            permit = self._lock_permit(connection, permit_id)
            completed = permit.succeed(adapter_code=adapter_code, at=at)
            capability = capability.record_success(
                at=at,
                was_half_open_probe=permit.was_half_open_probe,
            )
            self._update_capability(connection, capability)
            return self._update_permit(connection, completed)

    def complete_failure(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
        failure_code: str,
    ) -> ProviderCapturePermit:
        with self._engine.begin() as connection:
            capability = self._lock_capability(connection, adapter_code)
            permit = self._lock_permit(connection, permit_id)
            completed = permit.fail(
                adapter_code=adapter_code,
                at=at,
                failure_code=failure_code,
            )
            capability = capability.record_failure(
                at=at,
                was_half_open_probe=permit.was_half_open_probe,
            )
            self._update_capability(connection, capability)
            return self._update_permit(connection, completed)

    def _recover_expired(
        self,
        connection,
        *,
        capability: SourceProviderCapability,
        at: datetime,
    ) -> SourceProviderCapability:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM knowledge.source_provider_capture_permit
                WHERE adapter_code = :adapter_code
                  AND state = 'ACTIVE'
                  AND expires_at <= :at
                ORDER BY expires_at, id
                FOR UPDATE SKIP LOCKED
                """
            ),
            {"adapter_code": capability.adapter_code, "at": at},
        ).mappings().all()
        permits = tuple(self._permit_from_row(row) for row in rows)
        for permit in permits:
            self._update_permit(connection, permit.abandon(at=at))
        included_probe = any(permit.was_half_open_probe for permit in permits)
        updated = capability.after_expired_permits(
            count=len(permits),
            at=at,
            included_half_open_probe=included_probe,
        )
        return self._update_capability(connection, updated)

    @staticmethod
    def _lock_capability(connection, adapter_code: str) -> SourceProviderCapability:
        row = connection.execute(
            text(
                """
                SELECT *
                FROM knowledge.source_provider_capability
                WHERE adapter_code = :adapter_code
                FOR UPDATE
                """
            ),
            {"adapter_code": adapter_code},
        ).mappings().one_or_none()
        if row is None:
            raise KeyError(adapter_code)
        return PostgresSourceProviderAdmissionRepository._capability_from_row(row)

    @staticmethod
    def _lock_permit(connection, permit_id: UUID) -> ProviderCapturePermit:
        row = connection.execute(
            text(
                """
                SELECT *
                FROM knowledge.source_provider_capture_permit
                WHERE id = :permit_id
                FOR UPDATE
                """
            ),
            {"permit_id": permit_id},
        ).mappings().one_or_none()
        if row is None:
            raise KeyError(permit_id)
        return PostgresSourceProviderAdmissionRepository._permit_from_row(row)

    @staticmethod
    def _update_capability(
        connection,
        capability: SourceProviderCapability,
    ) -> SourceProviderCapability:
        row = connection.execute(
            text(
                """
                UPDATE knowledge.source_provider_capability
                SET lifecycle_state = :lifecycle_state,
                    window_started_at = :window_started_at,
                    window_request_count = :window_request_count,
                    consecutive_failure_count = :consecutive_failure_count,
                    circuit_state = :circuit_state,
                    circuit_opened_at = :circuit_opened_at,
                    updated_at = :updated_at
                WHERE adapter_code = :adapter_code
                RETURNING *
                """
            ),
            PostgresSourceProviderAdmissionRepository._capability_params(capability),
        ).mappings().one()
        return PostgresSourceProviderAdmissionRepository._capability_from_row(row)

    @staticmethod
    def _update_permit(
        connection,
        permit: ProviderCapturePermit,
    ) -> ProviderCapturePermit:
        row = connection.execute(
            text(
                """
                UPDATE knowledge.source_provider_capture_permit
                SET state = :state,
                    completed_at = :completed_at,
                    failure_code = :failure_code
                WHERE id = :id
                RETURNING *
                """
            ),
            PostgresSourceProviderAdmissionRepository._permit_params(permit),
        ).mappings().one()
        return PostgresSourceProviderAdmissionRepository._permit_from_row(row)

    @staticmethod
    def _denied(
        capability: SourceProviderCapability,
        *,
        outcome: ProviderAdmissionOutcome,
        reason_code: str,
        retry_after_seconds: int | None = None,
    ) -> ProviderAdmissionResult:
        return ProviderAdmissionResult(
            outcome=outcome,
            adapter_code=capability.adapter_code,
            permit_id=None,
            circuit_state=capability.circuit_state,
            retry_after_seconds=retry_after_seconds,
            reason_code=reason_code,
        )

    @staticmethod
    def _capability_params(capability: SourceProviderCapability) -> dict[str, object]:
        return {
            "adapter_code": capability.adapter_code,
            "credential_mode": capability.credential_mode.value,
            "secret_ref": capability.secret_ref,
            "lifecycle_state": capability.lifecycle_state.value,
            "quota_limit": capability.quota_limit,
            "quota_window_seconds": capability.quota_window_seconds,
            "failure_threshold": capability.failure_threshold,
            "circuit_open_seconds": capability.circuit_open_seconds,
            "permit_ttl_seconds": capability.permit_ttl_seconds,
            "window_started_at": capability.window_started_at,
            "window_request_count": capability.window_request_count,
            "consecutive_failure_count": capability.consecutive_failure_count,
            "circuit_state": capability.circuit_state.value,
            "circuit_opened_at": capability.circuit_opened_at,
            "created_at": capability.created_at,
            "updated_at": capability.updated_at,
        }

    @staticmethod
    def _permit_params(permit: ProviderCapturePermit) -> dict[str, object]:
        return {
            "id": permit.id,
            "adapter_code": permit.adapter_code,
            "state": permit.state.value,
            "was_half_open_probe": permit.was_half_open_probe,
            "admitted_at": permit.admitted_at,
            "expires_at": permit.expires_at,
            "completed_at": permit.completed_at,
            "failure_code": permit.failure_code,
        }

    @staticmethod
    def _capability_from_row(row) -> SourceProviderCapability:
        return SourceProviderCapability(
            adapter_code=row["adapter_code"],
            credential_mode=ProviderCredentialMode(row["credential_mode"]),
            secret_ref=row["secret_ref"],
            lifecycle_state=ProviderCapabilityLifecycle(row["lifecycle_state"]),
            quota_limit=row["quota_limit"],
            quota_window_seconds=row["quota_window_seconds"],
            failure_threshold=row["failure_threshold"],
            circuit_open_seconds=row["circuit_open_seconds"],
            permit_ttl_seconds=row["permit_ttl_seconds"],
            window_started_at=row["window_started_at"],
            window_request_count=row["window_request_count"],
            consecutive_failure_count=row["consecutive_failure_count"],
            circuit_state=ProviderCircuitState(row["circuit_state"]),
            circuit_opened_at=row["circuit_opened_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _permit_from_row(row) -> ProviderCapturePermit:
        return ProviderCapturePermit(
            id=row["id"],
            adapter_code=row["adapter_code"],
            state=ProviderCapturePermitState(row["state"]),
            was_half_open_probe=row["was_half_open_probe"],
            admitted_at=row["admitted_at"],
            expires_at=row["expires_at"],
            completed_at=row["completed_at"],
            failure_code=row["failure_code"],
        )
