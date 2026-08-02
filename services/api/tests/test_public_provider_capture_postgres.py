from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.infrastructure.postgres_provider_execution_context import (
    PostgresProviderPermitExecutionContextRepository,
)
from kefe_api.infrastructure.postgres_source_provider_admission import (
    PostgresSourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
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


def _register(
    engine,
    *,
    adapter_code: str,
    base: datetime,
    mode: ProviderCredentialMode,
):
    repository = PostgresSourceProviderAdmissionRepository(engine)
    service = SourceProviderAdmissionService(repository)
    capability = service.register(
        adapter_code=adapter_code,
        credential_mode=mode,
        secret_ref=(
            None
            if mode is ProviderCredentialMode.PUBLIC
            else f"vault://kefe/providers/{adapter_code}"
        ),
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=30,
        created_at=base,
    )
    return repository, service, capability


def test_postgres_public_capability_and_active_context_are_mode_exact() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_public_{uuid4().hex[:10]}.v1"
    try:
        repository, service, capability = _register(
            engine,
            adapter_code=adapter_code,
            base=base,
            mode=ProviderCredentialMode.PUBLIC,
        )
        assert capability.credential_mode is ProviderCredentialMode.PUBLIC
        assert capability.secret_ref is None
        permit = service.admit(adapter_code=adapter_code, at=base)
        context = PostgresProviderPermitExecutionContextRepository(
            engine
        ).get_active_execution_context(
            permit_id=permit.permit_id,
            adapter_code=adapter_code,
            at=base + timedelta(seconds=1),
        )
        assert context.credential_mode is ProviderCredentialMode.PUBLIC
        assert context.secret_ref is None
        assert repository.get(adapter_code).credential_mode is (
            ProviderCredentialMode.PUBLIC
        )
    finally:
        _cleanup(engine, adapter_code)


def test_postgres_existing_registration_defaults_to_secret_ref_mode() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_secret_{uuid4().hex[:10]}.v1"
    try:
        repository = PostgresSourceProviderAdmissionRepository(engine)
        capability = SourceProviderAdmissionService(repository).register(
            adapter_code=adapter_code,
            secret_ref=f"secret://providers/{adapter_code}",
            quota_limit=10,
            quota_window_seconds=60,
            failure_threshold=3,
            circuit_open_seconds=30,
            permit_ttl_seconds=30,
            created_at=base,
        )
        assert capability.credential_mode is ProviderCredentialMode.SECRET_REF
        assert capability.secret_ref is not None
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT credential_mode, secret_ref
                    FROM knowledge.source_provider_capability
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            ).mappings().one()
        assert row["credential_mode"] == "SECRET_REF"
        assert row["secret_ref"].startswith("secret://")
    finally:
        _cleanup(engine, adapter_code)


def test_postgres_credential_mode_cross_field_constraints_fail_closed() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    public_code = f"test.pg_constraint_public_{uuid4().hex[:8]}.v1"
    secret_code = f"test.pg_constraint_secret_{uuid4().hex[:8]}.v1"
    try:
        _register(
            engine,
            adapter_code=public_code,
            base=base,
            mode=ProviderCredentialMode.PUBLIC,
        )
        _register(
            engine,
            adapter_code=secret_code,
            base=base,
            mode=ProviderCredentialMode.SECRET_REF,
        )

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.source_provider_capability
                        SET secret_ref = 'secret://forbidden/public'
                        WHERE adapter_code = :adapter_code
                        """
                    ),
                    {"adapter_code": public_code},
                )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.source_provider_capability
                        SET credential_mode = 'PUBLIC'
                        WHERE adapter_code = :adapter_code
                        """
                    ),
                    {"adapter_code": secret_code},
                )
    finally:
        _cleanup(engine, public_code, secret_code)


def test_postgres_public_context_rejects_wrong_or_expired_permit() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_public_context_{uuid4().hex[:8]}.v1"
    try:
        _, service, _ = _register(
            engine,
            adapter_code=adapter_code,
            base=base,
            mode=ProviderCredentialMode.PUBLIC,
        )
        permit = service.admit(adapter_code=adapter_code, at=base)
        contexts = PostgresProviderPermitExecutionContextRepository(engine)
        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=uuid4(),
                adapter_code=adapter_code,
                at=base + timedelta(seconds=1),
            )
        with pytest.raises(ProviderPermitContextError):
            contexts.get_active_execution_context(
                permit_id=permit.permit_id,
                adapter_code=adapter_code,
                at=base + timedelta(seconds=30),
            )
    finally:
        _cleanup(engine, adapter_code)


def test_migration_downgrade_refuses_public_rows_and_preserves_head() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    adapter_code = f"test.pg_downgrade_public_{uuid4().hex[:8]}.v1"
    try:
        _register(
            engine,
            adapter_code=adapter_code,
            base=base,
            mode=ProviderCredentialMode.PUBLIC,
        )
        result = subprocess.run(
            ["alembic", "downgrade", "20260802_0024"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "cannot downgrade while PUBLIC provider capabilities exist" in (
            result.stdout + result.stderr
        )
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "20260803_0025"
    finally:
        _cleanup(engine, adapter_code)
