from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_provider_execution_context import (
    PostgresProviderPermitExecutionContextRepository,
)
from kefe_api.infrastructure.postgres_source_provider_admission import (
    PostgresSourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


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


def test_postgres_execution_context_requires_exact_active_unexpired_permit() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    first_code = f"test.secret_context_{uuid4().hex[:10]}.v1"
    second_code = f"test.secret_other_{uuid4().hex[:10]}.v1"
    secret_ref = f"vault://kefe/providers/{first_code}"
    repository = PostgresSourceProviderAdmissionRepository(engine)
    service = SourceProviderAdmissionService(repository)
    contexts = PostgresProviderPermitExecutionContextRepository(engine)
    try:
        service.register(
            adapter_code=first_code,
            secret_ref=secret_ref,
            quota_limit=10,
            quota_window_seconds=60,
            failure_threshold=3,
            circuit_open_seconds=60,
            permit_ttl_seconds=10,
            created_at=base,
        )
        service.register(
            adapter_code=second_code,
            secret_ref=f"vault://kefe/providers/{second_code}",
            quota_limit=10,
            quota_window_seconds=60,
            failure_threshold=3,
            circuit_open_seconds=60,
            permit_ttl_seconds=10,
            created_at=base,
        )
        admitted = service.admit(adapter_code=first_code, at=base)
        assert admitted.permit_id is not None

        context = contexts.get_active_execution_context(
            permit_id=admitted.permit_id,
            adapter_code=first_code,
            at=base + timedelta(seconds=1),
        )
        assert context.adapter_code == first_code
        assert context.secret_ref == secret_ref
        assert secret_ref not in repr(context)

        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=admitted.permit_id,
                adapter_code=second_code,
                at=base + timedelta(seconds=1),
            )
        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=admitted.permit_id,
                adapter_code=first_code,
                at=base + timedelta(seconds=10),
            )

        service.complete_success(
            permit_id=admitted.permit_id,
            adapter_code=first_code,
            at=base + timedelta(seconds=2),
        )
        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=admitted.permit_id,
                adapter_code=first_code,
                at=base + timedelta(seconds=3),
            )
    finally:
        _cleanup(engine, first_code, second_code)


def test_postgres_paused_capability_cannot_resolve_active_permit_context() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.secret_paused_{uuid4().hex[:10]}.v1"
    repository = PostgresSourceProviderAdmissionRepository(engine)
    service = SourceProviderAdmissionService(repository)
    contexts = PostgresProviderPermitExecutionContextRepository(engine)
    try:
        service.register(
            adapter_code=adapter_code,
            secret_ref=f"secret://providers/{adapter_code}",
            quota_limit=10,
            quota_window_seconds=60,
            failure_threshold=3,
            circuit_open_seconds=60,
            permit_ttl_seconds=10,
            created_at=base,
        )
        admitted = service.admit(adapter_code=adapter_code, at=base)
        assert admitted.permit_id is not None
        service.pause(adapter_code, at=base + timedelta(seconds=1))

        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=admitted.permit_id,
                adapter_code=adapter_code,
                at=base + timedelta(seconds=2),
            )
    finally:
        _cleanup(engine, adapter_code)
