from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_provider_http_auth_architecture_contract() -> None:
    api_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "tools/check_provider_http_auth_contract.py"],
        cwd=api_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
