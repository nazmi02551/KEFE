from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from uuid import UUID

import pytest

ROOT = Path(__file__).resolve().parents[3]
TOOL_PATH = ROOT / "services/api/tools/run_connected_alpha_acceptance.py"
SPEC = importlib.util.spec_from_file_location("connected_alpha_acceptance", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)

CASE_ID = "11111111-1111-4111-8111-111111111111"
CASE_VERSION_ID = "22222222-2222-4222-8222-222222222222"
QUESTION_ID = "33333333-3333-4333-8333-333333333333"
SOURCE_COMMIT = "1234567890abcdef1234567890abcdef12345678"


def test_rejects_non_https_and_reserved_endpoint() -> None:
    for value in (
        "http://api.example.com",
        "https://localhost",
        "https://127.0.0.1",
        "https://10.0.0.1",
        "https://alpha-api.invalid",
        "https://user@example.com",
        "https://api.example.com/path",
    ):
        with pytest.raises(acceptance.AcceptanceError):
            acceptance._validate_base_url(value)


def test_accepts_public_https_endpoint() -> None:
    assert acceptance._validate_base_url("https://alpha-api.example.com") == (
        "https://alpha-api.example.com"
    )


def test_requires_exact_deployed_source_commit() -> None:
    for value in (
        "",
        "abc",
        "g" * 40,
        "a" * 39,
        "a" * 41,
    ):
        with pytest.raises(acceptance.AcceptanceError, match="source commit"):
            acceptance._validate_source_commit(value)
    assert acceptance._validate_source_commit("A" * 40) == "a" * 40


def test_refuses_remote_mutation_without_explicit_allow_write() -> None:
    with pytest.raises(acceptance.AcceptanceError, match="--allow-write"):
        acceptance.run_acceptance(
            base_url="https://alpha-api.example.com",
            case_id=CASE_ID,
            allow_write=False,
            timeout_seconds=12,
            source_commit=SOURCE_COMMIT,
        )


class FakeClient:
    last: FakeClient | None = None

    def __init__(self, base_url: str, *, timeout_seconds: int) -> None:
        self.base_url = acceptance._validate_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.actor_seq = 0
        self.session_seq = 0
        self.actor_by_token: dict[str, str] = {}
        self.session_by_token: dict[str, str] = {}
        self.option_by_token: dict[str, str] = {}
        self.committed_tokens: list[str] = []
        self.deleted_actor_ids: list[str] = []
        FakeClient.last = self

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: int,
    ) -> dict[str, Any] | None:
        del headers
        if method == "GET" and path == "/health":
            assert expected_status == 200
            return {"status": "ok"}
        if method == "GET" and path == "/ready":
            assert expected_status == 200
            return {"status": "ok"}
        if method == "POST" and path == "/v1/identity/guest":
            assert expected_status == 201
            self.actor_seq += 1
            actor_id = f"00000000-0000-4000-8000-{self.actor_seq:012d}"
            actor_token = f"guest-token-{self.actor_seq}"
            self.actor_by_token[actor_token] = actor_id
            return {
                "actor_id": actor_id,
                "access_token": actor_token,
                "expires_at": "2030-01-01T00:00:00Z",
            }
        if method == "GET" and path == f"/v1/cases/{CASE_ID}":
            assert expected_status == 200
            return {
                "case_id": CASE_ID,
                "case_version_id": CASE_VERSION_ID,
                "questions": [
                    {
                        "question_id": QUESTION_ID,
                        "response_type": "SINGLE_CHOICE",
                        "required": True,
                        "options": ["A", "B"],
                    }
                ],
            }
        if method == "POST" and path == f"/v1/cases/{CASE_ID}/weigh-sessions":
            assert expected_status == 201
            assert token in self.actor_by_token
            self.session_seq += 1
            session_id = f"10000000-0000-4000-8000-{self.session_seq:012d}"
            self.session_by_token[token] = session_id
            return {
                "session_id": session_id,
                "case_id": CASE_ID,
                "case_version_id": CASE_VERSION_ID,
                "state": "DRAFT",
            }
        if method == "PUT" and path.endswith("/responses"):
            assert expected_status == 200
            assert token is not None
            assert json_body is not None
            responses = json_body["responses"]
            assert isinstance(responses, list) and len(responses) == 1
            value = responses[0]["value"]
            assert value in {"A", "B"}
            self.option_by_token[token] = value
            return {"status": "ok"}
        if method == "POST" and path.endswith("/commit"):
            assert expected_status == 200
            assert token is not None
            self.committed_tokens.append(token)
            return {"status": "committed"}
        if method == "GET" and path.endswith("/reveal"):
            assert expected_status == 200
            n = len(self.committed_tokens)
            counts = {"A": 0, "B": 0}
            for committed in self.committed_tokens:
                counts[self.option_by_token[committed]] += 1
            distribution = [
                {"option": key, "value": counts[key] / n if n else 0.0}
                for key in ("A", "B")
            ]
            return {
                "layer": "RAW",
                "n": n,
                "distribution": distribution,
                "confidence": "INSUFFICIENT",
            }
        if method == "DELETE" and path == "/v1/me":
            assert expected_status == 200
            assert token is not None
            actor_id = self.actor_by_token[token]
            self.deleted_actor_ids.append(actor_id)
            return {
                "actor_id": actor_id,
                "private_data_deleted": True,
                "aggregate_contributions_anonymized": True,
            }
        raise AssertionError(f"unexpected request {method} {path}")


def test_two_actor_acceptance_flow_is_shared_and_cleanup_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(acceptance, "HttpClient", FakeClient)

    evidence = acceptance.run_acceptance(
        base_url="https://alpha-api.example.com",
        case_id=CASE_ID,
        allow_write=True,
        timeout_seconds=12,
        source_commit=SOURCE_COMMIT,
    )

    client = FakeClient.last
    assert client is not None
    assert len(client.actor_by_token) == 2
    assert len(client.committed_tokens) == 2
    assert len(client.deleted_actor_ids) == 2
    assert evidence["source_commit"] == SOURCE_COMMIT
    assert evidence["case_id"] == CASE_ID
    assert evidence["case_version_id"] == CASE_VERSION_ID
    assert evidence["first_raw_n"] == 1
    assert evidence["second_raw_n"] == 2
    assert evidence["reread_raw_n"] == 2
    serialized = json.dumps(evidence)
    for token in client.actor_by_token:
        assert token not in serialized
    for actor_id in client.actor_by_token.values():
        assert actor_id not in serialized
    assert "selected_option" not in serialized


def test_cleanup_still_runs_when_second_commit_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingSecondCommitClient(FakeClient):
        def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
            if method == "POST" and path.endswith("/commit") and len(self.committed_tokens) == 1:
                raise acceptance.AcceptanceError("synthetic second commit failure")
            return super().request(method, path, **kwargs)

    monkeypatch.setattr(acceptance, "HttpClient", FailingSecondCommitClient)

    with pytest.raises(acceptance.AcceptanceError, match="synthetic second commit failure"):
        acceptance.run_acceptance(
            base_url="https://alpha-api.example.com",
            case_id=CASE_ID,
            allow_write=True,
            timeout_seconds=12,
            source_commit=SOURCE_COMMIT,
        )

    client = FakeClient.last
    assert client is not None
    assert len(client.deleted_actor_ids) == 2


def test_cleanup_failure_is_acceptance_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class CleanupFailureClient(FakeClient):
        def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
            if method == "DELETE" and path == "/v1/me":
                raise acceptance.AcceptanceError("synthetic cleanup failure")
            return super().request(method, path, **kwargs)

    monkeypatch.setattr(acceptance, "HttpClient", CleanupFailureClient)

    with pytest.raises(acceptance.AcceptanceError, match="cleanup failed"):
        acceptance.run_acceptance(
            base_url="https://alpha-api.example.com",
            case_id=CASE_ID,
            allow_write=True,
            timeout_seconds=12,
            source_commit=SOURCE_COMMIT,
        )


def test_rejects_trusted_reveal_for_live_raw_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    class TrustedRevealClient(FakeClient):
        def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
            response = super().request(method, path, **kwargs)
            if method == "GET" and path.endswith("/reveal") and response is not None:
                response["layer"] = "TRUSTED"
            return response

    monkeypatch.setattr(acceptance, "HttpClient", TrustedRevealClient)

    with pytest.raises(acceptance.AcceptanceError, match="expected RAW"):
        acceptance.run_acceptance(
            base_url="https://alpha-api.example.com",
            case_id=CASE_ID,
            allow_write=True,
            timeout_seconds=12,
            source_commit=SOURCE_COMMIT,
        )
