from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.models import ActorPrincipal
from kefe_api.modules.privacy.models import (
    PrivacyDeletionReceipt,
    PrivacyExport,
    PrivacyExportManifest,
)
from kefe_api.modules.privacy.ports import PrivacyRepository


class PrivacyService:
    POLICY_VERSION = "PRIVACY_SELF_SERVICE_V2"
    EXPORT_SCHEMA_VERSION = "privacy-export.v2"

    def __init__(self, repository: PrivacyRepository) -> None:
        self._repo = repository

    def export(self, principal: ActorPrincipal) -> PrivacyExport:
        product_data = self._repo.export_actor_data(principal.actor_id)
        retention: dict[str, Any] = {
            "guest_unclaimed_history_days": 30,
            "uncommitted_local_draft_days": 7,
            "security_telemetry": ("shortest necessary retention; excluded from this export"),
            "audit_exception": (
                "security/legal audit records may be retained without reusable profile data"
            ),
        }
        manifest = self._manifest(product_data)
        canonical = {
            "schema_version": self.EXPORT_SCHEMA_VERSION,
            "actor_id": str(principal.actor_id),
            "actor_kind": principal.actor_kind.value,
            "retention": retention,
            "manifest": {
                "dataset_counts": manifest.dataset_counts,
                "total_records": manifest.total_records,
                "empty_datasets": list(manifest.empty_datasets),
            },
            "product_data": product_data,
        }
        encoded = json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return PrivacyExport(
            schema_version=self.EXPORT_SCHEMA_VERSION,
            actor_id=principal.actor_id,
            actor_kind=principal.actor_kind.value,
            generated_at=datetime.now(UTC),
            retention=retention,
            manifest=manifest,
            product_data=product_data,
            data_sha256=hashlib.sha256(encoded).hexdigest(),
        )

    def delete(
        self,
        principal: ActorPrincipal,
        *,
        confirmation: str | None,
    ) -> PrivacyDeletionReceipt:
        expected = f"DELETE:{principal.actor_id}"
        if confirmation is None or not hmac.compare_digest(confirmation, expected):
            raise DomainError(
                "PRIVACY_DELETE_CONFIRMATION_REQUIRED",
                "Actor-bound deletion confirmation is required",
                422,
            )
        return self._repo.delete_actor_data(
            actor_id=principal.actor_id,
            actor_kind=principal.actor_kind.value,
            deleted_at=datetime.now(UTC),
        )

    @classmethod
    def _manifest(cls, product_data: dict[str, Any]) -> PrivacyExportManifest:
        counts = {name: cls._dataset_count(product_data[name]) for name in sorted(product_data)}
        return PrivacyExportManifest(
            dataset_counts=counts,
            total_records=sum(counts.values()),
            empty_datasets=tuple(name for name, count in counts.items() if count == 0),
        )

    @staticmethod
    def _dataset_count(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, (list, tuple, dict)):
            return len(value)
        return 1
