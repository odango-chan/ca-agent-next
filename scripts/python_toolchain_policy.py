"""Fail-closed CI policy for the ca-agent-next root Python toolchain.

This script uses only the Python standard library. It validates the PR base
against the shared uv baseline and inspects only newly added executable lines.
The policy snapshot and baseline manifest must be loaded from the PR base for
ordinary PRs; the bootstrap PR is the sole exception.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterable

BASELINE_MANIFEST_PATH = ".github/python-toolchain-baseline.json"

ROOT_TOOLCHAIN_FILES = {
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    ".gitignore",
    BASELINE_MANIFEST_PATH,
}
ROOT_LOCKFILE_NAMES = {
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "conda-lock.yml",
    "conda-lock.yaml",
    "environment.yml",
    "environment.yaml",
}
EXECUTABLE_SUFFIXES = {
    ".py", ".sh", ".bash", ".ps1", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".bat", ".cmd",
}
DEPENDENCY_SURFACE_KEYS = {
    "requires-python",
    "dependencies",
    "optional-dependencies",
}
UV_DEPENDENCY_KEYS = {
    "sources",
    "index",
    "indexes",
    "constraint-dependencies",
    "override-dependencies",
    "conflicts",
    "dev-dependencies",
}
FORBIDDEN_COMMANDS = (
    (
        "PIP_INSTALL",
        re.compile(
            r"\b(?:python(?:\d+(?:\.\d+)?)?\s+-m\s+pip|pip(?:3)?)\s+install\b"
            r"|\bpip-(?:compile|sync)\b",
            re.IGNORECASE,
        ),
        "禁止使用 pip 安装入口；请更新 pyproject.toml/uv.lock 并使用 uv sync。",
    ),
    (
        "ALTERNATE_PACKAGE_MANAGER",
        re.compile(
            r"\b(?:poetry\s+(?:install|lock)|conda\s+(?:install|env\s+create)|"
            r"mamba\s+(?:install|env\s+create))\b",
            re.IGNORECASE,
        ),
        "禁止引入 Poetry/Conda/Mamba 第二套根项目依赖管理入口。",
    ),
)
BARE_PYTHON_PROJECT_COMMAND = re.compile(
    r"\bpython(?:\d+(?:\.\d+)?)?\s+"
    r"(?:-m\s+(?:unittest|pytest|compileall|ca_agent_next)\b|"
    r"(?:scripts|tests)/)",
    re.IGNORECASE,
)
BARE_TEST_RUNNER = re.compile(r"(?<![\w./-])pytest(?:\s|$)", re.IGNORECASE)
PROJECT_RUN_MARKERS = re.compile(
    r"\bpython(?:\d+(?:\.\d+)?)?\s+"
    r"(?:-m\s+(?:unittest|pytest|compileall|ca_agent_next)\b|"
    r"(?:scripts|tests)/)|(?<![\w./-])pytest(?:\s|$)",
    re.IGNORECASE,
)


class PolicyError(RuntimeError):
    """A fail-closed toolchain policy violation."""


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise PolicyError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def git_blob(repo_root: Path, revision: str, path: str) -> str | None:
    result = run_git(repo_root, "show", f"{revision}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def is_root_lockfile(path: str) -> bool:
    candidate = Path(path)
    if candidate.parent != Path("."):
        return False
    name = candidate.name.lower()
    return (
        name.startswith("requirements") and name.endswith(".txt")
    ) or candidate.name in ROOT_LOCKFILE_NAMES


def is_python_scope_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in ROOT_TOOLCHAIN_FILES or is_root_lockfile(normalized):
        return True
    if normalized.startswith(("src/", "tests/")):
        return True
    if normalized.startswith("scripts/") and normalized.endswith(".py"):
        return True
    if normalized.startswith(".github/workflows/") and normalized.endswith((".yml", ".yaml")):
        return True
    if normalized.startswith(".github/scripts/") and normalized.endswith(".py"):
        return True
    return False


def extract_added_lines(diff_text: str) -> list[tuple[str, str]]:
    current_path: str | None = None
    added: list[tuple[str, str]] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if current_path is not None:
                added.append((current_path, line[1:]))
    return added


def forbidden_root_lockfiles(changed_paths: Iterable[str]) -> list[str]:
    return sorted(path for path in changed_paths if is_root_lockfile(path))


def command_violations(added_lines: Iterable[tuple[str, str]]) -> list[str]:
    violations: list[str] = []
    for path, raw_line in added_lines:
        if Path(path).suffix.lower() not in EXECUTABLE_SUFFIXES:
            continue
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "REM ")):
            continue

        for code, pattern, message in FORBIDDEN_COMMANDS:
            if pattern.search(line):
                violations.append(f"{code}: {path}: {line} — {message}")
        if re.search(r"\\bUV_PROJECT_ENVIRONMENT\\s*=", line):
            violations.append(
                f"SHARED_UV_ENVIRONMENT: {path}: {line} — "
                "每个 worktree 必须使用本地 .venv，禁止设置共享 UV_PROJECT_ENVIRONMENT。"
            )
        if re.search(r"\\buv\\s+(?:run|sync)\\b.*(?:--system|--active)\\b", line):
            violations.append(
                f"UV_ENVIRONMENT_BYPASS: {path}: {line} — "
                "禁止使用 --system/--active 绕过项目虚拟环境。"
            )

        has_uv_run = re.search(r"\buv\s+run\b", line) is not None
        has_no_project = "--no-project" in line
        if PROJECT_RUN_MARKERS.search(line):
            if not has_uv_run:
                if BARE_PYTHON_PROJECT_COMMAND.search(line) or BARE_TEST_RUNNER.search(line):
                    violations.append(
                        f"BARE_PYTHON_ENTRY: {path}: {line} — "
                        "项目测试/Smoke/脚本必须经 uv run 执行。"
                    )
            elif not has_no_project and (
                "--no-sync" not in line or "--locked" not in line
            ):
                violations.append(
                    f"UV_RUN_NOT_LOCKED: {path}: {line} — "
                    "项目命令必须同时使用 uv run --no-sync --locked。"
                )
    return violations


def dependency_surface(pyproject_text: str) -> dict[str, Any]:
    data = tomllib.loads(pyproject_text)
    project = data.get("project", {})
    uv = data.get("tool", {}).get("uv", {})
    return {
        "project": {
            key: project.get(key)
            for key in sorted(DEPENDENCY_SURFACE_KEYS)
        },
        "dependency-groups": data.get("dependency-groups", {}),
        "tool.uv": {
            key: uv.get(key)
            for key in sorted(UV_DEPENDENCY_KEYS)
            if key in uv
        },
    }


def validate_base_ref(
    manifest: dict[str, Any],
    base_ref: str,
    base_sha: str,
    pr_number: int,
) -> None:
    baseline = manifest.get("baseline", {})
    bootstrap = manifest.get("bootstrap", {})
    baseline_sha = baseline.get("sha")

    if not isinstance(baseline_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", baseline_sha):
        raise PolicyError("基线清单缺少有效的 40 位 baseline.sha。")

    if pr_number == bootstrap.get("pr_number"):
        if (
            base_ref != bootstrap.get("base_ref")
            or base_sha != bootstrap.get("base_sha")
            or baseline_sha != bootstrap.get("base_sha")
        ):
            raise PolicyError(
                "PR #112 仅允许从固定的 SR-028 实施基线引导门禁；"
                "Base ref/SHA 或 baseline SHA 已漂移。"
            )
        return

    allowed = manifest.get("allowed_base_refs", [])
    if base_ref not in allowed:
        raise PolicyError(
            f"PR Base {base_ref!r} 不在允许的共享基线分支列表中：{allowed!r}。"
        )


def validate_base_contents(
    repo_root: Path,
    base_sha: str,
    manifest: dict[str, Any],
) -> None:
    baseline_sha = manifest["baseline"]["sha"]
    ancestry = run_git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        baseline_sha,
        base_sha,
        check=False,
    )
    if ancestry.returncode != 0:
        raise PolicyError(
            f"PR Base {base_sha} 不包含共享 uv 基线 {baseline_sha}；"
            "禁止从旧 main/设计分支直接实施 Python 变更。"
        )

    required = manifest.get("required_base_files", [])
    for path in required:
        content = git_blob(repo_root, base_sha, path)
        if content is None:
            raise PolicyError(f"共享基线缺少必需文件：{path}")

    python_version = git_blob(repo_root, base_sha, ".python-version")
    if python_version is None or python_version.strip() != manifest.get("python_version"):
        raise PolicyError(
            f"PR Base 的 .python-version 必须为 {manifest.get('python_version')}。"
        )

    pyproject = git_blob(repo_root, base_sha, "pyproject.toml") or ""
    required_uv = f'required-version = "=={manifest.get("uv_version")}"'
    if required_uv not in pyproject:
        raise PolicyError(f"PR Base 的 pyproject.toml 未固定 uv {manifest.get('uv_version')}。")

    workflow_paths = [
        path
        for path in required
        if path.startswith(".github/workflows/")
    ]
    for path in workflow_paths:
        workflow = git_blob(repo_root, base_sha, path) or ""
        if manifest.get("uv_setup_action") not in workflow:
            raise PolicyError(f"PR Base 的 {path} 未使用固定 SHA 的 setup-uv action。")
        if f"version: '{manifest.get('uv_version')}'" not in workflow:
            raise PolicyError(f"PR Base 的 {path} 未显式固定 uv 版本。")


def validate_dependency_lock(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    changed_paths: set[str],
) -> list[str]:
    if "pyproject.toml" not in changed_paths:
        return []
    base_text = git_blob(repo_root, base_sha, "pyproject.toml")
    head_text = git_blob(repo_root, head_sha, "pyproject.toml")
    if base_text is None or head_text is None:
        return ["DEPENDENCY_LOCK: 无法读取 Base/Head 的 pyproject.toml。"]
    try:
        changed = dependency_surface(base_text) != dependency_surface(head_text)
    except (tomllib.TOMLDecodeError, TypeError) as exc:
        return [f"DEPENDENCY_LOCK: pyproject.toml 解析失败：{exc}"]
    if changed and "uv.lock" not in changed_paths:
        return [
            "DEPENDENCY_LOCK: pyproject.toml 的 Python 依赖/解释器/uv 解析配置发生变化，"
            "但同一 PR 未更新 uv.lock。"
        ]
    return []


def evaluate(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    base_ref: str,
    pr_number: int,
    manifest: dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    validate_base_ref(manifest, base_ref, base_sha, pr_number)
    validate_base_contents(repo_root, base_sha, manifest)

    changed_result = run_git(
        repo_root,
        "diff",
        "--name-only",
        "--no-renames",
        f"{base_sha}...{head_sha}",
    )
    changed_paths = {
        item.strip()
        for item in changed_result.stdout.splitlines()
        if item.strip()
    }
    if not any(is_python_scope_path(path) for path in changed_paths):
        return True, [], sorted(changed_paths)

    lockfiles = forbidden_root_lockfiles(changed_paths)
    violations = [
        f"SECOND_LOCKFILE: {path} — 根 Python 工程只允许 pyproject.toml + uv.lock。"
        for path in lockfiles
    ]

    diff = run_git(
        repo_root,
        "diff",
        "--no-ext-diff",
        "--unified=0",
        f"{base_sha}...{head_sha}",
    ).stdout
    violations.extend(command_violations(extract_added_lines(diff)))
    violations.extend(
        validate_dependency_lock(repo_root, base_sha, head_sha, changed_paths)
    )
    return not violations, violations, sorted(changed_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Next root Python uv toolchain policy gate")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--baseline-file", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        manifest = json.loads(args.baseline_file.read_text(encoding="utf-8"))
        ok, violations, changed_paths = evaluate(
            args.repo_root.resolve(),
            args.base_sha,
            args.head_sha,
            args.base_ref,
            args.pr_number,
            manifest,
        )
    except (OSError, json.JSONDecodeError, PolicyError, KeyError) as exc:
        print(f"PYTHON_TOOLCHAIN_POLICY_FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PR #{args.pr_number}: base={args.base_ref}@{args.base_sha}")
    print(f"Head: {args.head_sha}")
    print(f"Changed files: {len(changed_paths)}")
    if not any(is_python_scope_path(path) for path in changed_paths):
        print("PYTHON_TOOLCHAIN_POLICY_SKIP: no Next root Python files/workflows changed.")
        return 0
    if violations:
        for item in violations:
            print(f"::error::{item}")
        print("PYTHON_TOOLCHAIN_POLICY_FAIL")
        return 1
    print("PYTHON_TOOLCHAIN_POLICY_PASS")
    print("Shared uv baseline, dependency lock, and added command checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
