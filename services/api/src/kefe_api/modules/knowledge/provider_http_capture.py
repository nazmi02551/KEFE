from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from kefe_api.modules.knowledge.provider_http_auth import SecureProviderHttpExecutor
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    OutboundHttpRequest,
    ProviderHttpResponse,
    RetryableProviderHttpError,
)
from kefe_api.modules.knowledge.provider_secret_execution import SecretAccess
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

MAX_EXTERNAL_LOCATOR_CHARS = 4096
MAX_TRACE_ID_CHARS = 128
_PROVIDER_HTTP_ERROR_CODE = re.compile(r"^PROVIDER_HTTP_[A-Z0-9_]{1,80}$")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _require_bounded_text(
    value: str,
    *,
    field_name: str,
    max_chars: int,
) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must not be blank or padded")
    if len(value) > max_chars:
        raise ValueError(f"{field_name} exceeds the supported length")


def _map_http_error_code(code: str) -> str | None:
    if _PROVIDER_HTTP_ERROR_CODE.fullmatch(code) is None:
        return None
    return f"SOURCE_{code}"


@dataclass(frozen=True, slots=True, repr=False)
class ProviderHttpCapturePlan:
    adapter_code: str
    request: OutboundHttpRequest

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if not isinstance(self.request, OutboundHttpRequest):
            raise ValueError("provider HTTP capture plan requires OutboundHttpRequest")
        if self.request.adapter_code != self.adapter_code:
            raise ValueError("provider HTTP capture plan adapter code mismatch")

    def __repr__(self) -> str:
        return (
            "ProviderHttpCapturePlan("
            f"adapter_code={self.adapter_code!r}, request=<redacted>)"
        )


class ProviderHttpCaptureDefinition(Protocol):
    @property
    def adapter_code(self) -> str: ...

    def build_plan(
        self,
        *,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ) -> ProviderHttpCapturePlan: ...

    def parse_response(
        self,
        *,
        plan: ProviderHttpCapturePlan,
        response: ProviderHttpResponse,
        trace_id: str,
        at: datetime,
    ) -> CapturedSource: ...


class ProviderHttpCaptureAdapter:
    def __init__(
        self,
        *,
        definition: ProviderHttpCaptureDefinition,
        http_executor: SecureProviderHttpExecutor,
    ) -> None:
        require_versioned_adapter_code(definition.adapter_code)
        self._adapter_code = definition.adapter_code
        self._definition = definition
        self._http_executor = http_executor

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
        secret: SecretAccess,
        at: datetime,
    ) -> CapturedSource:
        try:
            _require_bounded_text(
                external_locator,
                field_name="external_locator",
                max_chars=MAX_EXTERNAL_LOCATOR_CHARS,
            )
            _require_bounded_text(
                trace_id,
                field_name="trace_id",
                max_chars=MAX_TRACE_ID_CHARS,
            )
            _require_utc(at, "at")
        except ValueError as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_PLAN_INVALID"
            ) from exc

        try:
            plan = self._definition.build_plan(
                external_locator=external_locator,
                trace_id=trace_id,
                at=at,
            )
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_PLAN_INVALID"
            ) from exc
        if not isinstance(plan, ProviderHttpCapturePlan):
            raise FinalSourceCaptureError("SOURCE_PROVIDER_HTTP_PLAN_INVALID")
        if (
            plan.adapter_code != self.adapter_code
            or plan.request.adapter_code != self.adapter_code
        ):
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_ADAPTER_MISMATCH"
            )

        try:
            response = self._http_executor.execute(
                plan.request,
                secret=secret,
                at=at,
            )
        except RetryableProviderHttpError as exc:
            mapped = _map_http_error_code(exc.code)
            if mapped is None:
                raise FinalSourceCaptureError(
                    "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
                ) from exc
            raise RetryableSourceCaptureError(mapped) from exc
        except FinalProviderHttpError as exc:
            mapped = _map_http_error_code(exc.code)
            if mapped is None:
                raise FinalSourceCaptureError(
                    "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
                ) from exc
            raise FinalSourceCaptureError(mapped) from exc
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
            ) from exc
        if type(response) is not ProviderHttpResponse:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
            )

        try:
            captured = self._definition.parse_response(
                plan=plan,
                response=response,
                trace_id=trace_id,
                at=at,
            )
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_RESPONSE_INVALID"
            ) from exc
        if type(captured) is not CapturedSource:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_HTTP_RESPONSE_INVALID"
            )
        return captured


class ProviderHttpCaptureAdapterFactory:
    def __init__(self, http_executor: SecureProviderHttpExecutor) -> None:
        self._http_executor = http_executor

    def create(
        self,
        definition: ProviderHttpCaptureDefinition,
    ) -> ProviderHttpCaptureAdapter:
        return ProviderHttpCaptureAdapter(
            definition=definition,
            http_executor=self._http_executor,
        )


__all__ = [
    "MAX_EXTERNAL_LOCATOR_CHARS",
    "MAX_TRACE_ID_CHARS",
    "ProviderHttpCaptureAdapter",
    "ProviderHttpCaptureAdapterFactory",
    "ProviderHttpCaptureDefinition",
    "ProviderHttpCapturePlan",
]
