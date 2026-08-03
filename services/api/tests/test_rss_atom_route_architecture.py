from __future__ import annotations

from kefe_api.modules.knowledge.rss_atom_route import RssAtomRouteProfile


def test_rss_atom_route_architecture_module_is_importable() -> None:
    assert RssAtomRouteProfile.__name__ == "RssAtomRouteProfile"
