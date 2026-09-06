from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SystemHealthStatus(StrEnum):
    OPERATIONAL_OPTIMAL = "OPERATIONAL_OPTIMAL"
    DEGRADED_PERFORMANCE = "DEGRADED_PERFORMANCE"
    INCIDENT_ACTIVE = "INCIDENT_ACTIVE"


@dataclass(frozen=True, slots=True)
class SystemHealthResult:
    subsystem_id: str
    subsystem_name: str
    status: SystemHealthStatus
    p99_latency_ms: int
    uptime_percentage_30d: float
    active_incident_summary: str


class SystemHealthTransparencyService:
    @staticmethod
    def report_health(
        *,
        subsystem_id: str,
        subsystem_name: str,
        status: SystemHealthStatus,
        p99_latency_ms: int,
        uptime_percentage_30d: float,
        active_incident_summary: str = "",
    ) -> SystemHealthResult:
        if len(subsystem_name.strip()) < 3:
            raise ValueError("subsystem_name must have at least 3 characters")
        if p99_latency_ms < 0:
            raise ValueError(f"p99_latency_ms must be >= 0, got {p99_latency_ms}")
        if not 0.0 <= uptime_percentage_30d <= 100.0:
            raise ValueError(f"uptime_percentage_30d must be in [0.0, 100.0], got {uptime_percentage_30d}")

        return SystemHealthResult(
            subsystem_id=subsystem_id.strip(),
            subsystem_name=subsystem_name.strip(),
            status=status,
            p99_latency_ms=p99_latency_ms,
            uptime_percentage_30d=round(uptime_percentage_30d, 2),
            active_incident_summary=active_incident_summary.strip(),
        )
