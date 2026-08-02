from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
    ProviderPermitExecutionContext,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code


class PostgresProviderPermitExecutionContextRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext:
        require_versioned_adapter_code(adapter_code)
        with self._engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as connection:
            with connection.begin():
                connection.execute(text("SET TRANSACTION READ ONLY"))
                row = connection.execute(
                    text(
                        """
                        SELECT
                            permit.id AS permit_id,
                            permit.adapter_code,
                            capability.credential_mode,
                            capability.secret_ref,
                            permit.expires_at AS permit_expires_at
                        FROM knowledge.source_provider_capture_permit AS permit
                        JOIN knowledge.source_provider_capability AS capability
                          ON capability.adapter_code = permit.adapter_code
                        WHERE permit.id = :permit_id
                          AND permit.adapter_code = :adapter_code
                          AND permit.state = 'ACTIVE'
                          AND permit.expires_at > :at
                          AND capability.lifecycle_state = 'ENABLED'
                        """
                    ),
                    {
                        "permit_id": permit_id,
                        "adapter_code": adapter_code,
                        "at": at,
                    },
                ).mappings().one_or_none()
        if row is None:
            raise ProviderPermitContextError()
        return ProviderPermitExecutionContext(
            permit_id=row["permit_id"],
            adapter_code=row["adapter_code"],
            credential_mode=ProviderCredentialMode(row["credential_mode"]),
            secret_ref=row["secret_ref"],
            permit_expires_at=row["permit_expires_at"],
        )
