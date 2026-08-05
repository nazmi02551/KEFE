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
from kefe_api.modules.identity.otp_delivery_health import (
    InMemoryOtpDeliveryHealthRepository,
    OtpDeliveryHealthService,
    OtpDeliveryHealthSignal,
)
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
        otp_delivery_health: OtpDeliveryHealthService | None = None,
        default_policy: AdminOperationalReportPolicy | None = None,
        clock=utcnow,
    ) -> None:
        self._content_supply = content_supply
        self._content_authoring = content_authoring
        self._proposal_review = proposal_review
        self._community_reason = community_reason
        self._otp_delivery_health = otp_delivery_health or OtpDeliveryHealthService(
            InMemoryOtpDeliveryHealthRepository()
        )
        self._default_policy = default_policy or AdminOperationalReportPolicy()
        self._clock = clock

    def snapshot(
        self,
        policy: AdminOperationalReportPolicy | None = None,
    ) -> AdminOperationalReportSnapshot:
        resolved_policy = policy or self._default_policy
        as_of = self._clock()
        content_supply = self._content_supply.snapshot(
            resolved_policy.content_supply,
            as_of=as_of,
        )
        otp_delivery = self._otp_delivery_health.snapshot(
            resolved_policy.otp_delivery,
            as_of=as_of,
        )
        editorial = {
            state.value: self._content_authoring.count_by_state(state) for state in ContentLifecycle
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
            otp_delivery_signal=otp_delivery.signal,
            editorial=editorial,
            proposals=proposals,
            moderation=moderation,
            policy=resolved_policy,
        )
        signal = self._signal(
            content_supply_signal=content_supply.signal,
            otp_delivery_signal=otp_delivery.signal,
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
            otp_delivery=otp_delivery,
            editorial_lifecycle=AdminOperationalReportSnapshot.immutable_counts(editorial),
            proposal_review=AdminOperationalReportSnapshot.immutable_counts(proposals),
            moderation=AdminOperationalReportSnapshot.immutable_counts(moderation),
        )

    @staticmethod
    def _reason_codes(
        *,
        content_supply_signal: ContentSupplyHealthSignal,
        otp_delivery_signal: OtpDeliveryHealthSignal,
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
        if otp_delivery_signal is OtpDeliveryHealthSignal.CRITICAL:
            reasons.add(AdminOperationalReason.OTP_DELIVERY_CRITICAL.value)
        elif otp_delivery_signal is OtpDeliveryHealthSignal.ATTENTION:
            reasons.add(AdminOperationalReason.OTP_DELIVERY_ATTENTION.value)
        if editorial[ContentLifecycle.IN_REVIEW.value] > policy.in_review_attention_threshold:
            reasons.add(AdminOperationalReason.EDITORIAL_IN_REVIEW_BACKLOG.value)
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
        otp_delivery_signal: OtpDeliveryHealthSignal,
        reasons: set[str],
        editorial: dict[str, int],
        proposals: dict[str, int],
        moderation: dict[str, int],
    ) -> AdminOperationalSignal:
        if (
            content_supply_signal is ContentSupplyHealthSignal.CRITICAL
            or otp_delivery_signal is OtpDeliveryHealthSignal.CRITICAL
        ):
            return AdminOperationalSignal.CRITICAL
        if reasons:
            return AdminOperationalSignal.ATTENTION
        backlog = sum(editorial.values()) + sum(proposals.values()) + sum(moderation.values())
        if (
            content_supply_signal is ContentSupplyHealthSignal.QUIET
            and otp_delivery_signal is OtpDeliveryHealthSignal.QUIET
            and backlog == 0
        ):
            return AdminOperationalSignal.QUIET
        return AdminOperationalSignal.NOMINAL
