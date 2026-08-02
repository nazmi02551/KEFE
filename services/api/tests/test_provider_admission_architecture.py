from __future__ import annotations

from tools.check_provider_admission_control_contract import main


def test_provider_admission_control_architecture_contract() -> None:
    assert main() == 0
