from __future__ import annotations

import unittest

from scripts.python_toolchain_policy import (
    PolicyError,
    command_violations,
    dependency_surface,
    extract_added_lines,
    forbidden_root_lockfiles,
    is_python_scope_path,
    validate_base_ref,
)


class PythonToolchainPolicyTests(unittest.TestCase):
    def test_python_scope_includes_root_python_and_workflows(self) -> None:
        for path in (
            "src/ca_agent_next/host.py",
            "tests/test_host.py",
            "scripts/review_context.py",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            ".github/workflows/review-context.yml",
        ):
            with self.subTest(path=path):
                self.assertTrue(is_python_scope_path(path))

    def test_python_scope_excludes_docs_and_go_example(self) -> None:
        for path in (
            "README.md",
            "docs/SR/SR-028-example.md",
            "examples/echo/plugin/main.go",
        ):
            with self.subTest(path=path):
                self.assertFalse(is_python_scope_path(path))

    def test_root_alternate_lockfiles_are_rejected_but_nested_fixtures_are_not(self) -> None:
        self.assertEqual(
            forbidden_root_lockfiles(
                {
                    "requirements.txt",
                    "requirements-dev.txt",
                    "poetry.lock",
                    "tests/fixtures/requirements.txt",
                    "uv.lock",
                }
            ),
            ["poetry.lock", "requirements-dev.txt", "requirements.txt"],
        )

    def test_pip_install_is_rejected(self) -> None:
        line = "pip" + " install requests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_python_module_pip_is_rejected(self) -> None:
        line = "python -m " + "pip install requests"
        found = command_violations([("scripts/setup.py", line)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_bare_unittest_is_rejected(self) -> None:
        line = "python -m " + "unittest discover -s tests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_uv_locked_unittest_is_allowed(self) -> None:
        line = (
            "uv run --no-sync --locked --group dev --extra plugins "
            "python -m unittest discover -s tests"
        )
        self.assertEqual(command_violations([(".github/workflows/ci.yml", line)]), [])

    def test_uv_no_project_policy_test_is_allowed(self) -> None:
        line = "uv run --no-project --python 3.14.6 python -m unittest discover -s tests"
        self.assertEqual(command_violations([(".github/workflows/ci.yml", line)]), [])

    def test_uv_project_test_without_locked_flags_is_rejected(self) -> None:
        line = "uv run python -m unittest discover -s tests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("UV_RUN_NOT_LOCKED" in item for item in found))

    def test_extract_added_lines_ignores_removed_lines_and_headers(self) -> None:
        diff = (
            "diff --git a/a.yml b/a.yml\n"
            "--- a/a.yml\n"
            "+++ b/a.yml\n"
            "@@ -1 +1 @@\n"
            "-pip install old\n"
            "+uv run --no-sync --locked python -m unittest\n"
        )
        self.assertEqual(
            extract_added_lines(diff),
            [("a.yml", "uv run --no-sync --locked python -m unittest")],
        )

    def test_dependency_surface_tracks_project_and_uv_dependency_fields(self) -> None:
        base = """
[project]
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest>=8"]

[tool.uv]
required-version = "==0.13.10"
"""
        changed = base.replace('dev = ["pytest>=8"]', 'dev = ["pytest>=9"]')
        self.assertNotEqual(dependency_surface(base), dependency_surface(changed))
        self.assertEqual(dependency_surface(base), dependency_surface(base))

    def test_bootstrap_pr_requires_exact_fixed_base(self) -> None:
        manifest = {
            "baseline": {"sha": "a" * 40},
            "bootstrap": {
                "pr_number": 112,
                "base_ref": "feature/sr028",
                "base_sha": "a" * 40,
            },
            "allowed_base_refs": ["docs/shared-uv", "main"],
        }
        validate_base_ref(manifest, "feature/sr028", "a" * 40, 112)
        with self.assertRaises(PolicyError):
            validate_base_ref(manifest, "main", "a" * 40, 112)

    def test_regular_pr_requires_an_approved_base_ref(self) -> None:
        manifest = {
            "baseline": {"sha": "a" * 40},
            "bootstrap": {"pr_number": 112, "base_ref": "feature/sr028", "base_sha": "a" * 40},
            "allowed_base_refs": ["docs/shared-uv", "main"],
        }
        validate_base_ref(manifest, "docs/shared-uv", "b" * 40, 113)
        with self.assertRaises(PolicyError):
            validate_base_ref(manifest, "old-design-branch", "b" * 40, 113)


if __name__ == "__main__":
    unittest.main()
