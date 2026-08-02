from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
    require_secret_reference,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


@dataclass(frozen=True, slots=True)
class ProviderPermitExecutionContext:
    permit_id: UUID
    adapter_code: str
    secret_ref: str | None = field(repr=False)
    permit_expires_at: datetime
    credential_mode: ProviderCredentialMode = ProviderCredentialMode.SECRET_REF

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if type(self.credential_mode) is not ProviderCredentialMode:
            raise ValueError("credential_mode must be an exact ProviderCredentialMode")
        if self.credential_mode is ProviderCredentialMode.PUBLIC:
            if self.secret_ref is not None:
                raise ValueError("PUBLIC permit context cannot contain secret_ref")
        else:
            if self.secret_ref is None:
                raise ValueError("SECRET_REF permit context requires secret_ref")
            require_secret_reference(self.secret_ref)
        _require_utc(self.permit_expires_at, "permit_expires_at")

    def __repr__(self) -> str:
        return (
            "ProviderPermitExecutionContext("
            f"permit_id={self.permit_id!r}, "
            f"adapter_code={self.adapter_code!r}, "
            f"credential_mode={self.credential_mode.value!r}, "
            "secret_ref=<REDACTED>, "
            f"permit_expires_at={self.permit_expires_at!r})"
        )


@dataclass(frozen=True, slots=True)
class ProviderPermitContextError(Exception):
    code: str = "SOURCE_PROVIDER_PERMIT_CONTEXT_INVALID"

    def __str__(self) -> str:
        return self.code
