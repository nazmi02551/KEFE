from __future__ import annotations

import json
from dataclasses import replace
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from kefe_api.infrastructure.postgres_content_authoring import PostgresContentAuthoringRepository
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    ResolvedFlowDefinition,
    ResolvedFlowStep,
)


class PostgresFlowPinnedContentAuthoringRepository(PostgresContentAuthoringRepository):
    """Extends the proven authoring adapter with immutable Flow/config provenance."""

    @staticmethod
    def _resolved_flow_document(flow: ResolvedFlowDefinition | None) -> dict[str, Any] | None:
        if flow is None:
            return None
        return {
            "template_code": flow.template_code,
            "template_version_no": flow.template_version_no,
            "entry_step_code": flow.entry_step_code,
            "steps": [
                {
                    "code": step.code,
                    "primitive_code": step.primitive_code,
                    "capability_codes": list(step.capability_codes),
                    "next_step_codes": list(step.next_step_codes),
                    "payload_schema_ref": step.payload_schema_ref,
                }
                for step in flow.steps
            ],
        }

    @staticmethod
    def _resolved_flow_from_document(
        document: dict[str, Any] | None,
    ) -> ResolvedFlowDefinition | None:
        if document is None:
            return None
        return ResolvedFlowDefinition(
            template_code=document["template_code"],
            template_version_no=int(document["template_version_no"]),
            entry_step_code=document["entry_step_code"],
            steps=tuple(
                ResolvedFlowStep(
                    code=item["code"],
                    primitive_code=item["primitive_code"],
                    capability_codes=tuple(item.get("capability_codes", [])),
                    next_step_codes=tuple(item.get("next_step_codes", [])),
                    payload_schema_ref=item.get("payload_schema_ref"),
                )
                for item in document.get("steps", [])
            ),
        )

    @classmethod
    def _document(cls, version: AuthoringCaseVersion) -> dict[str, Any]:
        document = PostgresContentAuthoringRepository._document(version)
        document.update(
            {
                "flow_template_code": version.flow_template_code,
                "flow_template_version_no": version.flow_template_version_no,
                "content_configuration_id": (
                    str(version.content_configuration_id)
                    if version.content_configuration_id is not None
                    else None
                ),
                "content_configuration_version_no": version.content_configuration_version_no,
                "resolved_flow": cls._resolved_flow_document(version.resolved_flow),
            }
        )
        return document

    @classmethod
    def _version_from_row(cls, row) -> AuthoringCaseVersion:
        base = PostgresContentAuthoringRepository._version_from_row(row)
        document = row["aggregate"]
        config_id = document.get("content_configuration_id")
        return replace(
            base,
            flow_template_code=document.get("flow_template_code", "STANDARD_COMMIT_REVEAL"),
            flow_template_version_no=int(document.get("flow_template_version_no", 1)),
            content_configuration_id=UUID(config_id) if config_id else None,
            content_configuration_version_no=document.get("content_configuration_version_no"),
            resolved_flow=cls._resolved_flow_from_document(document.get("resolved_flow")),
        )

    def _materialize_consumer(
        self,
        connection: Connection,
        version: AuthoringCaseVersion,
    ) -> None:
        super()._materialize_consumer(connection, version)
        if (
            version.content_configuration_id is None
            or version.content_configuration_version_no is None
            or version.resolved_flow is None
        ):
            raise ValueError("published CaseVersion requires resolved Flow/configuration provenance")

        connection.execute(
            text(
                """
                UPDATE content.case_version
                SET content_configuration_id = :content_configuration_id,
                    content_configuration_version_no = :content_configuration_version_no,
                    flow_template_code = :flow_template_code,
                    flow_template_version_no = :flow_template_version_no,
                    resolved_flow = CAST(:resolved_flow AS jsonb)
                WHERE id = :version_id
                """
            ),
            {
                "version_id": version.id,
                "content_configuration_id": version.content_configuration_id,
                "content_configuration_version_no": version.content_configuration_version_no,
                "flow_template_code": version.resolved_flow.template_code,
                "flow_template_version_no": version.resolved_flow.template_version_no,
                "resolved_flow": json.dumps(
                    self._resolved_flow_document(version.resolved_flow)
                ),
            },
        )
