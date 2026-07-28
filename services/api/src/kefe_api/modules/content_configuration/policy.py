from __future__ import annotations

from kefe_api.modules.content_authoring.models import AuthoringCaseVersion


def derive_required_review_modes(version: AuthoringCaseVersion) -> frozenset[str]:
    required: set[str] = set()
    if version.is_fact_bearing or version.is_real_event:
        required.add("SOURCE_VERIFICATION")
    if version.content_risk in {"L2", "L3"}:
        required.add("RISK_REVIEW")
    if (
        version.primary_domain_code == "CIVIC_POLITICS"
        or "CIVIC_INTEGRITY" in version.modifiers
    ):
        required.add("CIVIC_REVIEW")
    if version.content_risk == "L3":
        required.add("EDITORIAL")
    return frozenset(required)
