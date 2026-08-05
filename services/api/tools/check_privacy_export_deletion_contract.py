from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = json.loads(
    (ROOT / "docs/contracts/privacy-export-deletion-hardening.v1.json").read_text()
)
SERVICE = (ROOT / "services/api/src/kefe_api/modules/privacy/service.py").read_text()
ROUTER = (ROOT / "services/api/src/kefe_api/modules/privacy/router.py").read_text()
MEMORY = (ROOT / "services/api/src/kefe_api/modules/privacy/in_memory.py").read_text()
IDENTITY_MEMORY = (ROOT / "services/api/src/kefe_api/modules/identity/in_memory.py").read_text()
POSTGRES = (ROOT / "services/api/src/kefe_api/infrastructure/postgres_privacy.py").read_text()
MIGRATION = (
    ROOT / "services/api/migrations/versions/20260805_0029_privacy_self_service_hardening.py"
).read_text()
MOBILE_BOUNDARY = (
    ROOT / "apps/mobile/docs/privacy-self-service-cross-surface-boundary.md"
).read_text()

assert CONTRACT["source_issue"] == 312
assert CONTRACT["parent"]["exact_head"] == "4f31fb894c153b9bc5c90a5a0dc6fce534db04b8"
assert CONTRACT["primary_capability"] == "CAP-085"
assert CONTRACT["lifecycle_promotion"] is False
assert CONTRACT["export"]["schema_version"] == "privacy-export.v2"
assert CONTRACT["deletion"]["confirmation_format"] == "DELETE:<authenticated_actor_uuid>"
assert CONTRACT["deletion"]["one_receipt_per_actor"] is True
assert CONTRACT["export"]["payload_persistence_forbidden"] is True

for fragment in (
    "privacy-export.v2",
    "hashlib.sha256",
    "sort_keys=True",
    "separators=",
    "ensure_ascii=False",
    "hmac.compare_digest",
    "DELETE:{principal.actor_id}",
):
    assert fragment in SERVICE, fragment

for fragment in (
    "PrivacyExportManifestResponse",
    "schema_version=bundle.schema_version",
    "data_sha256=bundle.data_sha256",
    "actor_id=receipt.actor_id",
    "service.delete(principal, confirmation=confirm)",
):
    assert fragment in ROUTER, fragment

assert "self._receipts" in MEMORY
assert "with self._lock" in MEMORY
assert "PRIVACY_SELF_SERVICE_V2" in MEMORY
assert "account_actor_id != actor_id" in IDENTITY_MEMORY
assert "FOR UPDATE" in POSTGRES
assert "WHERE actor_id = :actor_id" in POSTGRES
assert "DELETE FROM identity.actor_merge" in POSTGRES
assert "merged_from_actor_id = NULL" in POSTGRES
assert "PRIVACY_SELF_SERVICE_V2" in POSTGRES
assert "CREATE UNIQUE INDEX privacy_actor_deletion_receipt_actor_uidx" in MIGRATION
assert "BEFORE UPDATE OR DELETE" in MIGRATION
assert "privacy deletion receipts are append-only" in MIGRATION

for forbidden in (
    "export_payload_table",
    "privacy_warehouse",
    "background_export",
    "ideology_score",
):
    assert forbidden not in (SERVICE + ROUTER + MEMORY + POSTGRES).lower(), forbidden

assert "no consumer/mobile write endpoint" in MOBILE_BOUNDARY.lower()
assert "not a production release" in MOBILE_BOUNDARY.lower()

print(
    "Privacy export/deletion contract: PASS — deterministic additive export, "
    "actor-bound confirmation, one append-only receipt, merge-link cleanup, "
    "and no parallel privacy data store."
)
