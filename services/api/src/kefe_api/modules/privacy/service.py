from __future__ import annotations

from datetime import UTC, datetime

from kefe_api.modules.identity.models import ActorPrincipal
from kefe_api.modules.privacy.models import PrivacyDeletionReceipt, PrivacyExport
from kefe_api.modules.privacy.ports import PrivacyRepository


class PrivacyService:
    POLICY_VERSION = "MVP_PRIVACY_V1"

    def __init__(self, repository: PrivacyRepository) -> None:
        self._repo = repository

    def export(self, principal: ActorPrincipal) -> PrivacyExport:
        now = datetime.now(UTC)
        return PrivacyExport(
            actor_id=principal.actor_id,
            actor_kind=principal.actor_kind.value,
            generated_at=now,
            retention={
                "guest_unclaimed_history_days": 30,
                "uncommitted_local_draft_days": 7,
                "security_telemetry": (
                    "shortest necessary retention; excluded from this export"
                ),
                "audit_exception": (
                    "security/legal audit records may be retained without reusable profile data"
                ),
            },
            product_data=self._repo.export_actor_data(principal.actor_id),
        )

    def delete(self, principal: ActorPrincipal) -> PrivacyDeletionReceipt:
        return self._repo.delete_actor_data(
            actor_id=principal.actor_id,
            actor_kind=principal.actor_kind.value,
            deleted_at=datetime.now(UTC),
        )
