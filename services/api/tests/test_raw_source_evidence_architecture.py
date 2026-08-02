from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_raw_source_evidence_architecture_contract() -> None:
    api_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "tools/check_raw_source_evidence_contract.py"],
        cwd=api_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
