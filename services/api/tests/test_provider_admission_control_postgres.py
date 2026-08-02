from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_source_provider_admission import (
    PostgresSourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionOutcome,
    ProviderCapturePermitState,
    ProviderCircuitState,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _service(engine, *, adapter_code: str, base: datetime, **overrides):
    repository = PostgresSourceProviderAdmissionRepository(engine)
    service = SourceProviderAdmissionService(repository)
    values = {
        "quota_limit": 10,
        "quota_window_seconds": 60,
        "failure_threshold": 2,
        "circuit_open_seconds": 5,
        "permit_ttl_seconds": 5,
    }
    values.update(overrides)
    service.register(
        adapter_code=adapter_code,
        secret_ref=f"vault://kefe/providers/{adapter_code}",
        created_at=base,
        **values,
    )
    return repository, service


def _cleanup(engine, *adapter_codes: str) -> None:
    with engine.begin() as connection:
        for adapter_code in adapter_codes:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_provider_capture_permit
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            )


def test_postgres_concurrent_quota_admission_is_transactional() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_quota_{uuid4().hex[:10]}.v1"
    try:
        _, service = _service(
            engine,
            adapter_code=adapter_code,
            base=base,
            quota_limit=1,
        )
        barrier = Barrier(2)

        def admit_once():
            local = SourceProviderAdmissionService(
                PostgresSourceProviderAdmissionRepository(engine)
            )
            barrier.wait()
            return local.admit(adapter_code=adapter_code, at=base)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(lambda _: admit_once(), range(2)))

        assert sorted(result.outcome.value for result in results) == [
            "ADMITTED",
            "RATE_LIMITED",
        ]
        limited = next(
            result
            for result in results
            if result.outcome is ProviderAdmissionOutcome.RATE_LIMITED
        )
        assert limited.retry_after_seconds == 60
        with engine.connect() as connection:
            count = connection.execute(
                text(
                    """
                    SELECT window_request_count
                    FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            ).scalar_one()
        assert count == 1
    finally:
        _cleanup(engine, adapter_code)


def test_postgres_half_open_allows_exactly_one_concurrent_probe() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_probe_{uuid4().hex[:10]}.v1"
    try:
        repository, service = _service(
            engine,
            adapter_code=adapter_code,
            base=base,
            failure_threshold=1,
            circuit_open_seconds=5,
        )
        first = service.admit(adapter_code=adapter_code, at=base)
        service.complete_failure(
            permit_id=first.permit_id,
            adapter_code=adapter_code,
            failure_code="OPEN_CIRCUIT",
            at=base + timedelta(seconds=1),
        )
        assert repository.get(adapter_code).circuit_state is ProviderCircuitState.OPEN
        barrier = Barrier(2)
        probe_at = base + timedelta(seconds=6)

        def probe_once():
            local = SourceProviderAdmissionService(
                PostgresSourceProviderAdmissionRepository(engine)
            )
            barrier.wait()
            return local.admit(adapter_code=adapter_code, at=probe_at)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(lambda _: probe_once(), range(2)))

        assert sorted(result.outcome.value for result in results) == [
            "ADMITTED",
            "CIRCUIT_OPEN",
        ]
        admitted = next(
            result
            for result in results
            if result.outcome is ProviderAdmissionOutcome.ADMITTED
        )
        assert admitted.circuit_state is ProviderCircuitState.HALF_OPEN
        with engine.connect() as connection:
            active_probe_count = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM knowledge.source_provider_capture_permit
                    WHERE adapter_code = :adapter_code
                      AND state = 'ACTIVE'
                      AND was_half_open_probe
                    """
                ),
                {"adapter_code": adapter_code},
            ).scalar_one()
        assert active_probe_count == 1
    finally:
        _cleanup(engine, adapter_code)


def test_postgres_expired_permit_is_abandoned_and_counts_as_failure() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_expired_{uuid4().hex[:10]}.v1"
    try:
        repository, service = _service(
            engine,
            adapter_code=adapter_code,
            base=base,
            failure_threshold=1,
            permit_ttl_seconds=5,
        )
        permit = service.admit(adapter_code=adapter_code, at=base)
        denied = service.admit(
            adapter_code=adapter_code,
            at=base + timedelta(seconds=5),
        )

        assert denied.outcome is ProviderAdmissionOutcome.CIRCUIT_OPEN
        capability = repository.get(adapter_code)
        assert capability.circuit_state is ProviderCircuitState.OPEN
        with engine.connect() as connection:
            permit_state = connection.execute(
                text(
                    """
                    SELECT state
                    FROM knowledge.source_provider_capture_permit
                    WHERE id = :permit_id
                    """
                ),
                {"permit_id": permit.permit_id},
            ).scalar_one()
        assert permit_state == ProviderCapturePermitState.ABANDONED.value
    finally:
        _cleanup(engine, adapter_code)


def test_postgres_permit_completion_requires_exact_adapter_and_active_ttl() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    first_code = f"test.pg_exact_{uuid4().hex[:10]}.v1"
    second_code = f"test.pg_other_{uuid4().hex[:10]}.v1"
    try:
        repository, service = _service(
            engine,
            adapter_code=first_code,
            base=base,
        )
        _service(engine, adapter_code=second_code, base=base)
        permit = service.admit(adapter_code=first_code, at=base)

        with pytest.raises(ValueError, match="another adapter"):
            service.complete_success(
                permit_id=permit.permit_id,
                adapter_code=second_code,
                at=base + timedelta(seconds=1),
            )
        with pytest.raises(ValueError, match="expired"):
            service.complete_success(
                permit_id=permit.permit_id,
                adapter_code=first_code,
                at=base + timedelta(seconds=5),
            )
        with engine.connect() as connection:
            state = connection.execute(
                text(
                    """
                    SELECT state
                    FROM knowledge.source_provider_capture_permit
                    WHERE id = :permit_id
                    """
                ),
                {"permit_id": permit.permit_id},
            ).scalar_one()
        assert state == ProviderCapturePermitState.ACTIVE.value
        assert repository.get(first_code).circuit_state is ProviderCircuitState.CLOSED
    finally:
        _cleanup(engine, first_code, second_code)
