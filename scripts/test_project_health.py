from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("project_health.py")
SPEC = importlib.util.spec_from_file_location("project_health", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
project_health = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_health
SPEC.loader.exec_module(project_health)


class ProjectHealthTests(unittest.TestCase):
    def test_quick_profile_does_not_include_slow_builds_or_full_suites(self) -> None:
        names = {check.name for check in project_health.quick_checks()}

        self.assertIn("API lint", names)
        self.assertIn("Web tests", names)
        self.assertIn("Mobile analyze", names)
        self.assertIn("Admin production dependency audit", names)
        self.assertIn("Web production dependency audit", names)
        self.assertNotIn("API full in-memory tests", names)
        self.assertNotIn("Web full verify", names)
        self.assertNotIn("Mobile full tests", names)

    def test_full_profile_covers_all_local_product_surfaces(self) -> None:
        names = {check.name for check in project_health.full_checks(include_postgres=False)}

        self.assertIn("API full in-memory tests", names)
        self.assertIn("Admin full verify", names)
        self.assertIn("Web full verify", names)
        self.assertIn("Mobile full tests", names)
        self.assertIn("Admin production dependency audit", names)
        self.assertIn("Web production dependency audit", names)
        self.assertNotIn("API PostgreSQL tests", names)

    def test_postgres_is_explicit_opt_in(self) -> None:
        names = {check.name for check in project_health.full_checks(include_postgres=True)}

        self.assertIn("API PostgreSQL tests", names)

    @patch.object(project_health.shutil, "which", return_value=None)
    @patch.object(project_health.subprocess, "run")
    def test_run_check_never_uses_a_shell(self, run_mock, _which_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(["tool"], 0, "ok", "")

        result = project_health.run_check(
            project_health.Check("Example", ("tool", "--check"), Path("."))
        )

        self.assertTrue(result.passed)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    @patch.object(project_health.shutil, "which", return_value=None)
    @patch.object(project_health.subprocess, "run")
    def test_dirty_worktree_fails(self, run_mock, _which_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            ["git", "status", "--porcelain"], 0, " M changed.py\n", ""
        )

        result = project_health.git_clean_check()

        self.assertFalse(result.passed)
        self.assertIn("changed.py", result.detail)

    def test_quick_cannot_claim_postgres(self) -> None:
        self.assertEqual(project_health.main(["--quick", "--include-postgres"]), 2)


if __name__ == "__main__":
    unittest.main()
