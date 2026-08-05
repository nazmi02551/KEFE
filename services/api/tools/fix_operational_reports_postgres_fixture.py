from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "services/api/tests/test_admin_operational_reports_http_postgres.py"


def replace_once(source: str, old: str, new: str) -> str:
    matches = source.count(old)
    if matches != 1:
        raise RuntimeError(f"expected one fixture snippet, found {matches}: {old[:120]!r}")
    return source.replace(old, new, 1)


content = PATH.read_text(encoding="utf-8")
content = replace_once(
    content,
    "def _seed_proposal(app, decision: ProposalReviewDecisionKind | None) -> None:\n",
    "def _seed_proposal(\n"
    "    app,\n"
    "    database_url: str,\n"
    "    decision: ProposalReviewDecisionKind | None,\n"
    ") -> None:\n",
)
content = replace_once(
    content,
    "    proposal_id = uuid4()\n"
    "    repository.create_or_get_run(\n",
    "    proposal_id = uuid4()\n"
    "    source_artifact_id = uuid4()\n"
    "    engine = create_engine(database_url)\n"
    "    with engine.begin() as connection:\n"
    "        connection.execute(\n"
    "            text(\n"
    "                \"\"\"\n"
    "                INSERT INTO knowledge.source_artifact (\n"
    "                    id, adapter_code, external_locator, captured_at,\n"
    "                    content_hash, created_at\n"
    "                ) VALUES (\n"
    "                    :id, 'OPERATIONAL_REPORT_TEST', :locator, :captured_at,\n"
    "                    :content_hash, :captured_at\n"
    "                )\n"
    "                \"\"\"\n"
    "            ),\n"
    "            {\n"
    "                \"id\": source_artifact_id,\n"
    "                \"locator\": f\"urn:kefe:test:operational-report:{source_artifact_id}\",\n"
    "                \"captured_at\": now,\n"
    "                \"content_hash\": source_artifact_id.hex.ljust(64, \"0\")[:64],\n"
    "            },\n"
    "        )\n"
    "    repository.create_or_get_run(\n",
)
content = replace_once(
    content,
    "            input_artifact_id=uuid4(),\n",
    "            input_artifact_id=source_artifact_id,\n",
)
for old, new in (
    ("        _seed_proposal(first_app, None)\n", "        _seed_proposal(first_app, database_url, None)\n"),
    (
        "        _seed_proposal(first_app, ProposalReviewDecisionKind.ACCEPTED)\n",
        "        _seed_proposal(\n"
        "            first_app, database_url, ProposalReviewDecisionKind.ACCEPTED\n"
        "        )\n",
    ),
    (
        "        _seed_proposal(first_app, ProposalReviewDecisionKind.REJECTED)\n",
        "        _seed_proposal(\n"
        "            first_app, database_url, ProposalReviewDecisionKind.REJECTED\n"
        "        )\n",
    ),
    (
        "        _seed_proposal(first_app, ProposalReviewDecisionKind.CHANGES_REQUESTED)\n",
        "        _seed_proposal(\n"
        "            first_app,\n"
        "            database_url,\n"
        "            ProposalReviewDecisionKind.CHANGES_REQUESTED,\n"
        "        )\n",
    ),
):
    content = replace_once(content, old, new)

compile(content, str(PATH), "exec")
PATH.write_text(content, encoding="utf-8")
print("Operational Reports PostgreSQL fixture now seeds canonical source artifacts")
