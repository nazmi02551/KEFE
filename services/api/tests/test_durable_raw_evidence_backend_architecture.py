from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_durable_raw_evidence_backend_architecture_contract() -> None:
    api_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "tools/check_durable_raw_evidence_backend_contract.py"],
        cwd=api_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "durable raw evidence backend contract: PASS" in completed.stdout
