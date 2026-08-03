from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
MODELS = API / "src/kefe_api/modules/admin_security/models.py"
POLICY = API / "src/kefe_api/modules/admin_security/policy.py"
SERVICE = API / "src/kefe_api/modules/admin_security/source_subscriptions.py"
ROUTER = API / "src/kefe_api/modules/admin_security/source_subscription_router.py"
MAIN = API / "src/kefe_api/main.py"
TEST = API / "tests/test_admin_rss_atom_subscriptions.py"
ADR = (
    ROOT
    / "docs/adr/0091-admin-rss-atom-subscription-inventory-and-step-up-activation.md"
)
CONTRACT = ROOT / "docs/contracts/admin-rss-atom-subscriptions-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/admin-rss-atom-subscriptions-ci.yml"

REQUIRED = (MODELS, POLICY, SERVICE, ROUTER, MAIN, TEST, ADR, CONTRACT, WORKFLOW)
INVENTORY_FIELDS = (
    "subscription_code",
    "adapter_code",
    "external_locator",
    "interval_seconds",
    "max_dispatch_attempts",
    "quota_limit",
    "quota_window_seconds",
    "failure_threshold",
    "circuit_open_seconds",
    "permit_ttl_seconds",
    "connect_timeout_ms",
    "read_timeout_ms",
    "total_timeout_ms",
    "max_redirect_hops",
    "locale",
    "jurisdiction_code",
    "configuration_hash",
)
ACTIVATION_FIELDS = (
    "subscription_code",
    "adapter_code",
    "configuration_hash",
    "capability_lifecycle",
    "circuit_state",
    "schedule_id",
    "schedule_state",
    "next_due_at",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, ast.ClassDef)
    }


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
    )


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing Admin RSS/Atom subscription files: {missing}")

    models = MODELS.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "admin-rss-atom-subscriptions-slice55":
        fail("Admin RSS/Atom subscription contract identity drifted")
    if contract.get("status") != "accepted":
        fail("Admin RSS/Atom subscription contract is not accepted")
    routes = contract.get("routes", {})
    if routes.get("list") != {
        "method": "GET",
        "path": "/internal/admin/v1/source-subscriptions",
        "capability": "SOURCE_SUBSCRIPTION_READ",
        "csrf_required": False,
        "step_up_required": False,
    }:
        fail("Admin source subscription list route contract drifted")
    if routes.get("activate") != {
        "method": "POST",
        "path": "/internal/admin/v1/source-subscriptions/{subscription_code}/activate",
        "capability": "SOURCE_SUBSCRIPTION_ACTIVATE",
        "csrf_required": True,
        "step_up_required": True,
        "expected_configuration_hash_required": True,
    }:
        fail("Admin source subscription activation route contract drifted")

    inventory_contract = contract.get("inventory", {})
    if tuple(inventory_contract.get("allowed_fields", ())) != INVENTORY_FIELDS:
        fail("Admin source subscription inventory allowlist drifted")
    if inventory_contract.get("manifest_mutation_allowed") is not False:
        fail("Admin HTTP manifest mutation must remain forbidden")
    activation_contract = contract.get("activation", {})
    if tuple(activation_contract.get("allowed_response_fields", ())) != ACTIVATION_FIELDS:
        fail("Admin source subscription activation allowlist drifted")
    if activation_contract.get("hash_comparison") != "constant_time":
        fail("Admin source subscription hash comparison must remain constant-time")
    if activation_contract.get("side_effect_before_hash_match") is not False:
        fail("Admin source subscription activation cannot mutate before hash match")

    for fragment in (
        'SOURCE_SUBSCRIPTION_READ = "SOURCE_SUBSCRIPTION_READ"',
        'SOURCE_SUBSCRIPTION_ACTIVATE = "SOURCE_SUBSCRIPTION_ACTIVATE"',
    ):
        if fragment not in models:
            fail(f"Admin subscription capability missing: {fragment}")
    for fragment in (
        "AdminRole.REVIEWER",
        "AdminRole.ACCESS_ADMIN",
        "AdminCapability.SOURCE_SUBSCRIPTION_READ",
        "AdminCapability.SOURCE_SUBSCRIPTION_ACTIVATE",
        "step_up_capabilities=frozenset(",
    ):
        if fragment not in policy:
            fail(f"Admin subscription role/step-up policy missing: {fragment}")

    classes = class_map(service)
    for class_name in (
        "AdminRssAtomSubscriptionView",
        "AdminRssAtomActivationView",
        "SecuredRssAtomSubscriptionService",
    ):
        if class_name not in classes:
            fail(f"Admin subscription service class missing: {class_name}")
    if fields(classes["AdminRssAtomSubscriptionView"]) != INVENTORY_FIELDS:
        fail("Admin subscription inventory view fields drifted")
    if fields(classes["AdminRssAtomActivationView"]) != ACTIVATION_FIELDS:
        fail("Admin subscription activation view fields drifted")

    secured = classes["SecuredRssAtomSubscriptionService"]
    list_source = ast.get_source_segment(service, method(secured, "list_subscriptions")) or ""
    activate_source = ast.get_source_segment(service, method(secured, "activate")) or ""
    for fragment in (
        "AdminCapability.SOURCE_SUBSCRIPTION_READ",
        "MAX_ADMIN_SUBSCRIPTION_ITEMS",
        "AdminRssAtomSubscriptionView.from_manifest(manifest)",
    ):
        if fragment not in list_source:
            fail(f"Admin subscription inventory guard missing: {fragment}")
    authorize_position = activate_source.find(
        "AdminCapability.SOURCE_SUBSCRIPTION_ACTIVATE"
    )
    compare_position = activate_source.find("compare_digest(")
    delegate_position = activate_source.find("self._activation.activate(")
    if not 0 <= authorize_position < compare_position < delegate_position:
        fail("Admin activation order must be authorize, hash compare, delegate")
    for fragment in (
        "SOURCE_SUBSCRIPTION_CONFIGURATION_STALE",
        "current_configuration_hash",
        "subscription_code=manifest.subscription_code",
        "activated_at=current",
    ):
        if fragment not in activate_source:
            fail(f"Admin subscription activation guard missing: {fragment}")

    router_classes = class_map(router)
    if fields(router_classes["SourceSubscriptionResponse"]) != INVENTORY_FIELDS:
        fail("Admin subscription HTTP inventory response fields drifted")
    if fields(router_classes["SourceSubscriptionActivationResponse"]) != ACTIVATION_FIELDS:
        fail("Admin subscription HTTP activation response fields drifted")
    for fragment in (
        'prefix="/internal/admin/v1/source-subscriptions"',
        '@router.get("", response_model=SourceSubscriptionInventoryResponse)',
        '"/{subscription_code}/activate"',
        "principal: ReadPrincipalDep",
        "principal: WritePrincipalDep",
        'pattern=r"^sha256:[0-9a-f]{64}$"',
    ):
        if fragment not in router:
            fail(f"Admin subscription HTTP guard missing: {fragment}")
    for forbidden in (
        "@router.put",
        "@router.delete",
        '@router.post(""',
        "terms_evidence_ref",
        "rate_limit_evidence_ref",
        "secret_ref",
        "raw_storage_ref",
        "object_key",
    ):
        if forbidden in router:
            fail(f"forbidden field/route leaked into Admin subscription router: {forbidden}")

    for fragment in (
        "SecuredRssAtomSubscriptionService(",
        "app.state.secured_rss_atom_subscription_service",
        "app.include_router(admin_source_subscription_router)",
    ):
        if fragment not in main_source:
            fail(f"Admin subscription application composition missing: {fragment}")
    if "RssAtomSubscriptionManifest(" in main_source or ".activate(" in main_source:
        fail("application startup must not create or activate a subscription")

    for test_name in contract.get("required_tests", ()):
        if test_name not in tests:
            fail(f"Admin subscription test evidence missing: {test_name}")

    for phrase in (
        "exactly two operations",
        "Only Access Admin receives activation access",
        "constant-time comparison",
        "No create, update, delete, import",
        "Production continues to compose an empty manifest registry",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")

    for phrase in (
        "Admin RSS Atom subscription architecture fitness",
        "Admin RSS Atom subscription behavior",
        "Parent Admin security architecture fitness",
        "Parent RSS Atom subscription activation architecture fitness",
        "check_admin_rss_atom_subscriptions_contract.py",
    ):
        if phrase not in workflow:
            fail(f"Admin subscription CI step missing: {phrase}")

    print("Admin RSS Atom subscriptions contract: PASS")


if __name__ == "__main__":
    main()
