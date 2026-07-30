from __future__ import annotations

from statistics import quantiles
from time import perf_counter

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

BUDGET_MS = {
    "feed": 700.0,
    "commit": 500.0,
    "cached_reveal": 800.0,
}


def _p95(samples: list[float]) -> float:
    if len(samples) < 2:
        return samples[0]
    return quantiles(samples, n=20, method="inclusive")[18]


def _guest(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def main() -> None:
    client = TestClient(create_app())
    feed_samples: list[float] = []
    commit_samples: list[float] = []
    reveal_samples: list[float] = []

    # This is a deterministic in-process regression harness, not a production SLO claim.
    for index in range(20):
        start = perf_counter()
        response = client.get("/v1/cases")
        elapsed = (perf_counter() - start) * 1000
        response.raise_for_status()
        feed_samples.append(elapsed)

        headers = _guest(client)
        session = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
        session.raise_for_status()
        session_id = session.json()["session_id"]
        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        )
        answer.raise_for_status()

        start = perf_counter()
        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"perf-commit-{index:04d}"},
        )
        commit_samples.append((perf_counter() - start) * 1000)
        commit.raise_for_status()

        # Warm once, then time a cached/read-only Reveal retrieval.
        warm = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
        warm.raise_for_status()
        start = perf_counter()
        reveal = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
        reveal_samples.append((perf_counter() - start) * 1000)
        reveal.raise_for_status()

    results = {
        "feed": _p95(feed_samples),
        "commit": _p95(commit_samples),
        "cached_reveal": _p95(reveal_samples),
    }
    failures = [
        f"{name} p95 {value:.1f}ms exceeds {BUDGET_MS[name]:.0f}ms"
        for name, value in results.items()
        if value > BUDGET_MS[name]
    ]
    if failures:
        raise SystemExit("\n".join(failures))
    print(
        "MVP in-process performance budget OK: "
        + ", ".join(f"{name} p95={value:.1f}ms" for name, value in results.items())
    )
    print("Production SLO/load validation remains an external beta gate.")


if __name__ == "__main__":
    main()
