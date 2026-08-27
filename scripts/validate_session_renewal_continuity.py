from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/session-renewal-continuity.v1.json"
ROUTER = ROOT / "services/api/src/kefe_api/modules/identity/router.py"
SERVICE = ROOT / "services/api/src/kefe_api/modules/identity/session_renewal_service.py"
POSTGRES = ROOT / "services/api/src/kefe_api/infrastructure/postgres_identity.py"
OPENAPI = ROOT / "docs/contracts/openapi-mvp.v0.19.overlay.json"
MOBILE_CLIENT = ROOT / "apps/mobile/lib/core/network/session_renewal_client.dart"
BUNDLE = ROOT / "apps/mobile/lib/core/storage/credential_bundle.dart"
SECURE_STORE = ROOT / "apps/mobile/lib/core/storage/secure_credential_store.dart"
PROVIDERS = ROOT / "apps/mobile/lib/features/decision/application/decision_controller.dart"
PRODUCTION = ROOT / "apps/mobile/lib/main.dart"
CONNECTED_ALPHA = ROOT / "apps/mobile/lib/main_connected_alpha.dart"
PREVIEW = ROOT / "apps/mobile/lib/main_preview.dart"
API_TEST = ROOT / "services/api/tests/test_session_renewal_http.py"
SERVICE_TEST = ROOT / "services/api/tests/test_session_renewal_service.py"
POSTGRES_TEST = ROOT / "services/api/tests/test_session_renewal_postgres.py"
MOBILE_TEST = ROOT / "apps/mobile/test/session_renewal_client_test.dart"
LOCALIZATION_TEST = ROOT / "apps/mobile/test/session_renewal_localization_test.dart"
FORBIDDEN_WORKFLOW = ROOT / ".github/workflows/session-renewal-continuity.yml"


def require(text: str, needle: str, *, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"{where} missing session continuity boundary: {needle}")


def forbid(text: str, needle: str, *, where: str) -> None:
    if needle in text:
        raise SystemExit(f"{where} contains forbidden session behavior: {needle}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_id"] != "KEFE-SESSION-RENEWAL-CONTINUITY-001":
        raise SystemExit("unexpected session renewal contract id")
    if contract["authority_alignment"]["silent_guest_replacement_allowed"] is not False:
        raise SystemExit("silent guest replacement must remain forbidden")
    if contract["mobile"]["atomic_credential_bundle_required"] is not True:
        raise SystemExit("mobile credential persistence must remain atomic")
    if contract["mobile"]["single_flight_renewal_required"] is not True:
        raise SystemExit("mobile renewal must remain single-flight")
    if contract["mobile"]["synthesized_access_expiry_allowed"] is not False:
        raise SystemExit("mobile access expiry must come from the server")
    if contract["verification"]["new_feature_specific_workflow_allowed"] is not False:
        raise SystemExit("session renewal must use existing CI workflows")
    if FORBIDDEN_WORKFLOW.exists():
        raise SystemExit("session renewal must not add a feature-specific workflow")

    router = ROUTER.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    openapi = OPENAPI.read_text(encoding="utf-8")
    client = MOBILE_CLIENT.read_text(encoding="utf-8")
    bundle = BUNDLE.read_text(encoding="utf-8")
    secure = SECURE_STORE.read_text(encoding="utf-8")
    providers = PROVIDERS.read_text(encoding="utf-8")
    production = PRODUCTION.read_text(encoding="utf-8")
    connected_alpha = CONNECTED_ALPHA.read_text(encoding="utf-8")
    preview = PREVIEW.read_text(encoding="utf-8")
    api_test = API_TEST.read_text(encoding="utf-8")
    service_test = SERVICE_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    mobile_test = MOBILE_TEST.read_text(encoding="utf-8")
    localization_test = LOCALIZATION_TEST.read_text(encoding="utf-8")

    for needle in (
        '"/session/renew"',
        '"/session/continuity/bootstrap"',
        "service.require_active_access_token(authorization)",
        "_renewal_service(request).bootstrap(access_token=access_token)",
    ):
        require(router, needle, where="identity router")
    for needle in (
        "def bootstrap(self, *, access_token: str)",
        "SessionBootstrapStatus.ACTIVE_LEGACY",
        "SessionBootstrapStatus.ACTIVE_CURRENT",
        "AUTH_SESSION_CONTINUITY_EXPIRED",
    ):
        require(service, needle, where="session renewal service")
    for needle in (
        "def resolve_bootstrap(",
        "def bootstrap_session(",
        "expected_rotation_counter",
        "previous_token_valid_until",
    ):
        require(postgres, needle, where="PostgreSQL identity repository")
    for path in (
        "/v1/identity/session/renew",
        "/v1/identity/session/continuity/bootstrap",
    ):
        require(openapi, path, where="canonical OpenAPI")

    for needle in (
        "class SessionRenewalCoordinator",
        "Future<SessionCredentialBundle>? _renewalInFlight",
        "_singleFlight(() => _renew(bundle))",
        "_singleFlight(() => _bootstrap(legacyAccess))",
        "renewAfterExpired(firstToken)",
        "AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED",
        "AUTH_GUEST_CONTINUITY_REQUIRED",
        "AUTH_LEGACY_CONTINUITY_REQUIRED",
    ):
        require(client, needle, where="mobile session renewal client")
    forbid(client, "autoCreateGuest", where="mobile session renewal client")
    for needle in (
        "required this.actorKind",
        "required this.accessExpiresAt",
        "required this.renewalToken",
        "required this.rotationCounter",
        "SessionCredentialBundle.fromApiJson",
    ):
        require(bundle, needle, where="mobile credential bundle")
    for needle in (
        "_storage.write(key: _bundleKey, value: bundle.encode())",
        "_storage.delete(key: _accessTokenKey)",
        "_storage.delete(key: _actorIdKey)",
    ):
        require(secure, needle, where="secure credential store")
    for needle in (
        "sessionRenewalCoordinatorProvider",
        "RenewingHttpClient(",
        "sessionRenewalCoordinator:",
    ):
        require(providers, needle, where="mobile production providers")
    require(production, "sessionRenewalCoordinatorProvider", where="production composition")
    require(
        connected_alpha,
        "sessionRenewalCoordinatorProvider",
        where="Connected Alpha composition",
    )
    forbid(preview, "sessionRenewalCoordinatorProvider", where="Preview composition")

    for needle in (
        "test_active_legacy_access_http_bootstrap_preserves_actor_and_converges",
    ):
        require(api_test, needle, where="session renewal API tests")
    require(
        service_test,
        "test_expired_legacy_access_cannot_bootstrap",
        where="session renewal service tests",
    )
    for needle in (
        "test_postgres_legacy_bootstrap_survives_restart_and_can_renew",
        "test_postgres_concurrent_same_renewal_token_converges",
    ):
        require(postgres_test, needle, where="PostgreSQL session tests")
    for needle in (
        "proactive renewal is single-flight across concurrent requests",
        "expired access renews once and retries the protected request once",
        "active legacy access bootstraps without creating a new actor",
        "terminal account renewal failure requires reauthentication",
        "guest continuity failure reaches repository as an explicit API state",
    ):
        require(mobile_test, needle, where="mobile renewal tests")
    for needle in (
        "AUTH_GUEST_CONTINUITY_REQUIRED",
        "AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED",
        "AUTH_LEGACY_CONTINUITY_REQUIRED",
        "Locale('tr', 'TR')",
        "Locale('en', 'US')",
    ):
        require(localization_test, needle, where="session localization tests")

    print("Session renewal continuity: OK")


if __name__ == "__main__":
    main()
