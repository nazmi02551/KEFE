from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_rss_atom_subscription_activation_architecture_contract() -> None:
    api_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(api_root / "tools/check_rss_atom_subscription_activation_contract.py"),
        ],
        cwd=api_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
