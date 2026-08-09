from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

TOOL_PATH = Path(__file__).resolve().parents[1] / "tools/run_connected_alpha_acceptance.py"
SPEC = importlib.util.spec_from_file_location("connected_alpha_acceptance_tool", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
acceptance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = acceptance
SPEC.loader.exec_module(acceptance)

CASE_ID = "11111111-1111-4111-8111-111111111111"
CASE_VERSION_ID = "22222222-2222-4222-8222-222222222222"
QUESTION_ID = "33333333-3333-4333-8333-333333333333"
SOURCE_COMMIT = "d" * 40


@pytest.mark.parametrize(
    "value",
    [
        "",
        "http://api.example.com",
        "https://localhost",
        "https://127.0.0.1",
        "https://[::1]",
        "https://10.0.2.2",
        "https://api.invalid",
        "https://user:pass@api.example.com",
        "https://api.example.com?token=x",
        "https://api.example.com/#fragment",
    ],
)
def test_base_url_rejects_non_external_or_secret_bearing_targets(value: str) -> None:
    with pytest.raises(acceptance.AcceptanceError):
        acceptance._validate_base_url(value)


def test_base_url_accepts_https_external_origin_and_path() -> None:
    assert (
        acceptance._validate_base_url(" https://alpha-api.example.com/v1-root/ ")
        == "https://alpha-api.example.com/v1-root"
    )


@pytest.mark.parametrize(
    "value",
    ["", "unknown", "deadbeef", "g" * 40, "a" * 39, "b" * 41],
)
def test_source_commit_requires_exact_40_hex_sha(value: str) -> None:
    with pytest.raises(acceptance.AcceptanceError, match="40-character"):
        acceptance._validate_source_commit(value)


def test_source_commit_normalizes_hex_case() -> None:
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
    last: "FakeClient | None" = None

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
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if method == "GET" and path in {"/health", "/ready"}:
            return {"status": "ok"}
        if method == "GET" and path == f"/v1/cases/{CASE_ID}":
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
        if method == "POST" and path == "/v1/identity/guest":
            self.actor_seq += 1
            actor_id = f"00000000-0000-4000-8000-{self.actor_seq:012d}"
            issued_token = f"guest-token-{self.actor_seq}"
            self.actor_by_token[issued_token] = actor_id
            return {"actor_id": actor_id, "access_token": issued_token}
        if method == "POST" and path == f"/v1/cases/{CASE_ID}/weigh-sessions":
            assert token in self.actor_by_token
            self.session_seq += 1
            session_id = f"session-{self.session_seq}"
            self.session_by_token[token] = session_id
            return {"session_id": session_id}
        if method == "PUT" and path.endswith("/responses"):
            assert token in self.session_by_token
            assert body is not None
            response = body["responses"][0]
            self.option_by_token[token] = response["value"]
            return {"state": "DRAFT"}
        if method == "POST" and path.endswith("/commit"):
            assert token in self.option_by_token
            assert headers is not None and headers.get("Idempotency-Key")
            if token not in self.committed_tokens:
                self.committed_tokens.append(token)
            return {"state": "COMMITTED"}
        if method == "GET" and path.endswith("/reveal"):
            counts = {"A": 0, "B": 0}
            for committed in self.committed_tokens:
                counts[self.option_by_token[committed]] += 1
            n = len(self.committed_tokens)
            assert n > 0
            return {
                "layer": "RAW",
                "n": n,
                "confidence": "INSUFFICIENT",
                "result": {key: value / n for key, value in counts.items()},
            }
        if method == "DELETE" and path == "/v1/me":
            assert token in self.actor_by_token
            actor_id = self.actor_by_token[token]
            assert headers == {"X-KEFE-Delete-Confirm": f"DELETE:{actor_id}"}
            self.deleted_actor_ids.append(actor_id)
            return {"actor_id": actor_id, "private_data_deleted": True}
        raise AssertionError(f"unexpected request: {method} {path}")


class TrustedRevealClient(FakeClient):
    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if method == "GET" and path.endswith("/reveal"):
            return {
                "layer": "TRUSTED",
                "n": 10,
                "confidence": "HIGH",
                "result": {"A": 0.5, "B": 0.5},
            }
        return super().request(method, path, **kwargs)


def test_two_actor_acceptance_proves_shared_increment_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(acceptance, "JsonHttpClient", FakeClient)
    record = acceptance.run_acceptance(
        base_url="https://alpha-api.example.com",
        case_id=CASE_ID,
        allow_write=True,
        timeout_seconds=12,
        source_commit=SOURCE_COMMIT,
    )

    client = FakeClient.last
    assert client is not None
    assert record["status"] == "ACCEPTED_CLEANED"
    assert record["sample_size_after_second"] == record["sample_size_after_first"] + 1
    assert record["actor_count"] == 2
    assert record["cleanup"] == "PASSED"
    assert record["source_commit"] == SOURCE_COMMIT
    assert len(client.deleted_actor_ids) == 2
    assert "token" not in str(record).lower()


def test_trusted_case_is_not_accepted_as_live_raw_proof_and_actors_are_cleaned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(acceptance, "JsonHttpClient", TrustedRevealClient)
    with pytest.raises(acceptance.AcceptanceError, match="live RAW"):
        acceptance.run_acceptance(
            base_url="https://alpha-api.example.com",
            case_id=CASE_ID,
            allow_write=True,
            timeout_seconds=12,
            source_commit=SOURCE_COMMIT,
        )

    client = TrustedRevealClient.last
    assert client is not None
    assert len(client.deleted_actor_ids) == 2
