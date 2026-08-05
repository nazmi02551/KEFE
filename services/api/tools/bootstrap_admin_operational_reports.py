from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[3]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    content = target.read_text()
    if old not in content:
        raise RuntimeError(f"expected snippet not found in {path}: {old[:120]!r}")
    target.write_text(content.replace(old, new, 1))


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dedent(content).lstrip())


replace_once(
    "services/api/src/kefe_api/modules/content_authoring/ports.py",
    """    def next_version_no(self, case_id: UUID) -> int: ...\n""",
    """    def count_by_state(self, state: ContentLifecycle) -> int: ...\n\n    def next_version_no(self, case_id: UUID) -> int: ...\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/content_authoring/in_memory.py",
    """            return tuple(versions[offset : offset + limit])\n\n    def next_version_no(self, case_id: UUID) -> int:\n""",
    """            return tuple(versions[offset : offset + limit])\n\n    def count_by_state(self, state: ContentLifecycle) -> int:\n        with self._lock:\n            return sum(\n                1 for version in self._versions.values() if version.state is state\n            )\n\n    def next_version_no(self, case_id: UUID) -> int:\n""",
)

replace_once(
    "services/api/src/kefe_api/infrastructure/postgres_flow_pinned_content_authoring.py",
    """        return tuple(self._version_from_row(row) for row in rows)\n\n    def _materialize_consumer(\n""",
    """        return tuple(self._version_from_row(row) for row in rows)\n\n    def count_by_state(self, state: ContentLifecycle) -> int:\n        with self._engine.connect() as connection:\n            value = connection.execute(\n                text(\n                    \"\"\"\n                    SELECT count(*)\n                    FROM editorial.case_version\n                    WHERE lifecycle_state = :state\n                    \"\"\"\n                ),\n                {\"state\": state.value},\n            ).scalar_one()\n        return int(value)\n\n    def _materialize_consumer(\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/review_queue.py",
    """@dataclass(frozen=True, slots=True)\nclass ProposalQueueRecord:\n""",
    """@dataclass(frozen=True, slots=True)\nclass ProposalQueueCountQuery:\n    review_state: ProposalQueueReviewState | None = None\n    proposal_kind: str | None = None\n    risk_code: str | None = None\n    run_id: UUID | None = None\n    pipeline_code: str | None = None\n\n    def __post_init__(self) -> None:\n        for value, field_name in (\n            (self.proposal_kind, \"proposal_kind\"),\n            (self.risk_code, \"risk_code\"),\n            (self.pipeline_code, \"pipeline_code\"),\n        ):\n            if value is not None and not value.strip():\n                raise ValueError(f\"{field_name} must not be blank\")\n\n\n@dataclass(frozen=True, slots=True)\nclass ProposalQueueRecord:\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/ports.py",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n)\n""",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueCountQuery,\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n)\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/ports.py",
    """    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None: ...\n""",
    """    def count_proposal_queue(self, query: ProposalQueueCountQuery) -> int: ...\n\n    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None: ...\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/in_memory.py",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n)\n""",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueCountQuery,\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n)\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/in_memory.py",
    """    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None:\n""",
    """    def count_proposal_queue(self, query: ProposalQueueCountQuery) -> int:\n        with self._lock:\n            return sum(\n                1\n                for proposal in self._proposals.values()\n                if self._matches_count_query(\n                    ProposalQueueRecord(\n                        proposal=proposal,\n                        run=self._runs[proposal.run_id],\n                        review=self._review_decisions.get(proposal.id),\n                    ),\n                    query,\n                )\n            )\n\n    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None:\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/in_memory.py",
    """        proposal = record.proposal\n        run = record.run\n        if query.review_state is not None and record.review_state != query.review_state:\n            return False\n""",
    """        if not InMemoryIngestionOrchestrationRepository._matches_count_query(\n            record,\n            ProposalQueueCountQuery(\n                review_state=query.review_state,\n                proposal_kind=query.proposal_kind,\n                risk_code=query.risk_code,\n                run_id=query.run_id,\n                pipeline_code=query.pipeline_code,\n            ),\n        ):\n            return False\n        proposal = record.proposal\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/in_memory.py",
    """        if query.pipeline_code is not None and run.pipeline_code != query.pipeline_code:\n            return False\n        if query.after_created_at is not None:\n""",
    """        if query.after_created_at is not None:\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/ingestion_orchestration/in_memory.py",
    """        return True\n\n    def _validate_stage_execution_available(self, execution: StageExecution) -> None:\n""",
    """        return True\n\n    @staticmethod\n    def _matches_count_query(\n        record: ProposalQueueRecord,\n        query: ProposalQueueCountQuery,\n    ) -> bool:\n        proposal = record.proposal\n        run = record.run\n        if query.review_state is not None and record.review_state != query.review_state:\n            return False\n        if query.proposal_kind is not None and proposal.proposal_kind != query.proposal_kind:\n            return False\n        if query.risk_code is not None and proposal.risk_code != query.risk_code:\n            return False\n        if query.run_id is not None and proposal.run_id != query.run_id:\n            return False\n        if query.pipeline_code is not None and run.pipeline_code != query.pipeline_code:\n            return False\n        return True\n\n    def _validate_stage_execution_available(self, execution: StageExecution) -> None:\n""",
)

replace_once(
    "services/api/src/kefe_api/infrastructure/postgres_proposal_review_queue.py",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n    ProposalQueueReviewState,\n)\n""",
    """from kefe_api.modules.ingestion_orchestration.review_queue import (\n    ProposalQueueCountQuery,\n    ProposalQueueQuery,\n    ProposalQueueRecord,\n    ProposalQueueReviewState,\n)\n""",
)
replace_once(
    "services/api/src/kefe_api/infrastructure/postgres_proposal_review_queue.py",
    """    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None:\n""",
    """    def count_proposal_queue(self, query: ProposalQueueCountQuery) -> int:\n        clauses: list[str] = []\n        params: dict[str, object] = {}\n        if query.review_state is ProposalQueueReviewState.PENDING:\n            clauses.append(\"rd.id IS NULL\")\n        elif query.review_state is not None:\n            clauses.append(\"rd.decision = :review_state\")\n            params[\"review_state\"] = query.review_state.value\n        if query.proposal_kind is not None:\n            clauses.append(\"p.proposal_kind = :proposal_kind\")\n            params[\"proposal_kind\"] = query.proposal_kind\n        if query.risk_code is not None:\n            clauses.append(\"p.risk_code = :risk_code\")\n            params[\"risk_code\"] = query.risk_code\n        if query.run_id is not None:\n            clauses.append(\"p.run_id = :run_id\")\n            params[\"run_id\"] = query.run_id\n        if query.pipeline_code is not None:\n            clauses.append(\"ir.pipeline_code = :pipeline_code\")\n            params[\"pipeline_code\"] = query.pipeline_code\n\n        statement = \"\"\"\n            SELECT count(*)\n            FROM ingestion.proposal p\n            JOIN ingestion.ingestion_run ir ON ir.id = p.run_id\n            LEFT JOIN ingestion.proposal_review_decision rd ON rd.proposal_id = p.id\n        \"\"\"\n        if clauses:\n            statement += \" WHERE \" + \" AND \".join(clauses)\n        with self._engine.connect() as connection:\n            value = connection.execute(text(statement), params).scalar_one()\n        return int(value)\n\n    def get_proposal_queue_record(\n        self,\n        proposal_id: UUID,\n    ) -> ProposalQueueRecord | None:\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/community_reason/ports.py",
    """    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None: ...\n""",
    """    def count_moderation_queue(\n        self,\n        *,\n        kind: CommunityReasonModerationQueueKind,\n        case_version_id: UUID | None = None,\n        report_code: ReasonReportCode | None = None,\n    ) -> int: ...\n\n    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None: ...\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/community_reason/in_memory.py",
    """    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None:\n""",
    """    def count_moderation_queue(\n        self,\n        *,\n        kind: CommunityReasonModerationQueueKind,\n        case_version_id: UUID | None = None,\n        report_code: ReasonReportCode | None = None,\n    ) -> int:\n        return len(\n            self.moderation_queue(\n                kind=kind,\n                limit=max(len(self._reasons), 1),\n                offset=0,\n                case_version_id=case_version_id,\n                report_code=report_code,\n            )\n        )\n\n    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None:\n""",
)
replace_once(
    "services/api/src/kefe_api/infrastructure/postgres_community_reason.py",
    """    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None:\n""",
    """    def count_moderation_queue(\n        self,\n        *,\n        kind: CommunityReasonModerationQueueKind,\n        case_version_id: UUID | None = None,\n        report_code: ReasonReportCode | None = None,\n    ) -> int:\n        candidate_query = (\n            _MODERATION_SELECT\n            + \"\"\"\n            WHERE (\n                (:kind = 'PENDING' AND r.moderation_state = 'PENDING')\n                OR (\n                    :kind = 'REPORTED'\n                    AND r.moderation_state IN ('NOT_REQUIRED', 'ALLOWED')\n                    AND rs.latest_reported_at IS NOT NULL\n                    AND (\n                        la.latest_audit_at IS NULL\n                        OR rs.latest_reported_at > la.latest_audit_at\n                    )\n                )\n            )\n              AND (\n                CAST(:case_version_id AS uuid) IS NULL\n                OR r.case_version_id = CAST(:case_version_id AS uuid)\n              )\n              AND (\n                CAST(:report_code AS text) IS NULL\n                OR EXISTS (\n                    SELECT 1\n                    FROM community.reason_report filtered_report\n                    WHERE filtered_report.reason_id = r.id\n                      AND filtered_report.report_code = CAST(:report_code AS text)\n                )\n              )\n            \"\"\"\n        )\n        with self._engine.connect() as connection:\n            value = connection.execute(\n                text(f\"SELECT count(*) FROM ({candidate_query}) candidates\"),\n                {\n                    \"kind\": kind.value,\n                    \"case_version_id\": case_version_id,\n                    \"report_code\": (\n                        report_code.value if report_code is not None else None\n                    ),\n                },\n            ).scalar_one()\n        return int(value)\n\n    def moderation_inspection(\n        self,\n        reason_id: UUID,\n    ) -> CommunityReasonModerationItem | None:\n""",
)

replace_once(
    "services/api/src/kefe_api/modules/admin_security/models.py",
    """    AUDIT_READ = \"AUDIT_READ\"\n""",
    """    AUDIT_READ = \"AUDIT_READ\"\n    OPERATIONAL_REPORT_READ = \"OPERATIONAL_REPORT_READ\"\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/admin_security/policy.py",
    """                    AdminCapability.AUDIT_READ,\n                }\n            ),\n            AdminRole.PUBLISHER: frozenset(\n""",
    """                    AdminCapability.AUDIT_READ,\n                    AdminCapability.OPERATIONAL_REPORT_READ,\n                }\n            ),\n            AdminRole.PUBLISHER: frozenset(\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/admin_security/policy.py",
    """                    AdminCapability.CONTENT_WITHDRAW,\n                    AdminCapability.AUDIT_READ,\n                }\n            ),\n""",
    """                    AdminCapability.CONTENT_WITHDRAW,\n                    AdminCapability.AUDIT_READ,\n                    AdminCapability.OPERATIONAL_REPORT_READ,\n                }\n            ),\n""",
)
replace_once(
    "services/api/src/kefe_api/modules/admin_security/policy.py",
    """                    AdminCapability.SOURCE_ACTIVATE,\n                    AdminCapability.AUDIT_READ,\n                }\n            ),\n""",
    """                    AdminCapability.SOURCE_ACTIVATE,\n                    AdminCapability.AUDIT_READ,\n                    AdminCapability.OPERATIONAL_REPORT_READ,\n                }\n            ),\n""",
)

write(
    "services/api/src/kefe_api/modules/admin_operational_reports/__init__.py",
    """
    \"\"\"Privacy-safe aggregate Admin operational reporting.\"\"\"
    """,
)
write(
    "services/api/src/kefe_api/modules/admin_operational_reports/models.py",
    """
    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import UTC, datetime
    from enum import StrEnum
    from types import MappingProxyType
    from typing import Mapping

    from kefe_api.modules.content_supply_health.models import (
        ContentSupplyHealthPolicy,
        ContentSupplyHealthSnapshot,
    )


    def _require_utc(value: datetime, field_name: str) -> None:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be timezone-aware UTC")


    class AdminOperationalSignal(StrEnum):
        QUIET = "QUIET"
        NOMINAL = "NOMINAL"
        ATTENTION = "ATTENTION"
        CRITICAL = "CRITICAL"


    class AdminOperationalReason(StrEnum):
        CONTENT_SUPPLY_ATTENTION = "CONTENT_SUPPLY_ATTENTION"
        CONTENT_SUPPLY_CRITICAL = "CONTENT_SUPPLY_CRITICAL"
        EDITORIAL_IN_REVIEW_BACKLOG = "EDITORIAL_IN_REVIEW_BACKLOG"
        PROPOSAL_REVIEW_BACKLOG = "PROPOSAL_REVIEW_BACKLOG"
        MODERATION_BACKLOG = "MODERATION_BACKLOG"


    @dataclass(frozen=True, slots=True)
    class AdminOperationalReportPolicy:
        in_review_attention_threshold: int = 50
        pending_proposal_attention_threshold: int = 100
        moderation_candidate_attention_threshold: int = 50
        content_supply: ContentSupplyHealthPolicy = field(
            default_factory=ContentSupplyHealthPolicy
        )

        def __post_init__(self) -> None:
            for value, name in (
                (self.in_review_attention_threshold, "in_review_attention_threshold"),
                (
                    self.pending_proposal_attention_threshold,
                    "pending_proposal_attention_threshold",
                ),
                (
                    self.moderation_candidate_attention_threshold,
                    "moderation_candidate_attention_threshold",
                ),
            ):
                if value < 0 or value > 1_000_000:
                    raise ValueError(f"{name} is outside the supported range")


    @dataclass(frozen=True, slots=True)
    class AdminOperationalReportSnapshot:
        as_of: datetime
        overall_signal: AdminOperationalSignal
        reason_codes: tuple[str, ...]
        policy: AdminOperationalReportPolicy
        content_supply: ContentSupplyHealthSnapshot
        editorial_lifecycle: Mapping[str, int]
        proposal_review: Mapping[str, int]
        moderation: Mapping[str, int]

        def __post_init__(self) -> None:
            _require_utc(self.as_of, "as_of")
            if self.content_supply.as_of != self.as_of:
                raise ValueError("content supply snapshot must share report as_of")
            if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
                raise ValueError("reason_codes must be sorted and unique")
            for section in (
                self.editorial_lifecycle,
                self.proposal_review,
                self.moderation,
            ):
                if any(value < 0 for value in section.values()):
                    raise ValueError("operational report counts must be non-negative")

        @staticmethod
        def immutable_counts(values: dict[str, int]) -> Mapping[str, int]:
            return MappingProxyType(dict(values))
    """,
)
write(
    "services/api/src/kefe_api/modules/admin_operational_reports/service.py",
    """
    from __future__ import annotations

    from kefe_api.modules.admin_operational_reports.models import (
        AdminOperationalReason,
        AdminOperationalReportPolicy,
        AdminOperationalReportSnapshot,
        AdminOperationalSignal,
    )
    from kefe_api.modules.community_reason.models import (
        CommunityReasonModerationQueueKind,
    )
    from kefe_api.modules.community_reason.ports import CommunityReasonRepository
    from kefe_api.modules.content_authoring.models import ContentLifecycle
    from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
    from kefe_api.modules.content_supply_health.models import ContentSupplyHealthSignal
    from kefe_api.modules.content_supply_health.service import ContentSupplyHealthService
    from kefe_api.modules.ingestion_orchestration.models import utcnow
    from kefe_api.modules.ingestion_orchestration.ports import (
        ProposalReviewQueueRepository,
    )
    from kefe_api.modules.ingestion_orchestration.review_queue import (
        ProposalQueueCountQuery,
        ProposalQueueReviewState,
    )


    class AdminOperationalReportsService:
        def __init__(
            self,
            *,
            content_supply: ContentSupplyHealthService,
            content_authoring: ContentAuthoringRepository,
            proposal_review: ProposalReviewQueueRepository,
            community_reason: CommunityReasonRepository,
            clock=utcnow,
        ) -> None:
            self._content_supply = content_supply
            self._content_authoring = content_authoring
            self._proposal_review = proposal_review
            self._community_reason = community_reason
            self._clock = clock

        def snapshot(
            self,
            policy: AdminOperationalReportPolicy | None = None,
        ) -> AdminOperationalReportSnapshot:
            resolved_policy = policy or AdminOperationalReportPolicy()
            as_of = self._clock()
            content_supply = self._content_supply.snapshot(
                resolved_policy.content_supply,
                as_of=as_of,
            )
            editorial = {
                state.value: self._content_authoring.count_by_state(state)
                for state in ContentLifecycle
            }
            proposals = {
                state.value: self._proposal_review.count_proposal_queue(
                    ProposalQueueCountQuery(review_state=state)
                )
                for state in ProposalQueueReviewState
            }
            moderation = {
                kind.value: self._community_reason.count_moderation_queue(kind=kind)
                for kind in CommunityReasonModerationQueueKind
            }
            reasons = self._reason_codes(
                content_supply_signal=content_supply.signal,
                editorial=editorial,
                proposals=proposals,
                moderation=moderation,
                policy=resolved_policy,
            )
            signal = self._signal(
                content_supply_signal=content_supply.signal,
                reasons=reasons,
                editorial=editorial,
                proposals=proposals,
                moderation=moderation,
            )
            return AdminOperationalReportSnapshot(
                as_of=as_of,
                overall_signal=signal,
                reason_codes=tuple(sorted(reasons)),
                policy=resolved_policy,
                content_supply=content_supply,
                editorial_lifecycle=AdminOperationalReportSnapshot.immutable_counts(
                    editorial
                ),
                proposal_review=AdminOperationalReportSnapshot.immutable_counts(
                    proposals
                ),
                moderation=AdminOperationalReportSnapshot.immutable_counts(moderation),
            )

        @staticmethod
        def _reason_codes(
            *,
            content_supply_signal: ContentSupplyHealthSignal,
            editorial: dict[str, int],
            proposals: dict[str, int],
            moderation: dict[str, int],
            policy: AdminOperationalReportPolicy,
        ) -> set[str]:
            reasons: set[str] = set()
            if content_supply_signal is ContentSupplyHealthSignal.CRITICAL:
                reasons.add(AdminOperationalReason.CONTENT_SUPPLY_CRITICAL.value)
            elif content_supply_signal is ContentSupplyHealthSignal.ATTENTION:
                reasons.add(AdminOperationalReason.CONTENT_SUPPLY_ATTENTION.value)
            if (
                editorial[ContentLifecycle.IN_REVIEW.value]
                > policy.in_review_attention_threshold
            ):
                reasons.add(
                    AdminOperationalReason.EDITORIAL_IN_REVIEW_BACKLOG.value
                )
            if (
                proposals[ProposalQueueReviewState.PENDING.value]
                > policy.pending_proposal_attention_threshold
            ):
                reasons.add(AdminOperationalReason.PROPOSAL_REVIEW_BACKLOG.value)
            moderation_total = sum(moderation.values())
            if moderation_total > policy.moderation_candidate_attention_threshold:
                reasons.add(AdminOperationalReason.MODERATION_BACKLOG.value)
            return reasons

        @staticmethod
        def _signal(
            *,
            content_supply_signal: ContentSupplyHealthSignal,
            reasons: set[str],
            editorial: dict[str, int],
            proposals: dict[str, int],
            moderation: dict[str, int],
        ) -> AdminOperationalSignal:
            if content_supply_signal is ContentSupplyHealthSignal.CRITICAL:
                return AdminOperationalSignal.CRITICAL
            if reasons:
                return AdminOperationalSignal.ATTENTION
            backlog = (
                sum(editorial.values())
                + sum(proposals.values())
                + sum(moderation.values())
            )
            if content_supply_signal is ContentSupplyHealthSignal.QUIET and backlog == 0:
                return AdminOperationalSignal.QUIET
            return AdminOperationalSignal.NOMINAL
    """,
)
write(
    "services/api/src/kefe_api/modules/admin_security/operational_reports.py",
    """
    from __future__ import annotations

    from kefe_api.modules.admin_operational_reports.models import (
        AdminOperationalReportSnapshot,
    )
    from kefe_api.modules.admin_operational_reports.service import (
        AdminOperationalReportsService,
    )
    from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
    from kefe_api.modules.admin_security.service import AdminSecurityService


    class SecuredAdminOperationalReportsService:
        def __init__(
            self,
            *,
            reports: AdminOperationalReportsService,
            security: AdminSecurityService,
        ) -> None:
            self._reports = reports
            self._security = security

        def snapshot(
            self,
            principal: AdminPrincipal,
        ) -> AdminOperationalReportSnapshot:
            self._security.authorize(
                principal,
                AdminCapability.OPERATIONAL_REPORT_READ,
            )
            return self._reports.snapshot()
    """,
)
write(
    "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py",
    """
    from __future__ import annotations

    from datetime import datetime
    from typing import Annotated

    from fastapi import APIRouter, Depends, Request
    from pydantic import BaseModel, ConfigDict

    from kefe_api.modules.admin_operational_reports.models import (
        AdminOperationalReportSnapshot,
    )
    from kefe_api.modules.admin_security.operational_reports import (
        SecuredAdminOperationalReportsService,
    )
    from kefe_api.modules.admin_security.router import ReadPrincipalDep

    router = APIRouter(
        prefix="/internal/admin/v1/operational-reports",
        tags=["Internal Admin Operational Reports"],
    )


    class StrictModel(BaseModel):
        model_config = ConfigDict(extra="forbid")


    class OperationalThresholdsResponse(StrictModel):
        in_review_attention_threshold: int
        pending_proposal_attention_threshold: int
        moderation_candidate_attention_threshold: int


    class ContentSupplyPolicyResponse(StrictModel):
        pending_dispatch_attention_threshold: int
        queued_run_attention_threshold: int
        unreviewed_proposal_attention_threshold: int
        recent_non_success_attention_threshold: int
        max_cycle_silence_seconds: int
        failure_window_seconds: int


    class ContentSupplySnapshotResponse(StrictModel):
        signal: str
        as_of: datetime
        reason_codes: list[str]
        active_schedule_count: int
        paused_schedule_count: int
        due_schedule_count: int
        pending_dispatch_count: int
        running_dispatch_count: int
        stale_dispatch_count: int
        recent_dispatch_non_success_count: int
        queued_ingestion_run_count: int
        running_ingestion_run_count: int
        stale_ingestion_lease_count: int
        recent_failed_ingestion_run_count: int
        unreviewed_proposal_count: int
        running_cycle_count: int
        stale_cycle_count: int
        recent_non_success_cycle_count: int
        latest_terminal_cycle_state: str | None
        latest_terminal_cycle_completed_at: datetime | None
        seconds_since_latest_terminal_cycle: int | None


    class OperationalReportsSnapshotResponse(StrictModel):
        as_of: datetime
        overall_signal: str
        reason_codes: list[str]
        thresholds: OperationalThresholdsResponse
        content_supply_policy: ContentSupplyPolicyResponse
        content_supply: ContentSupplySnapshotResponse
        editorial_lifecycle: dict[str, int]
        proposal_review: dict[str, int]
        moderation: dict[str, int]
        aggregate_only: bool = True


    def get_reports(request: Request) -> SecuredAdminOperationalReportsService:
        return request.app.state.secured_admin_operational_reports_service


    ReportsDep = Annotated[
        SecuredAdminOperationalReportsService,
        Depends(get_reports),
    ]


    @router.get("/snapshot", response_model=OperationalReportsSnapshotResponse)
    def operational_reports_snapshot(
        principal: ReadPrincipalDep,
        reports: ReportsDep,
    ) -> OperationalReportsSnapshotResponse:
        return _response(reports.snapshot(principal))


    def _response(
        snapshot: AdminOperationalReportSnapshot,
    ) -> OperationalReportsSnapshotResponse:
        supply = snapshot.content_supply
        policy = snapshot.policy
        supply_policy = policy.content_supply
        return OperationalReportsSnapshotResponse(
            as_of=snapshot.as_of,
            overall_signal=snapshot.overall_signal.value,
            reason_codes=list(snapshot.reason_codes),
            thresholds=OperationalThresholdsResponse(
                in_review_attention_threshold=policy.in_review_attention_threshold,
                pending_proposal_attention_threshold=(
                    policy.pending_proposal_attention_threshold
                ),
                moderation_candidate_attention_threshold=(
                    policy.moderation_candidate_attention_threshold
                ),
            ),
            content_supply_policy=ContentSupplyPolicyResponse(
                pending_dispatch_attention_threshold=(
                    supply_policy.pending_dispatch_attention_threshold
                ),
                queued_run_attention_threshold=(
                    supply_policy.queued_run_attention_threshold
                ),
                unreviewed_proposal_attention_threshold=(
                    supply_policy.unreviewed_proposal_attention_threshold
                ),
                recent_non_success_attention_threshold=(
                    supply_policy.recent_non_success_attention_threshold
                ),
                max_cycle_silence_seconds=supply_policy.max_cycle_silence_seconds,
                failure_window_seconds=supply_policy.failure_window_seconds,
            ),
            content_supply=ContentSupplySnapshotResponse(
                signal=supply.signal.value,
                as_of=supply.as_of,
                reason_codes=list(supply.reason_codes),
                active_schedule_count=supply.active_schedule_count,
                paused_schedule_count=supply.paused_schedule_count,
                due_schedule_count=supply.due_schedule_count,
                pending_dispatch_count=supply.pending_dispatch_count,
                running_dispatch_count=supply.running_dispatch_count,
                stale_dispatch_count=supply.stale_dispatch_count,
                recent_dispatch_non_success_count=(
                    supply.recent_dispatch_non_success_count
                ),
                queued_ingestion_run_count=supply.queued_ingestion_run_count,
                running_ingestion_run_count=supply.running_ingestion_run_count,
                stale_ingestion_lease_count=supply.stale_ingestion_lease_count,
                recent_failed_ingestion_run_count=(
                    supply.recent_failed_ingestion_run_count
                ),
                unreviewed_proposal_count=supply.unreviewed_proposal_count,
                running_cycle_count=supply.running_cycle_count,
                stale_cycle_count=supply.stale_cycle_count,
                recent_non_success_cycle_count=(
                    supply.recent_non_success_cycle_count
                ),
                latest_terminal_cycle_state=supply.latest_terminal_cycle_state,
                latest_terminal_cycle_completed_at=(
                    supply.latest_terminal_cycle_completed_at
                ),
                seconds_since_latest_terminal_cycle=(
                    supply.seconds_since_latest_terminal_cycle
                ),
            ),
            editorial_lifecycle=dict(snapshot.editorial_lifecycle),
            proposal_review=dict(snapshot.proposal_review),
            moderation=dict(snapshot.moderation),
        )
    """,
)

replace_once(
    "services/api/src/kefe_api/main.py",
    """from kefe_api.modules.admin_security.policy import default_admin_security_policy\n""",
    """from kefe_api.modules.admin_security.operational_reports import (\n    SecuredAdminOperationalReportsService,\n)\nfrom kefe_api.modules.admin_security.operational_reports_router import (\n    router as admin_operational_reports_router,\n)\nfrom kefe_api.modules.admin_security.policy import default_admin_security_policy\n""",
)
replace_once(
    "services/api/src/kefe_api/main.py",
    """from kefe_api.modules.community_reason.service import CommunityReasonService\n""",
    """from kefe_api.modules.admin_operational_reports.service import (\n    AdminOperationalReportsService,\n)\nfrom kefe_api.modules.community_reason.service import CommunityReasonService\n""",
)
replace_once(
    "services/api/src/kefe_api/main.py",
    """    canonical_public_feed = build_canonical_public_feed_composition(\n        settings,\n        admin_security_service=admin_security_service,\n        editorial_pipeline=editorial_pipeline,\n    )\n    content_configuration_service = ContentConfigurationService(\n""",
    """    canonical_public_feed = build_canonical_public_feed_composition(\n        settings,\n        admin_security_service=admin_security_service,\n        editorial_pipeline=editorial_pipeline,\n    )\n    admin_operational_reports_service = AdminOperationalReportsService(\n        content_supply=editorial_pipeline.content_supply_health_service,\n        content_authoring=content_authoring_repository,\n        proposal_review=editorial_pipeline.proposal_queue_repository,\n        community_reason=community_reason_repository,\n    )\n    secured_admin_operational_reports_service = (\n        SecuredAdminOperationalReportsService(\n            reports=admin_operational_reports_service,\n            security=admin_security_service,\n        )\n    )\n    content_configuration_service = ContentConfigurationService(\n""",
)
replace_once(
    "services/api/src/kefe_api/main.py",
    """    app.state.secured_content_configuration_service = secured_content_configuration_service\n""",
    """    app.state.secured_content_configuration_service = secured_content_configuration_service\n    app.state.admin_operational_reports_service = admin_operational_reports_service\n    app.state.secured_admin_operational_reports_service = (\n        secured_admin_operational_reports_service\n    )\n""",
)
replace_once(
    "services/api/src/kefe_api/main.py",
    """    app.include_router(admin_content_configuration_router)\n    app.include_router(community_reason_admin_router)\n""",
    """    app.include_router(admin_content_configuration_router)\n    app.include_router(community_reason_admin_router)\n    app.include_router(admin_operational_reports_router)\n""",
)

write(
    "services/api/tests/test_admin_operational_reports_http.py",
    """
    from __future__ import annotations

    from datetime import UTC, datetime, timedelta
    from uuid import UUID, uuid4

    from fastapi.testclient import TestClient

    from kefe_api.main import create_app
    from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
    from kefe_api.modules.admin_security.models import AdminRole
    from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
    from kefe_api.modules.community_reason.models import (
        CommunityReason,
        CommunityReasonModeration,
        ReasonReportCode,
    )
    from kefe_api.modules.content_authoring.models import (
        AuthoringCaseVersion,
        CaseIdentity,
        ContentLifecycle,
        LifecycleAuditEntry,
    )
    from kefe_api.modules.ingestion_orchestration.models import (
        ExecutorKind,
        IngestionRun,
        IngestionRunState,
        InputArtifactKind,
        Proposal,
        ProposalReviewDecision,
        ProposalReviewDecisionKind,
        StageExecution,
        StageOutcome,
        stable_payload_hash,
    )

    ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


    def _issue_admin(app, role: AdminRole) -> TestClient:
        store = app.state.admin_session_store
        assert isinstance(store, InMemoryAdminSessionStore)
        subject_id = uuid4()
        store.upsert_subject(subject_id, roles=frozenset({role}))
        now = datetime.now(UTC)
        issued = store.issue(
            admin_subject_id=subject_id,
            authenticated_at=now,
            mfa_satisfied_at=now,
            expires_at=now + timedelta(hours=12),
        )
        client = TestClient(app)
        client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
        return client


    def _seed_case_state(app, state: ContentLifecycle) -> None:
        case_id = uuid4()
        version = AuthoringCaseVersion(
            id=uuid4(),
            case_id=case_id,
            version_no=1,
            state=state,
            title="Operational aggregate fixture",
            summary="Aggregate-only lifecycle count fixture.",
            base_format_code="DILEMMA",
            primary_domain_code="DAILY_LIFE",
            content_risk="L0",
            issues=(),
        )
        app.state.content_authoring_repository.create_case(
            identity=CaseIdentity(id=case_id, slug=f"report-{state.value.lower()}-{case_id.hex}"),
            initial_version=version,
            audit=LifecycleAuditEntry.create(
                version=version,
                actor_ref="test:operational-report",
                command="seed",
                previous_state=None,
                new_state=state,
            ),
        )


    def _seed_proposal(app, decision: ProposalReviewDecisionKind | None) -> None:
        repository = app.state.ingestion_orchestration_repository
        now = datetime.now(UTC)
        run_id = uuid4()
        artifact_id = uuid4()
        stage_id = uuid4()
        proposal_id = uuid4()
        run = IngestionRun(
            id=run_id,
            run_key=f"operational-report-{run_id}",
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=artifact_id,
            input_content_hash="a" * 64,
            pipeline_code="OPERATIONAL_REPORT_TEST",
            pipeline_version="1",
            configuration_hash="b" * 64,
            state=IngestionRunState.RUNNING,
            created_at=now,
            updated_at=now,
        )
        repository.create_or_get_run(run)
        stage = StageExecution(
            id=stage_id,
            run_id=run_id,
            stage_code="PROPOSE",
            stage_version="1",
            attempt_no=1,
            max_attempts=1,
            executor_kind=ExecutorKind.DETERMINISTIC,
            input_hash="c" * 64,
            started_at=now,
            outcome=StageOutcome.SUCCEEDED,
            output_hash="d" * 64,
            completed_at=now,
        )
        repository.add_stage_execution(stage)
        payload = {"fixture": decision.value if decision is not None else "PENDING"}
        proposal = Proposal(
            id=proposal_id,
            proposal_kind="CASE_CANDIDATE",
            payload_schema_ref="urn:kefe:test:operational-report",
            payload_schema_version="1",
            payload=payload,
            payload_hash=stable_payload_hash(payload),
            run_id=run_id,
            stage_execution_id=stage_id,
            created_at=now,
            risk_code="L0",
        )
        repository.add_proposal(proposal)
        if decision is not None:
            repository.add_review_decision(
                ProposalReviewDecision(
                    id=uuid4(),
                    proposal_id=proposal_id,
                    decision=decision,
                    reviewer_ref="test:reviewer",
                    decided_at=now,
                )
            )


    def _seed_reason(app, state: CommunityReasonModeration, *, reported: bool) -> UUID:
        now = datetime.now(UTC)
        reason = CommunityReason(
            id=uuid4(),
            actor_id=uuid4(),
            session_id=uuid4(),
            case_version_id=uuid4(),
            tags=("FAIRNESS",),
            body="Aggregate fixture" if state is CommunityReasonModeration.PENDING else None,
            moderation_state=state,
            created_at=now,
            updated_at=now,
        )
        app.state.community_reason_repository.create_or_replace(reason)
        if reported:
            app.state.community_reason_repository.report(
                report_id=uuid4(),
                reason_id=reason.id,
                reporter_actor_id=uuid4(),
                report_code=ReasonReportCode.PERSONAL_DATA,
                created_at=now + timedelta(seconds=1),
            )
        return reason.id


    def test_snapshot_requires_dedicated_capability_and_no_csrf_or_step_up() -> None:
        app = create_app()
        editor = _issue_admin(app, AdminRole.EDITOR)
        denied = editor.get(ENDPOINT)
        assert denied.status_code == 403
        assert denied.json()["code"] == "ADMIN_FORBIDDEN"
        assert denied.json()["meta"]["required_capability"] == (
            "OPERATIONAL_REPORT_READ"
        )

        for role in (AdminRole.REVIEWER, AdminRole.PUBLISHER, AdminRole.ACCESS_ADMIN):
            client = _issue_admin(app, role)
            response = client.get(ENDPOINT)
            assert response.status_code == 200

        assert editor.post(ENDPOINT).status_code == 405
        assert editor.put(ENDPOINT).status_code == 405
        assert editor.delete(ENDPOINT).status_code == 405


    def test_snapshot_uses_authoritative_aggregate_counts_and_is_privacy_safe() -> None:
        app = create_app()
        for state in ContentLifecycle:
            _seed_case_state(app, state)
        _seed_proposal(app, None)
        _seed_proposal(app, ProposalReviewDecisionKind.ACCEPTED)
        _seed_proposal(app, ProposalReviewDecisionKind.REJECTED)
        _seed_proposal(app, ProposalReviewDecisionKind.CHANGES_REQUESTED)
        _seed_reason(app, CommunityReasonModeration.PENDING, reported=False)
        _seed_reason(app, CommunityReasonModeration.NOT_REQUIRED, reported=True)
        _seed_reason(app, CommunityReasonModeration.BLOCKED, reported=True)

        reviewer = _issue_admin(app, AdminRole.REVIEWER)
        before_audit = list(app.state.community_reason_repository._audits)
        response = reviewer.get(ENDPOINT)
        assert response.status_code == 200
        body = response.json()
        assert body["aggregate_only"] is True
        assert set(body["editorial_lifecycle"]) == {state.value for state in ContentLifecycle}
        assert set(body["editorial_lifecycle"].values()) == {1}
        assert body["proposal_review"] == {
            "PENDING": 1,
            "ACCEPTED": 1,
            "REJECTED": 1,
            "CHANGES_REQUESTED": 1,
        }
        assert body["moderation"] == {"PENDING": 1, "REPORTED": 1}
        assert body["as_of"] == body["content_supply"]["as_of"]
        assert body["thresholds"] == {
            "in_review_attention_threshold": 50,
            "pending_proposal_attention_threshold": 100,
            "moderation_candidate_attention_threshold": 50,
        }
        assert list(app.state.community_reason_repository._audits) == before_audit

        rendered = str(body).lower()
        for forbidden in (
            "case_id",
            "case_version_id",
            "proposal_id",
            "reason_id",
            "actor_id",
            "reporter_actor_id",
            "session_id",
            "reason_body",
            "rationale",
            "source_locator",
            "credential",
            "secret",
            "backend_object_key",
        ):
            assert forbidden not in rendered


    def test_signal_is_transparent_and_threshold_driven() -> None:
        app = create_app()
        service = app.state.admin_operational_reports_service
        policy = service.snapshot().policy
        for _ in range(policy.moderation_candidate_attention_threshold + 1):
            _seed_reason(app, CommunityReasonModeration.PENDING, reported=False)
        snapshot = service.snapshot(policy)
        assert snapshot.overall_signal.value == "ATTENTION"
        assert snapshot.reason_codes == ("MODERATION_BACKLOG",)
    """,
)

print("Admin operational reports backend bootstrap applied")
