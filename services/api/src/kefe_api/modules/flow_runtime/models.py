from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class FlowExecutionSupport(StrEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class FlowStepRuntimeState(StrEnum):
    READY = "READY"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class FlowRuntimeStep:
    code: str
    primitive_code: str
    capability_codes: tuple[str, ...]
    next_step_codes: tuple[str, ...]
    state: FlowStepRuntimeState
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class FlowRuntimeSnapshot:
    session_id: UUID
    case_version_id: UUID
    session_state: str
    template_code: str
    template_version_no: int
    entry_step_code: str
    execution_support: FlowExecutionSupport
    steps: tuple[FlowRuntimeStep, ...]
