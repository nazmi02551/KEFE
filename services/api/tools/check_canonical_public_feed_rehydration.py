from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOMAIN = ROOT / "services/api/src/kefe_api/modules/knowledge/canonical_public_feed_catalog.py"
COMPOSITION = ROOT / "services/api/src/kefe_api/infrastructure/canonical_public_feed_composition.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"canonical public-feed rehydration failed: {message}")


def main() -> None:
    domain = DOMAIN.read_text(encoding="utf-8")
    start = domain.index("    def rehydrate_runtime_profiles(")
    end = domain.index("    def list_definitions(", start)
    method = domain[start:end]

    for marker in (
        "self._repository.list_definitions()",
        "self._repository.get_activation_for_definition(",
        "PublicFeedActivationState.RETIRED",
        "PublicFeedCatalogState.APPROVED",
        "self._build_runtime_profile(definition)",
        "self._runtime_profiles.register_or_get(profile)",
        "persisted public-feed activation identity drifted",
    ):
        require(marker in method, f"rehydration missing {marker}")

    for forbidden in (
        "self._provider_admission.register(",
        "self._provider_admission.pause(",
        "self._provider_admission.resume(",
        "self._provider_admission.retire(",
        "self._scheduler.create_schedule(",
        "self._scheduler.pause(",
        "self._scheduler.resume(",
        "self._scheduler.retire(",
        "append_audit(",
        "add_activation(",
        "replace_activation(",
    ):
        require(
            forbidden not in method,
            f"rehydration must not mutate provider, schedule or audit via {forbidden}",
        )

    composition = COMPOSITION.read_text(encoding="utf-8")
    require(
        "service.rehydrate_runtime_profiles()" in composition,
        "composition must restore persisted non-retired runtime profiles",
    )
    require(
        composition.index("service.rehydrate_runtime_profiles()")
        < composition.index("return CanonicalPublicFeedComposition("),
        "rehydration must complete before composition is exposed",
    )

    print("canonical public-feed rehydration PASS")


if __name__ == "__main__":
    main()
