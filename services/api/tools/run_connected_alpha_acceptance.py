from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

_FORBIDDEN_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "10.0.2.2",
    }
)
_EXACT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class AcceptanceError(RuntimeError):
    pass


@dataclass(slots=True)
class GuestActor:
    actor_id: str
    token: str
    session_id: str | None = None


class JsonHttpClient:
    def __init__(self, base_url: str, *, timeout_seconds: int) -> None:
        self.base_url = _validate_base_url(base_url)
        self.timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request_headers = {"accept": "application/json"}
        if body is not None:
            request_headers["content-type"] = "application/json"
        if token is not None:
            request_headers["authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)

        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            urljoin(f"{self.base_url}/", path.lstrip("/")),
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = response.read()
                if not payload:
                    return {}
                try:
                    decoded = json.loads(payload)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise AcceptanceError(
                        f"{method} {path}: response was not valid JSON"
                    ) from exc
                if not isinstance(decoded, dict):
                    raise AcceptanceError(f"{method} {path}: expected a JSON object")
                return decoded
        except HTTPError as exc:
            code = "UNKNOWN_API_ERROR"
            try:
                decoded_error = json.loads(exc.read())
                if isinstance(decoded_error, dict):
                    code = str(decoded_error.get("code") or code)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            raise AcceptanceError(
                f"{method} {path}: HTTP {exc.code} ({code})"
            ) from None
        except (URLError, TimeoutError) as exc:
            raise AcceptanceError(f"{method} {path}: transport failure") from exc


def _validate_base_url(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise AcceptanceError("Connected Alpha base URL is required")
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise AcceptanceError("Connected Alpha acceptance requires HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise AcceptanceError("credentials are forbidden in the API URL")
    if parsed.query or parsed.fragment:
        raise AcceptanceError("query and fragment are forbidden in the API URL")
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise AcceptanceError("Connected Alpha API URL must contain a hostname")
    if hostname in _FORBIDDEN_HOSTS or hostname.endswith(".invalid"):
        raise AcceptanceError("local, emulator and reserved API hosts are forbidden")
    normalized = f"https://{parsed.netloc}{parsed.path}".rstrip("/")
    return normalized


def _validate_source_commit(value: str) -> str:
    normalized = value.strip().lower()
    if not _EXACT_COMMIT_RE.fullmatch(normalized):
        raise AcceptanceError("--source-commit must be an exact 40-character Git SHA")
    return normalized


def _required_decision(case: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    questions = case.get("questions")
    if not isinstance(questions, list):
        raise AcceptanceError("Case response does not contain typed questions")
    for raw in questions:
        if not isinstance(raw, dict):
            continue
        if raw.get("response_type") != "SINGLE_CHOICE" or raw.get("required") is not True:
            continue
        question_id = raw.get("question_id")
        if not isinstance(question_id, str):
            continue
        raw_options = raw.get("options")
        if not isinstance(raw_options, list):
            schema = raw.get("response_schema")
            raw_options = schema.get("options") if isinstance(schema, dict) else None
        if not isinstance(raw_options, list):
            continue
        options = tuple(
            dict.fromkeys(option for option in raw_options if isinstance(option, str) and option)
        )
        if len(options) >= 2:
            return question_id, options
    raise AcceptanceError(
        "acceptance Case requires a required SINGLE_CHOICE question with at least two options"
    )


def _new_guest(client: JsonHttpClient) -> GuestActor:
    body = client.request(
        "POST",
        "/v1/identity/guest",
        body={"platform": "ANDROID"},
    )
    actor_id = body.get("actor_id")
    token = body.get("access_token")
    if not isinstance(actor_id, str) or not isinstance(token, str):
        raise AcceptanceError("guest issuance returned an invalid credential response")
    try:
        UUID(actor_id)
    except ValueError as exc:
        raise AcceptanceError("guest issuance returned an invalid actor id") from exc
    return GuestActor(actor_id=actor_id, token=token)


def _start_and_answer(
    client: JsonHttpClient,
    actor: GuestActor,
    *,
    case_id: str,
    question_id: str,
    option: str,
) -> None:
    started = client.request(
        "POST",
        f"/v1/cases/{case_id}/weigh-sessions",
        token=actor.token,
    )
    session_id = started.get("session_id")
    if not isinstance(session_id, str):
        raise AcceptanceError("weigh-session creation returned no session id")
    actor.session_id = session_id
    client.request(
        "PUT",
        f"/v1/weigh-sessions/{session_id}/responses",
        token=actor.token,
        body={"responses": [{"question_id": question_id, "value": option}]},
    )


def _commit(client: JsonHttpClient, actor: GuestActor) -> None:
    if actor.session_id is None:
        raise AcceptanceError("actor has no weigh session")
    committed = client.request(
        "POST",
        f"/v1/weigh-sessions/{actor.session_id}/commit",
        token=actor.token,
        headers={"Idempotency-Key": f"external-alpha-{uuid4()}"},
    )
    if committed.get("state") != "COMMITTED":
        raise AcceptanceError("commit did not converge to COMMITTED")


def _reveal(client: JsonHttpClient, actor: GuestActor) -> dict[str, Any]:
    if actor.session_id is None:
        raise AcceptanceError("actor has no weigh session")
    result = client.request(
        "GET",
        f"/v1/weigh-sessions/{actor.session_id}/reveal",
        token=actor.token,
    )
    if result.get("layer") != "RAW":
        raise AcceptanceError(
            "acceptance Case must expose live RAW result; choose a dedicated Case "
            "without a TRUSTED snapshot"
        )
    if not isinstance(result.get("n"), int):
        raise AcceptanceError("RAW reveal returned an invalid sample size")
    values = result.get("result")
    if not isinstance(values, dict) or not values:
        raise AcceptanceError("RAW reveal returned no option proportions")
    try:
        total = sum(float(value) for value in values.values())
    except (TypeError, ValueError) as exc:
        raise AcceptanceError("RAW reveal returned non-numeric option proportions") from exc
    if abs(total - 1.0) > 1e-9:
        raise AcceptanceError("RAW reveal proportions do not sum to 1.0")
    return result


def _delete_actor(client: JsonHttpClient, actor: GuestActor) -> None:
    receipt = client.request(
        "DELETE",
        "/v1/me",
        token=actor.token,
        headers={"X-KEFE-Delete-Confirm": f"DELETE:{actor.actor_id}"},
    )
    if receipt.get("actor_id") != actor.actor_id:
        raise AcceptanceError("privacy cleanup receipt actor does not match test actor")
    if receipt.get("private_data_deleted") is not True:
        raise AcceptanceError("privacy cleanup receipt did not confirm private data deletion")
    if receipt.get("aggregate_contributions_anonymized") is not True:
        raise AcceptanceError(
            "privacy cleanup receipt did not confirm aggregate contribution handling"
        )


def run_acceptance(
    *,
    base_url: str,
    case_id: str,
    allow_write: bool,
    timeout_seconds: int,
    source_commit: str,
) -> dict[str, Any]:
    if not allow_write:
        raise AcceptanceError("refusing remote writes without explicit --allow-write")
    try:
        UUID(case_id)
    except ValueError as exc:
        raise AcceptanceError("--case-id must be a UUID") from exc
    if not 3 <= timeout_seconds <= 60:
        raise AcceptanceError("timeout must be between 3 and 60 seconds")
    exact_source_commit = _validate_source_commit(source_commit)

    started_at = datetime.now(UTC)
    client = JsonHttpClient(base_url, timeout_seconds=timeout_seconds)
    parsed_origin = urlsplit(client.base_url)
    origin = f"{parsed_origin.scheme}://{parsed_origin.netloc}"

    actors: list[GuestActor] = []
    primary_error: Exception | None = None
    record: dict[str, Any] | None = None
    try:
        client.request("GET", "/health")
        client.request("GET", "/ready")
        case = client.request("GET", f"/v1/cases/{case_id}")
        case_version_id = case.get("case_version_id")
        if not isinstance(case_version_id, str):
            raise AcceptanceError("Case response has no CaseVersion id")
        try:
            UUID(case_version_id)
        except ValueError as exc:
            raise AcceptanceError("Case response has an invalid CaseVersion id") from exc
        question_id, options = _required_decision(case)

        first = _new_guest(client)
        actors.append(first)
        second = _new_guest(client)
        actors.append(second)
        if first.actor_id == second.actor_id or first.token == second.token:
            raise AcceptanceError("guest issuance did not produce independent actors")

        _start_and_answer(
            client,
            first,
            case_id=case_id,
            question_id=question_id,
            option=options[0],
        )
        _start_and_answer(
            client,
            second,
            case_id=case_id,
            question_id=question_id,
            option=options[1],
        )

        _commit(client, first)
        after_first = _reveal(client, first)

        _commit(client, second)
        after_second = _reveal(client, second)
        if after_second["n"] != after_first["n"] + 1:
            raise AcceptanceError(
                "second committed actor did not increment shared RAW sample size by exactly one"
            )

        reread_first = _reveal(client, first)
        if reread_first["n"] != after_second["n"]:
            raise AcceptanceError(
                "first actor does not observe the shared post-second-commit sample"
            )
        if reread_first["result"] != after_second["result"]:
            raise AcceptanceError("actors do not observe the same shared RAW option payload")

        record = {
            "schema_version": "connected-alpha-acceptance.v1",
            "status": "ACCEPTED_PENDING_CLEANUP",
            "origin": origin,
            "case_id": case_id,
            "case_version_id": case_version_id,
            "layer": "RAW",
            "sample_size_after_first": after_first["n"],
            "sample_size_after_second": after_second["n"],
            "actor_count": 2,
            "source_commit": exact_source_commit,
            "started_at": started_at.isoformat(),
        }
    except Exception as exc:  # cleanup must still run for any partially created actor
        primary_error = exc
    finally:
        cleanup_errors: list[str] = []
        for actor in reversed(actors):
            try:
                _delete_actor(client, actor)
            except Exception as exc:  # noqa: BLE001 - redact cleanup failure details
                cleanup_errors.append(type(exc).__name__)

        if cleanup_errors:
            raise AcceptanceError(
                "acceptance actor cleanup failed: " + ",".join(cleanup_errors)
            ) from primary_error
        if primary_error is not None:
            if isinstance(primary_error, AcceptanceError):
                raise primary_error
            raise AcceptanceError("unexpected acceptance failure") from primary_error

    assert record is not None
    record["status"] = "ACCEPTED_CLEANED"
    record["cleanup"] = "PASSED"
    record["completed_at"] = datetime.now(UTC).isoformat()
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the external KEFE Connected Alpha two-actor acceptance proof."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--allow-write", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=12)
    parser.add_argument(
        "--source-commit",
        default=os.getenv("GITHUB_SHA", ""),
        help="Exact 40-character commit SHA of the deployed KEFE source.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        record = run_acceptance(
            base_url=args.base_url,
            case_id=args.case_id,
            allow_write=args.allow_write,
            timeout_seconds=args.timeout_seconds,
            source_commit=args.source_commit,
        )
    except AcceptanceError as exc:
        print(f"Connected Alpha acceptance failed: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(record, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
