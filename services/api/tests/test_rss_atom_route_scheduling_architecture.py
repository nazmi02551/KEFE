from __future__ import annotations

from kefe_api.modules.knowledge.rss_atom_route_scheduling import (
    RssAtomRouteScheduleService,
)


def test_rss_atom_route_scheduling_module_is_importable() -> None:
    assert RssAtomRouteScheduleService.__name__ == (
        "RssAtomRouteScheduleService"
    )
