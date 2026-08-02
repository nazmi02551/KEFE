from __future__ import annotations

from tools.check_provider_secret_execution_contract import main


def test_provider_secret_execution_architecture_contract() -> None:
    assert main() == 0
