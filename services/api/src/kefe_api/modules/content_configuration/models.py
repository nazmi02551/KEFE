from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ContentConfigLifecycle(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class TaxonomyItem:
    code: str
    label_key: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class TopicItem:
    code: str
    domain_code: str
    label_key: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class PrimitiveDefinition:
    code: str
    label_key: str
    payload_schema_ref: str | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    code: str
    label_key: str
    compatible_primitive_codes: frozenset[str]
    config_schema_ref: str | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class FlowStepDefinition:
    code: str
    primitive_code: str
    capability_codes: tuple[str, ...] = ()
    next_step_codes: tuple[str, ...] = ()
    payload_schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class FlowTemplateDefinition:
    code: str
    version_no: int
    label_key: str
    entry_step_code: str
    steps: tuple[FlowStepDefinition, ...]
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ContentConfigurationSnapshot:
    id: UUID
    version_no: int
    state: ContentConfigLifecycle
    domains: tuple[TaxonomyItem, ...]
    topics: tuple[TopicItem, ...]
    base_formats: tuple[TaxonomyItem, ...]
    modifiers: tuple[TaxonomyItem, ...]
    modifier_compatibility: dict[str, frozenset[str]]
    primitives: tuple[PrimitiveDefinition, ...]
    capabilities: tuple[CapabilityDefinition, ...]
    flow_templates: tuple[FlowTemplateDefinition, ...]
    risks: frozenset[str]
    claim_states: frozenset[str]
    source_kinds: frozenset[str]
    disclosure_levels: frozenset[str]
    created_by: str
    created_at: datetime
    published_at: datetime | None = None
    cloned_from_version_id: UUID | None = None

    def with_state(
        self,
        state: ContentConfigLifecycle,
        *,
        published_at: datetime | None = None,
    ) -> ContentConfigurationSnapshot:
        return replace(
            self,
            state=state,
            published_at=published_at if published_at is not None else self.published_at,
        )

    @property
    def enabled_domain_codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.domains if item.enabled)

    @property
    def enabled_base_format_codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.base_formats if item.enabled)

    @property
    def enabled_modifier_codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.modifiers if item.enabled)

    @property
    def enabled_primitive_codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.primitives if item.enabled)

    @property
    def enabled_capability_codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.capabilities if item.enabled)

    @property
    def enabled_flow_template_keys(self) -> frozenset[tuple[str, int]]:
        return frozenset(
            (item.code, item.version_no) for item in self.flow_templates if item.enabled
        )


@dataclass(frozen=True, slots=True)
class ContentConfigurationAuditEntry:
    audit_id: UUID
    config_version_id: UUID
    actor_ref: str
    command: str
    previous_state: ContentConfigLifecycle | None
    new_state: ContentConfigLifecycle
    occurred_at: datetime
    rationale: str | None = None

    @classmethod
    def create(
        cls,
        *,
        snapshot: ContentConfigurationSnapshot,
        actor_ref: str,
        command: str,
        previous_state: ContentConfigLifecycle | None,
        new_state: ContentConfigLifecycle,
        rationale: str | None = None,
    ) -> ContentConfigurationAuditEntry:
        return cls(
            audit_id=uuid4(),
            config_version_id=snapshot.id,
            actor_ref=actor_ref,
            command=command,
            previous_state=previous_state,
            new_state=new_state,
            occurred_at=datetime.now(UTC),
            rationale=rationale,
        )
