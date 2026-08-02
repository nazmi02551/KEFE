from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Protocol

from kefe_api.modules.knowledge.provider_http_capture import (
    MAX_EXTERNAL_LOCATOR_CHARS,
    MAX_TRACE_ID_CHARS,
    ProviderHttpCapturePlan,
)
from kefe_api.modules.knowledge.provider_http_evidence_capture import (
    ProviderHttpParsedSource,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    FinalProviderHttpError,
    ProviderHttpResponse,
    RetryableProviderHttpError,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_evidence import (
    FinalRawSourceEvidenceError,
    RawSourceEvidenceSeal,
    RawSourceEvidenceStore,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

_PROVIDER_HTTP_ERROR_CODE = re.compile(r"^PROVIDER_HTTP_[A-Z0-9_]{1,80}$")
_PUBLIC_PARSE_ERROR_CODE = re.compile(
    r"^SOURCE_PUBLIC_HTTP_PARSE_[A-Z0-9_]{1,80}$"
)


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


class FinalPublicHttpParseError(Exception):
    def __init__(self, code: str) -> None:
        if _PUBLIC_PARSE_ERROR_CODE.fullmatch(code) is None:
            raise ValueError("public HTTP parse error code is invalid")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"FinalPublicHttpParseError(code={self.code!r})"


class EvidenceBackedPublicHttpCaptureDefinition(Protocol):
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
    ) -> ProviderHttpParsedSource: ...


class EvidenceBackedPublicHttpCaptureAdapter:
    def __init__(
        self,
        *,
        definition: EvidenceBackedPublicHttpCaptureDefinition,
        transport: ControlledProviderHttpTransport,
        evidence_store: RawSourceEvidenceStore,
    ) -> None:
        require_versioned_adapter_code(definition.adapter_code)
        self._adapter_code = definition.adapter_code
        self._definition = definition
        self._transport = transport
        self._evidence_store = evidence_store

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
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
                "SOURCE_PUBLIC_HTTP_PLAN_INVALID"
            ) from exc

        try:
            plan = self._definition.build_plan(
                external_locator=external_locator,
                trace_id=trace_id,
                at=at,
            )
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_PLAN_INVALID"
            ) from exc
        if type(plan) is not ProviderHttpCapturePlan:
            raise FinalSourceCaptureError("SOURCE_PUBLIC_HTTP_PLAN_INVALID")
        if (
            plan.adapter_code != self.adapter_code
            or plan.request.adapter_code != self.adapter_code
        ):
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_ADAPTER_MISMATCH"
            )

        try:
            response = self._transport.execute(plan.request)
        except RetryableProviderHttpError as exc:
            mapped = _map_http_error_code(exc.code)
            if mapped is None:
                raise FinalSourceCaptureError(
                    "SOURCE_PUBLIC_HTTP_EXECUTION_INVALID"
                ) from exc
            raise RetryableSourceCaptureError(mapped) from exc
        except FinalProviderHttpError as exc:
            mapped = _map_http_error_code(exc.code)
            if mapped is None:
                raise FinalSourceCaptureError(
                    "SOURCE_PUBLIC_HTTP_EXECUTION_INVALID"
                ) from exc
            raise FinalSourceCaptureError(mapped) from exc
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_EXECUTION_INVALID"
            ) from exc
        if type(response) is not ProviderHttpResponse:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_EXECUTION_INVALID"
            )

        try:
            seal = self._evidence_store.seal(
                adapter_code=self.adapter_code,
                body=response.body,
                media_type=response.media_type,
                sealed_at=at,
            )
        except RetryableRawSourceEvidenceError as exc:
            raise RetryableSourceCaptureError(
                "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE"
            ) from exc
        except FinalRawSourceEvidenceError as exc:
            raise FinalSourceCaptureError(
                "SOURCE_RAW_EVIDENCE_STORE_FINAL"
            ) from exc
        except Exception as exc:
            raise RetryableSourceCaptureError(
                "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE"
            ) from exc
        if type(seal) is not RawSourceEvidenceSeal:
            raise FinalSourceCaptureError(
                "SOURCE_RAW_EVIDENCE_CONTRACT_INVALID"
            )
        expected_hash = canonical_content_hash(response.body)
        if (
            seal.content_hash != expected_hash
            or seal.byte_length != len(response.body)
            or seal.media_type != response.media_type
            or seal.sealed_at != at
        ):
            raise FinalSourceCaptureError(
                "SOURCE_RAW_EVIDENCE_CONTRACT_INVALID"
            )

        try:
            parsed = self._definition.parse_response(
                plan=plan,
                response=response,
                trace_id=trace_id,
                at=at,
            )
        except FinalPublicHttpParseError as exc:
            raise FinalSourceCaptureError(exc.code) from exc
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_RESPONSE_INVALID"
            ) from exc
        if type(parsed) is not ProviderHttpParsedSource:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_HTTP_RESPONSE_INVALID"
            )

        return CapturedSource(
            content_hash=seal.content_hash,
            external_id=parsed.external_id,
            canonical_url=parsed.canonical_url,
            publisher_or_issuer=parsed.publisher_or_issuer,
            published_at=parsed.published_at,
            language_code=parsed.language_code,
            jurisdiction_code=parsed.jurisdiction_code,
            raw_storage_ref=seal.storage_ref,
        )


class EvidenceBackedPublicHttpCaptureAdapterFactory:
    def __init__(
        self,
        *,
        transport: ControlledProviderHttpTransport,
        evidence_store: RawSourceEvidenceStore,
    ) -> None:
        self._transport = transport
        self._evidence_store = evidence_store

    def create(
        self,
        definition: EvidenceBackedPublicHttpCaptureDefinition,
    ) -> EvidenceBackedPublicHttpCaptureAdapter:
        return EvidenceBackedPublicHttpCaptureAdapter(
            definition=definition,
            transport=self._transport,
            evidence_store=self._evidence_store,
        )


__all__ = [
    "EvidenceBackedPublicHttpCaptureAdapter",
    "EvidenceBackedPublicHttpCaptureAdapterFactory",
    "EvidenceBackedPublicHttpCaptureDefinition",
    "FinalPublicHttpParseError",
]
