from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
contract = json.loads(
    (ROOT / "docs/contracts/admin-case-media-asset-management.v1.json").read_text()
)
assert contract["capabilities"] == ["CAP-094", "CAP-126"]
assert contract["production_projection"]["preview_fallback_forbidden"] is True
assert contract["admin_ui"]["no_binary_file_input"] is True

service = (ROOT / "services/api/src/kefe_api/modules/case_media/service.py").read_text()
router = (
    ROOT / "services/api/src/kefe_api/modules/admin_security/case_media_router.py"
).read_text()
main = (ROOT / "services/api/src/kefe_api/main.py").read_text()
for forbidden in ("preview_case_media", "assets/media/", "UploadFile", "multipart"):
    assert forbidden not in service
    assert forbidden not in router
assert "build_case_media_repository" in main
assert "admin_case_media_router" in main
assert (
    "MEDIA_ASSET_MANAGE"
    in (ROOT / "services/api/src/kefe_api/modules/admin_security/policy.py").read_text()
)
print("Admin Case Media contract: PASS")
