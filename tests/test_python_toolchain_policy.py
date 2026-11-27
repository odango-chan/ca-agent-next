from __future__ import annotations

import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_policy_path = Path(__file__).resolve().parents[1] / "scripts" / "python_toolchain_policy.py"
_policy_spec = spec_from_file_location("ca_agent_next_python_toolchain_policy", _policy_path)
if _policy_spec is None or _policy_spec.loader is None:
    raise RuntimeError(f"cannot load Python toolchain policy from {_policy_path}")
_policy_module = module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(_policy_module)

PolicyError = _policy_module.PolicyError
command_violations = _policy_module.command_violations
dependency_surface = _policy_module.dependency_surface
extract_added_lines = _policy_module.extract_added_lines
forbidden_root_lockfiles = _policy_module.forbidden_root_lockfiles
is_python_scope_path = _policy_module.is_python_scope_path
validate_base_ref = _policy_module.validate_base_ref


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

    def test_go_only_workflow_is_not_python_scope(self) -> None:
        self.assertFalse(
            is_python_scope_path(
                ".github/workflows/go-release.yml",
                "name: Go Release\\non: push\\njobs:\\n  build:\\n    steps:\\n      - run: go test ./...",
            )
        )

    def test_new_python_workflow_is_python_scope_by_content(self) -> None:
        self.assertTrue(
            is_python_scope_path(
                ".github/workflows/python-tests.yml",
                "name: Python tests\\njobs:\\n  test:\\n    steps:\\n      - run: uv run " + "pytest",
            )
        )

    def test_root_alternate_lockfiles_are_rejected_but_nested_fixtures_are_not(self) -> None:
        self.assertEqual(
            forbidden_root_lockfiles(
                {
                    "requirements.txt",
                    "requirements-dev.txt",
                    "poetry.lock",
                    "Pipfile.lock",
                    "conda-lock.yaml",
                    "environment.yaml",
                    "tests/fixtures/requirements.txt",
                    "uv.lock",
                }
            ),
            ["Pipfile.lock", "conda-lock.yaml", "environment.yaml", "poetry.lock", "requirements-dev.txt", "requirements.txt"],
        )

    def test_pip_install_is_rejected(self) -> None:
        line = "pip" + " install requests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_python_module_pip_is_rejected(self) -> None:
        line = "python -m " + "pip" + " install requests"
        found = command_violations([("scripts/setup.py", line)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_bare_unittest_is_rejected(self) -> None:
        line = "python -m " + "unittest discover -s tests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_uv_locked_unittest_is_allowed(self) -> None:
        line = (
            "uv run --no-sync --locked --group dev --extra plugins " +
            "python -m " + "unittest discover -s tests"
        )
        self.assertEqual(command_violations([(".github/workflows/ci.yml", line)]), [])

    def test_uv_no_project_policy_test_is_allowed(self) -> None:
        line = (
            "uv run --no-project --python 3.14.6 "
            + "python -m "
            + "unittest discover -s tests -p test_python_toolchain_policy.py"
        )
        self.assertEqual(
            command_violations([(".github/workflows/python-toolchain-policy.yml", line)]),
            [],
        )

    def test_uv_no_project_cannot_run_application_tests(self) -> None:
        line = (
            "uv run --no-project --python 3.14.6 "
            + "python -m "
            + "unittest discover -s tests"
        )
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("UV_NO_PROJECT_BYPASS" in item for item in found))

    def test_windows_py_launcher_is_rejected_without_uv(self) -> None:
        line = "py -m " + "unittest discover -s tests"
        found = command_violations([(".github/workflows/windows.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_bare_python_script_is_rejected(self) -> None:
        line = "python " + "scripts/custom_check.py"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_no_project_is_limited_to_policy_checker_script(self) -> None:
        line = (
            "uv run --no-project --python 3.14.6 python "
            + '"$policy_dir/'
            + "python_toolchain_policy.py"
            + '"'
        )
        self.assertEqual(
            command_violations([(".github/workflows/python-toolchain-policy.yml", line)]),
            [],
        )

    def test_no_project_cannot_run_arbitrary_python_script(self) -> None:
        line = (
            "uv run --no-project --python 3.14.6 python "
            + "scripts/application_task.py"
        )
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("UV_NO_PROJECT_BYPASS" in item for item in found))

    def test_uv_project_test_without_locked_flags_is_rejected(self) -> None:
        line = "uv run " + "python -m " + "unittest discover -s tests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("UV_RUN_NOT_LOCKED" in item for item in found))

    def test_policy_source_is_not_exempt_from_command_scanning(self) -> None:
        line = "pip" + " install requests"
        found = command_violations([("scripts/python_toolchain_policy.py", line)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_shared_uv_environment_override_is_rejected(self) -> None:
        assignment = "UV_PROJECT_" + "ENVIRONMENT=/tmp/shared-venv"
        found = command_violations([(".github/workflows/ci.yml", assignment)])
        self.assertTrue(any("SHARED_UV_ENVIRONMENT" in item for item in found))

    def test_uv_system_bypass_is_rejected(self) -> None:
        line = "uv run " + "--" + "system " + "python -m " + "unittest discover -s tests"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("UV_ENVIRONMENT_BYPASS" in item for item in found))

    def test_extract_added_lines_ignores_removed_lines_and_headers(self) -> None:
        diff = (
            "diff --git a/a.yml b/a.yml\n"
            "--- a/a.yml\n"
            "+++ b/a.yml\n"
            "@@ -1 +1 @@\n"
            "-pip" + " install old\n"
            "+uv run --no-sync --locked python -m " + "unittest\n"
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
