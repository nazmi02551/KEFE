from __future__ import annotations

from kefe_api.modules.decision.system_health_transparency import (
    SystemHealthResult,
    SystemHealthStatus,
    SystemHealthTransparencyService,
)


def test_system_health_reports_optimal() -> None:
    r = SystemHealthTransparencyService.report_health(
        subsystem_id="sub_weigh_engine",
        subsystem_name="Kör Tartım ve Sinyal Toplayıcı",
        status=SystemHealthStatus.OPERATIONAL_OPTIMAL,
        p99_latency_ms=45,
        uptime_percentage_30d=99.98,
    )

    assert isinstance(r, SystemHealthResult)
    assert r.status == SystemHealthStatus.OPERATIONAL_OPTIMAL
    assert r.p99_latency_ms == 45
    assert r.uptime_percentage_30d == 99.98


def test_system_health_invalid_uptime() -> None:
    failed = False
    try:
        SystemHealthTransparencyService.report_health(
            subsystem_id="sub_err",
            subsystem_name="AB",  # < 3
            status=SystemHealthStatus.DEGRADED_PERFORMANCE,
            p99_latency_ms=-10,  # < 0
            uptime_percentage_30d=105.0,  # > 100.0
        )
    except ValueError:
        failed = True

    assert failed is True
