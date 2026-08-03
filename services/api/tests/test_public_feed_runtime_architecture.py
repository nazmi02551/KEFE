from __future__ import annotations

from kefe_api.tools_contract_runner import run_contract_checker


def test_public_feed_runtime_architecture_contract() -> None:
    run_contract_checker("check_public_feed_runtime_contract.py")
