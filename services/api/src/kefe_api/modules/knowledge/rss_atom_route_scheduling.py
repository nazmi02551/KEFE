from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from kefe_api.modules.knowledge.provider_http_capture import (
    MAX_EXTERNAL_LOCATOR_CHARS,
)
from kefe_api.modules.knowledge.rss_atom_route import (
    RssAtomRouteBundle,
    RssAtomRouteRegistry,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code
from kefe_api.modules.knowledge.source_scheduler import (
    MAXIMUM_DISPATCH_ATTEMPTS,
    MAXIMUM_INTERVAL_SECONDS,
    MINIMUM_DISPATCH_ATTEMPTS,
    MINIMUM_INTERVAL_SECONDS,
    SourceAcquisitionSchedule,
    build_source_schedule_key,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceAcquisitionSchedulerService,
)

_ERROR_CODE = re.compile(r"^RSS_ATOM_ROUTE_SCHEDULE_[A-Z0-9_]{1,80}$")


class RssAtomRouteScheduleError(Exception):
    def __init__(self, code: str) -> None:
        if _ERROR_CODE.fullmatch(code) is None:
            raise ValueError("route schedule error code is invalid")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"RssAtomRouteScheduleError(code={self.code!r})"


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _require_locator(value: str) -> None:
    if not value or value != value.strip() or len(value) > MAX_EXTERNAL_LOCATOR_CHARS:
        raise ValueError("external_locator is invalid")


@dataclass(frozen=True, slots=True)
class RssAtomRouteScheduleRequest:
    route_code: str
    external_locator: str
    first_due_at: datetime
    interval_seconds: int
    max_dispatch_attempts: int

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.route_code)
        _require_locator(self.external_locator)
        _require_utc(self.first_due_at, "first_due_at")
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= (
            MAXIMUM_INTERVAL_SECONDS
        ):
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")


class RssAtomRouteScheduleService:
    def __init__(
        self,
        *,
        routes: RssAtomRouteRegistry,
        scheduler: SourceAcquisitionSchedulerService,
    ) -> None:
        self._routes = routes
        self._scheduler = scheduler

    def create(
        self,
        request: RssAtomRouteScheduleRequest,
        *,
        now: datetime | None = None,
    ) -> SourceAcquisitionSchedule:
        if type(request) is not RssAtomRouteScheduleRequest:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_REQUEST_INVALID"
            )
        if now is not None:
            _require_utc(now, "now")
        route = self._get_route(request.route_code)
        try:
            command = route.acquisition_command(request.external_locator)
            schedule = self._scheduler.create_schedule(
                adapter_code=command.adapter_code,
                external_locator=command.external_locator,
                pipeline_code=command.pipeline_code,
                pipeline_version=command.pipeline_version,
                configuration_hash=command.configuration_hash,
                first_due_at=request.first_due_at,
                interval_seconds=request.interval_seconds,
                max_dispatch_attempts=request.max_dispatch_attempts,
                taxonomy_version=command.taxonomy_version,
                methodology_version=command.methodology_version,
                locale=command.locale,
                jurisdiction_code=command.jurisdiction_code,
                now=now,
            )
        except RssAtomRouteScheduleError:
            raise
        except Exception as exc:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_CREATE_INVALID"
            ) from exc

        expected_key = build_source_schedule_key(
            adapter_code=command.adapter_code,
            external_locator=command.external_locator,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            configuration_hash=command.configuration_hash,
            first_due_at=request.first_due_at,
            interval_seconds=request.interval_seconds,
            max_dispatch_attempts=request.max_dispatch_attempts,
            taxonomy_version=command.taxonomy_version,
            methodology_version=command.methodology_version,
            locale=command.locale,
            jurisdiction_code=command.jurisdiction_code,
        )
        if schedule.schedule_key != expected_key:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_KEY_INVALID"
            )
        self._require_schedule_matches(route=route, schedule=schedule)
        return schedule

    def reconcile(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> RssAtomRouteBundle:
        if type(schedule) is not SourceAcquisitionSchedule:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_RECORD_INVALID"
            )
        try:
            route = self._routes.get_by_adapter_code(schedule.adapter_code)
        except (KeyError, ValueError) as exc:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_ROUTE_NOT_REGISTERED"
            ) from exc
        self._require_schedule_matches(route=route, schedule=schedule)
        return route

    def _get_route(self, route_code: str) -> RssAtomRouteBundle:
        try:
            return self._routes.get(route_code)
        except (KeyError, ValueError) as exc:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_ROUTE_NOT_REGISTERED"
            ) from exc

    @staticmethod
    def _require_schedule_matches(
        *,
        route: RssAtomRouteBundle,
        schedule: SourceAcquisitionSchedule,
    ) -> None:
        try:
            command = route.acquisition_command(schedule.external_locator)
        except Exception as exc:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_DRIFT"
            ) from exc
        expected = (
            command.adapter_code,
            command.pipeline_code,
            command.pipeline_version,
            command.configuration_hash,
            command.taxonomy_version,
            command.methodology_version,
            command.locale,
            command.jurisdiction_code,
        )
        actual = (
            schedule.adapter_code,
            schedule.pipeline_code,
            schedule.pipeline_version,
            schedule.configuration_hash,
            schedule.taxonomy_version,
            schedule.methodology_version,
            schedule.locale,
            schedule.jurisdiction_code,
        )
        if actual != expected:
            raise RssAtomRouteScheduleError(
                "RSS_ATOM_ROUTE_SCHEDULE_DRIFT"
            )


__all__ = [
    "RssAtomRouteScheduleError",
    "RssAtomRouteScheduleRequest",
    "RssAtomRouteScheduleService",
]
