from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
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
is_policy_gate_no_project = _policy_module.is_policy_gate_no_project
policy_control_file_violations = _policy_module.policy_control_file_violations
validate_base_ref = _policy_module.validate_base_ref
workflow_toolchain_violations = _policy_module.workflow_toolchain_violations


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

    def test_python_command_build_files_are_scoped_by_content(self) -> None:
        makefile = "test:\\n  uv " + "run " + "py" + "test"
        self.assertTrue(is_python_scope_path("Makefile", makefile))
        self.assertTrue(is_python_scope_path("Dockerfile", "FROM python:3.14"))
        self.assertFalse(is_python_scope_path("Makefile", "build:\\n  go test ./..."))

    def test_shell_launchers_are_scoped_by_python_command_content(self) -> None:
        launcher = "uv " + "run " + "python -m " + "unittest"
        powershell = "python -m " + "unittest"
        self.assertTrue(is_python_scope_path("scripts/test.sh", launcher))
        self.assertTrue(is_python_scope_path(".github/scripts/test.ps1", powershell))
        self.assertFalse(is_python_scope_path("scripts/build.sh", "go test ./..."))

    def test_go_only_workflow_is_not_python_scope(self) -> None:
        self.assertFalse(
            is_python_scope_path(
                ".github/workflows/go-release.yml",
                "name: Go Release\\non: push\\njobs:\\n  build:\\n    steps:\\n      - run: go test ./...",
            )
        )

    def test_new_python_workflow_is_python_scope_by_content(self) -> None:
        workflow = (
            "name: Python tests\\njobs:\\n  test:\\n    steps:\\n      - run: uv "
            + "run "
            + "py"
            + "test"
        )
        self.assertTrue(is_python_scope_path(".github/workflows/python-tests.yml", workflow))

    def test_root_alternate_lockfiles_are_rejected_but_nested_fixtures_are_not(self) -> None:
        self.assertEqual(
            forbidden_root_lockfiles(
                {
                    "requirements.txt",
                    "requirements-dev.txt",
                    "requirements-dev.in",
                    "constraints.txt",
                    "poetry.lock",
                    "Pipfile.lock",
                    "pdm.lock",
                    "rye.lock",
                    "conda-lock.yaml",
                    "environment.yaml",
                    "tests/fixtures/requirements.txt",
                    "uv.lock",
                }
            ),
            ["Pipfile.lock", "conda-lock.yaml", "constraints.txt", "environment.yaml", "pdm.lock", "poetry.lock", "requirements-dev.in", "requirements-dev.txt", "requirements.txt", "rye.lock"],
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
            + "unittest discover -s tests -p test_python_toolchain_policy.py -v"
        )
        self.assertEqual(
            command_violations([(".github/workflows/python-toolchain-policy.yml", line)]),
            [],
        )
        self.assertTrue(
            is_policy_gate_no_project(".github/workflows/python-toolchain-policy.yml", line)
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

    def test_bare_python_script_outside_scripts_directory_is_rejected(self) -> None:
        line = "python " + "tools/custom_check.py"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_makefile_python_entry_is_scanned(self) -> None:
        found = command_violations([("Makefile", "python " + "tools/custom_check.py")])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_uv_pip_sync_is_rejected(self) -> None:
        command = "uv " + "pip" + " sync requirements.txt"
        found = command_violations([(".github/workflows/ci.yml", command)])
        self.assertTrue(any("PIP_INSTALL" in item for item in found))

    def test_uv_sync_requires_locked(self) -> None:
        unlocked = "uv " + "sync --group dev"
        locked = "uv " + "sync --locked --group dev"
        found = command_violations([(".github/workflows/ci.yml", unlocked)])
        self.assertTrue(any("UV_SYNC_NOT_LOCKED" in item for item in found))
        self.assertEqual(command_violations([(".github/workflows/ci.yml", locked)]), [])

    def test_no_project_checker_allowlist_rejects_command_chaining(self) -> None:
        prefix = "uv " + "run --no-project --python 3.14.6 "
        checker = 'python "$policy_dir/' + "python_toolchain_policy.py" + '" \\'
        application = " && python " + "scripts/application.py"
        line = prefix + checker + application
        found = command_violations([(".github/workflows/python-toolchain-policy.yml", line)])
        self.assertTrue(any("UV_NO_PROJECT_BYPASS" in item for item in found))

    def test_policy_control_files_are_rejected_for_regular_prs(self) -> None:
        manifest = {"bootstrap": {"pr_number": 112}}
        found = policy_control_file_violations(
            {
                "scripts/python_toolchain_policy.py",
                ".github/python-toolchain-baseline.json",
            },
            113,
            manifest,
        )
        self.assertTrue(any("POLICY_SOURCE_CHANGE" in item for item in found))

    def test_bootstrap_pr_may_add_policy_control_files(self) -> None:
        manifest = {"bootstrap": {"pr_number": 112}}
        self.assertEqual(
            policy_control_file_violations(
                {"scripts/python_toolchain_policy.py", ".github/python-toolchain-baseline.json"},
                112,
                manifest,
            ),
            [],
        )

    def test_python_workflow_requires_pinned_setup_uv(self) -> None:
        manifest = {
            "uv_setup_action": "astral-sh/setup-uv@abc123",
            "uv_version": "0.13.10",
        }
        invalid = workflow_toolchain_violations(
            ".github/workflows/python-tests.yml",
            "name: Python tests\n"
            + "jobs:\n  test:\n    steps:\n"
            + "      - name: Run tests\n        run: uv " + "run " + "pytest\n",
            manifest,
        )
        self.assertEqual(len(invalid), 2)
        valid = workflow_toolchain_violations(
            ".github/workflows/python-tests.yml",
            "name: Python tests\n"
            + "jobs:\n  test:\n    steps:\n"
            + "      - name: Set up uv\n"
            + "        uses: astral-sh/setup-uv@abc123\n"
            + "        with:\n"
            + "          version: '0.13.10'\n"
            + "      - name: Run tests\n"
            + "        run: uv " + "run --no-sync --locked pytest\n",
            manifest,
        )
        self.assertEqual(valid, [])

    def test_setup_uv_version_must_be_in_the_matching_step(self) -> None:
        manifest = {
            "uv_setup_action": "astral-sh/setup-uv@abc123",
            "uv_version": "0.13.10",
        }
        content = (
            "jobs:\n  test:\n    steps:\n"
            "      - name: Set up uv\n"
            "        uses: astral-sh/setup-uv@abc123\n"
            "      - name: Unrelated version\n"
            "        with:\n"
            "          version: '0.13.10'\n"
            "      - name: Run Python tests\n"
            "        run: uv " + "run --no-sync --locked ruff check\n"
        )
        found = workflow_toolchain_violations(
            ".github/workflows/python-tests.yml", content, manifest
        )
        self.assertTrue(any("WORKFLOW_UV_VERSION" in item for item in found))

    def test_setup_uv_string_outside_step_does_not_satisfy_policy(self) -> None:
        manifest = {
            "uv_setup_action": "astral-sh/setup-uv@abc123",
            "uv_version": "0.13.10",
        }
        content = (
            "name: Python tests\n"
            "env:\n"
            "  NOTE: astral-sh/setup-uv@abc123\n"
            "  version: '0.13.10'\n"
            "jobs:\n  test:\n    steps:\n"
            "      - name: Run tests\n"
            "        run: echo 'version: 0.13.10'\n"
        )
        found = workflow_toolchain_violations(
            ".github/workflows/python-tests.yml", content, manifest
        )
        self.assertEqual(len(found), 2)

    def test_every_uv_run_tool_requires_locked_project_flags(self) -> None:
        commands = (
            "uv run ruff check .",
            "uv run mypy src",
            "uv run --no-project ruff check .",
            "uv run ruff check --no-sync --locked",
        )
        for command in commands:
            with self.subTest(command=command):
                found = command_violations([("scripts/ci.sh", command)])
                self.assertTrue(
                    any(
                        "UV_RUN_NOT_LOCKED" in item
                        or "UV_NO_PROJECT_BYPASS" in item
                        for item in found
                    )
                )
        allowed = command_violations([
            ("scripts/ci.sh", "uv run --no-sync --locked ruff check .")
        ])
        self.assertEqual(allowed, [])

    def test_each_uv_run_in_a_chained_command_is_checked(self) -> None:
        line = (
            "uv run --no-sync --locked ruff check ."
            " && uv run mypy src"
        )
        found = command_violations([("scripts/ci.sh", line)])
        self.assertTrue(any("UV_RUN_NOT_LOCKED" in item for item in found))

    def test_quoted_workflow_run_commands_require_locked_flags(self) -> None:
        invalid = command_violations([
            (".github/workflows/python-tests.yml", 'run: "uv run ruff check ."')
        ])
        self.assertTrue(any("UV_RUN_NOT_LOCKED" in item for item in invalid))
        valid = command_violations([
            (
                ".github/workflows/python-tests.yml",
                'run: "uv run --no-sync --locked ruff check ."',
            )
        ])
        self.assertEqual(valid, [])
    def test_bare_python_script_is_rejected(self) -> None:
        line = "python " + "scripts/custom_check.py"
        found = command_violations([(".github/workflows/ci.yml", line)])
        self.assertTrue(any("BARE_PYTHON_ENTRY" in item for item in found))

    def test_no_project_is_limited_to_policy_checker_script(self) -> None:
        line = (
            "uv run --no-project --python 3.14.6 python "
            + '"$policy_dir/'
            + "python_toolchain_policy.py"
            + '" \\'
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

    def test_dependency_surface_tracks_uv_resolver_fields(self) -> None:
        base = """
[project]
requires-python = ">=3.11"
dependencies = []

[tool.uv]
required-version = "==0.13.10"
index-strategy = "first-index"
"""
        changed = base.replace('index-strategy = "first-index"', 'index-strategy = "unsafe-first-match"')
        self.assertNotEqual(dependency_surface(base), dependency_surface(changed))

    def test_pep751_root_lockfiles_trigger_scope_and_rejection(self) -> None:
        for path in ("pylock.toml", "pylock.dev.toml", "pylock.dev.windows.toml"):
            with self.subTest(path=path):
                self.assertTrue(is_python_scope_path(path))
                self.assertTrue(
                    _policy_module.has_python_scope(Path("."), "a" * 40, "b" * 40, [path])
                )
                self.assertEqual(forbidden_root_lockfiles([path]), [path])
        self.assertEqual(forbidden_root_lockfiles(["tests/fixtures/pylock.dev.toml"]), [])

    def test_live_base_tip_matches_event_snapshot(self) -> None:
        with patch.object(
            _policy_module, "run_git",
            return_value=SimpleNamespace(returncode=0, stdout="a" * 40 + "\n"),
        ) as fake:
            _policy_module.validate_base_tip(Path("."), "feature/sr028", "a" * 40)
            fake.assert_called_once_with(
                Path("."), "rev-parse", "--verify",
                "refs/remotes/origin/feature/sr028", check=False,
            )

    def test_moved_or_unfetched_base_branch_is_rejected(self) -> None:
        for return_code, remote_sha in ((0, "b" * 40 + "\n"), (128, "")):
            with self.subTest(return_code=return_code):
                with patch.object(
                    _policy_module, "run_git",
                    return_value=SimpleNamespace(returncode=return_code, stdout=remote_sha),
                ):
                    with self.assertRaisesRegex(PolicyError, "STALE_BASE"):
                        _policy_module.validate_base_tip(Path("."), "feature/sr028", "a" * 40)

    def test_windows_launcher_module_pip_is_rejected(self) -> None:
        for command in (
            "py -m " + "pip" + " install requests",
            "py.exe -m " + "pip" + " install requests",
        ):
            with self.subTest(command=command):
                self.assertTrue(any(
                    "PIP_INSTALL" in violation
                    for violation in command_violations([("scripts/setup.ps1", command)])
                ))

    def test_shell_continuation_cannot_hide_install(self) -> None:
        lines = [
            ("scripts/setup.sh", "pip" + " \\"),
            ("scripts/setup.sh", "  install requests"),
        ]
        self.assertTrue(any("PIP_INSTALL" in item for item in command_violations(lines)))

    def test_alternate_package_manager_mutations_are_rejected(self) -> None:
        commands = (
            "poetry" + " add requests",
            "poetry" + " update",
            "conda env" + " update -f env.yaml",
            "mamba" + " update --all",
            "micromamba env" + " create -f environment.yml",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(any(
                    "ALTERNATE_PACKAGE_MANAGER" in violation
                    for violation in command_violations([(".github/workflows/ci.yml", command)])
                ))

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
