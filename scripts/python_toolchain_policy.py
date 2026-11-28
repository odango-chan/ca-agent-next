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
    "pipfile",
    "pipfile.lock",
    "poetry.lock",
    "conda-lock.yml",
    "conda-lock.yaml",
    "environment.yml",
    "environment.yaml",
    "pdm.lock",
    "rye.lock",
    "pixi.lock",
}
EXECUTABLE_SUFFIXES = {
    ".py", ".sh", ".bash", ".ps1", ".psm1", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".bat", ".cmd", ".fish", ".zsh", ".mk",
}
EXECUTABLE_NAMES = {"makefile", "dockerfile", "justfile"}
POLICY_CONTROL_FILES = {
    BASELINE_MANIFEST_PATH,
    "scripts/python_toolchain_policy.py",
    ".github/workflows/python-toolchain-policy.yml",
    ".github/workflows/python-toolchain-policy-trusted.yml",
    "tests/test_python_toolchain_policy.py",
}
DEPENDENCY_SURFACE_KEYS = {
    "requires-python",
    "dependencies",
    "optional-dependencies",
    "dynamic",
}
UV_DEPENDENCY_KEYS = {
    "sources",
    "index",
    "indexes",
    "constraint-dependencies",
    "build-constraint-dependencies",
    "override-dependencies",
    "conflicts",
    "dev-dependencies",
    "default-groups",
    "dependency-metadata",
    "environments",
    "exclude-newer",
    "index-strategy",
    "no-build",
    "no-build-isolation",
    "no-build-isolation-package",
    "no-binary",
    "required-environments",
    "resolution",
    "prerelease",
    "python-preference",
    "python-downloads",
    "link-mode",
    "managed",
    "package",
    "workspace",
    "required-version",
}
FORBIDDEN_COMMANDS = (
    (
        "PIP_INSTALL",
        re.compile(
            r"\b(?:(?:python(?:\d+(?:\.\d+)?)?|py(?:\.exe)?)\s+-m\s+pip|pip(?:3(?:\.\d+)?)?)\s+"
            r"(?:install|sync|compile)\b"
            r"|\bpip-(?:compile|sync)\b"
            r"|\bpipenv\s+(?:install|sync|lock)\b",
            re.IGNORECASE,
        ),
        "禁止使用 pip 安装入口；请更新 pyproject.toml/uv.lock 并通过 uv 管理依赖同步。",
    ),
    (
        "ALTERNATE_PACKAGE_MANAGER",
        re.compile(
            r"\b(?:poetry\s+(?:install|lock|add|remove|update|sync)|(?:conda|mamba|micromamba)\s+(?:install|create|update|remove|env\s+(?:create|update|remove))|"
            r"pdm\s+(?:install|sync|lock|add)|"
            r"rye\s+(?:sync|lock|add|install)|pixi\s+(?:install|lock|add))\b",
            re.IGNORECASE,
        ),
        "禁止引入 Poetry/Conda/Mamba 第二套根项目依赖管理入口。",
    ),
)
BARE_PYTHON_PROJECT_COMMAND = re.compile(
    r"\b(?:python(?:\d+(?:\.\d+)?)?|py(?:\.exe)?)\s+"
    r"(?:-m\s+(?:unittest|pytest|compileall|ca_agent_next)\b|"
    r"(?:scripts|tests)/|[^\s]+\.py(?:\s|$))",
    re.IGNORECASE,
)
BARE_TEST_RUNNER = re.compile(r"(?<![\w./-])pytest(?:\s|$)", re.IGNORECASE)
PROJECT_RUN_MARKERS = re.compile(
    r"\b(?:python(?:\d+(?:\.\d+)?)?|py(?:\.exe)?)\s+"
    r"(?:-m\s+(?:unittest|pytest|compileall|ca_agent_next)\b|"
    r"(?:scripts|tests)/|[^\s]+\.py(?:\s|$))|(?<![\w./-])pytest(?:\s|$)",
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
        name.startswith(("requirements", "constraints"))
        and Path(name).suffix in {".txt", ".in"}
    ) or name in ROOT_LOCKFILE_NAMES or re.fullmatch(r"pylock(?:\.[a-z0-9_-]+)*\.toml", name) is not None


def is_python_scope_path(path: str, workflow_content: str = "") -> bool:
    normalized = path.replace("\\", "/")
    if normalized in ROOT_TOOLCHAIN_FILES or is_root_lockfile(normalized):
        return True
    if normalized.startswith(("src/", "tests/")):
        return True
    candidate = Path(normalized)
    if normalized.startswith("scripts/") and candidate.suffix.lower() == ".py":
        return True
    if normalized.startswith(".github/scripts/") and candidate.suffix.lower() == ".py":
        return True
    is_script_launcher = (
        normalized.startswith(("scripts/", ".github/scripts/"))
        and candidate.suffix.lower() in EXECUTABLE_SUFFIXES
    )
    is_build_command_file = (
        candidate.name.lower() in EXECUTABLE_NAMES or candidate.suffix.lower() == ".mk"
    )
    if is_script_launcher or is_build_command_file:
        lowered = workflow_content.lower()
        return any(token in lowered for token in ("python", "uv ", "pytest", "unittest", "pyproject", "pip "))
    if normalized.startswith(".github/workflows/") and normalized.endswith((".yml", ".yaml")):
        if Path(normalized).name in {
            "review-context.yml",
            "sr003-plugin-ci.yml",
            "python-toolchain-policy.yml",
            "python-toolchain-policy-trusted.yml",
        }:
            return True
        lowered = workflow_content.lower()
        return any(token in lowered for token in ("uv ", "python", "pyproject", "unittest", "pytest"))
    return False


def has_python_scope(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    changed_paths: Iterable[str],
) -> bool:
    for path in changed_paths:
        candidate = Path(path)
        inspect_content = (
            path.startswith(".github/workflows/")
            or path.startswith(("scripts/", ".github/scripts/"))
            or candidate.name.lower() in EXECUTABLE_NAMES
            or candidate.suffix.lower() == ".mk"
        )
        if inspect_content:
            content = (git_blob(repo_root, base_sha, path) or "") + "\n" + (
                git_blob(repo_root, head_sha, path) or ""
            )
            if is_python_scope_path(path, content):
                return True
        elif is_python_scope_path(path):
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


def is_policy_gate_no_project(path: str, line: str) -> bool:
    if path not in {
        ".github/workflows/python-toolchain-policy.yml",
        ".github/workflows/python-toolchain-policy-trusted.yml",
    }:
        return False
    normalized = line.strip()
    prefix = "uv " + "run --no-project --python 3.14.6 "
    allowed_commands = (
        'python "$policy_dir/' + "python_toolchain_policy.py" + '" \\',
        "python " + "scripts/" + "python_toolchain_policy.py" + " \\",
        "python -m " + "unittest discover -s tests -p " + "test_python_toolchain_policy.py -v",
    )
    return any(
        re.fullmatch(re.escape(prefix + command), normalized)
        for command in allowed_commands
    )

def command_violations(added_lines: Iterable[tuple[str, str]]) -> list[str]:
    violations: list[str] = []
    added_lines = list(added_lines)
    for path, raw_line in added_lines:
        candidate = Path(path)
        if candidate.suffix.lower() not in EXECUTABLE_SUFFIXES and candidate.name.lower() not in EXECUTABLE_NAMES:
            continue
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "REM ")):
            continue

        for code, pattern, message in FORBIDDEN_COMMANDS:
            if pattern.search(line):
                violations.append(f"{code}: {path}: {line} — {message}")
        if re.search(r"\bUV_PROJECT_ENVIRONMENT\s*=", line):
            violations.append(
                f"SHARED_UV_ENVIRONMENT: {path}: {line} — "
                "每个 worktree 必须使用本地 .venv，禁止设置共享 UV_PROJECT_ENVIRONMENT。"
            )
        if re.search(r"\buv\s+(?:run|sync)\b.*(?:--system|--active)\b", line):
            violations.append(
                f"UV_ENVIRONMENT_BYPASS: {path}: {line} — "
                "禁止使用 --system/--active 绕过项目虚拟环境。"
            )
        if re.search(r"\buv\s+sync\b", line) and "--locked" not in line:
            violations.append(
                f"UV_SYNC_NOT_LOCKED: {path}: {line} — "
                "CI/实施环境同步依赖必须显式传入 --locked。"
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
            elif has_no_project:
                if not is_policy_gate_no_project(path, line):
                    violations.append(
                        f"UV_NO_PROJECT_BYPASS: {path}: {line} — "
                        "仅门禁自身的固定标准库检查器/自测命令可使用 --no-project；"
                        "其他项目命令必须使用项目锁定环境。"
                    )
            elif "--no-sync" not in line or "--locked" not in line:
                violations.append(
                    f"UV_RUN_NOT_LOCKED: {path}: {line} — "
                    "项目命令必须同时使用 uv run --no-sync --locked。"
                )
    for path, command in shell_continuation_commands(added_lines):
        for code, pattern, message in FORBIDDEN_COMMANDS:
            if pattern.search(command):
                violations.append(f"{code}: {path}: {command} — {message}")
    return violations


def policy_control_file_violations(
    changed_paths: Iterable[str],
    pr_number: int,
    manifest: dict[str, Any],
) -> list[str]:
    if pr_number == manifest.get("bootstrap", {}).get("pr_number"):
        return []
    changed = sorted(set(changed_paths).intersection(POLICY_CONTROL_FILES))
    if not changed:
        return []
    return [
        "POLICY_SOURCE_CHANGE: "
        + ", ".join(changed)
        + " — 策略脚本、基线清单、可信 Workflow 和自测不得在普通实施 PR 中修改；"
        "需要独立的策略维护评审与授权。"
    ]


def workflow_toolchain_violations(
    path: str,
    content: str,
    manifest: dict[str, Any],
) -> list[str]:
    if not path.startswith(".github/workflows/") or not path.endswith((".yml", ".yaml")):
        return []
    if not is_python_scope_path(path, content):
        return []
    violations: list[str] = []
    action = manifest.get("uv_setup_action")
    if not isinstance(action, str) or action not in content:
        violations.append(
            f"WORKFLOW_UV_ACTION: {path} — Python Workflow 必须使用共享基线固定 SHA 的 setup-uv action。"
        )
    version = manifest.get("uv_version")
    if not isinstance(version, str) or not re.search(
        rf"(?m)^\s*version:\s*['\"]?{re.escape(version)}['\"]?\s*$",
        content,
    ):
        violations.append(
            f"WORKFLOW_UV_VERSION: {path} — Python Workflow 必须显式固定 uv {version}。"
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


def validate_base_tip(repo_root: Path, base_ref: str, base_sha: str) -> None:
    """Fail closed if the fetched live Base tip differs from the PR event snapshot."""
    remote_ref = f"refs/remotes/origin/{base_ref}"
    actual = run_git(repo_root, "rev-parse", "--verify", remote_ref, check=False)
    if actual.returncode != 0 or actual.stdout.strip() != base_sha:
        raise PolicyError(
            f"STALE_BASE: {remote_ref} is {actual.stdout.strip() or 'unavailable'}, "
            f"but PR event Base SHA is {base_sha}; refresh the PR and rerun CI."
        )


def shell_continuation_commands(added_lines: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Reconstruct adjacent added shell lines ending in backslash for command checks."""
    joined: list[tuple[str, str]] = []
    pending_path: str | None = None
    pending = ""
    for path, raw in added_lines:
        piece = raw.strip()
        if pending_path is not None and path != pending_path:
            pending_path, pending = None, ""
        if pending_path is None:
            if piece.endswith("\\"):
                pending_path, pending = path, piece[:-1].rstrip()
            continue
        continued = piece.endswith("\\")
        pending += " " + (piece[:-1].rstrip() if continued else piece)
        if not continued:
            joined.append((path, pending))
            pending_path, pending = None, ""
    return joined


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
    pr_number: int,
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

    required = list(manifest.get("required_base_files", []))
    if pr_number != manifest.get("bootstrap", {}).get("pr_number"):
        for path in manifest.get("required_policy_files", []):
            if path not in required:
                required.append(path)
    for path in required:
        content = git_blob(repo_root, base_sha, path)
        if content is None:
            raise PolicyError(f"共享基线缺少必需文件：{path}")

    root_entries = run_git(
        repo_root, "ls-tree", "--name-only", base_sha
    ).stdout.splitlines()
    existing_alternates = sorted(
        name for name in root_entries if is_root_lockfile(name)
    )
    if existing_alternates:
        raise PolicyError(
            "PR Base 已包含禁止的根级替代依赖/锁文件："
            + ", ".join(existing_alternates)
        )

    gitignore = git_blob(repo_root, base_sha, ".gitignore") or ""
    if ".venv/" not in gitignore.splitlines():
        raise PolicyError("PR Base 的 .gitignore 未忽略根本地虚拟环境 .venv/。")

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


def validate_head_contents(
    repo_root: Path,
    head_sha: str,
    manifest: dict[str, Any],
) -> None:
    required = list(manifest.get("required_base_files", []))
    for path in manifest.get("required_policy_files", []):
        if path not in required:
            required.append(path)
    for path in required:
        if git_blob(repo_root, head_sha, path) is None:
            raise PolicyError(f"PR Head 删除或缺少共享工具链必需文件：{path}")

    root_entries = run_git(repo_root, "ls-tree", "--name-only", head_sha).stdout.splitlines()
    existing_alternates = sorted(name for name in root_entries if is_root_lockfile(name))
    if existing_alternates:
        raise PolicyError(
            "PR Head 包含禁止的根级替代依赖/锁文件：" + ", ".join(existing_alternates)
        )

    gitignore = git_blob(repo_root, head_sha, ".gitignore") or ""
    if ".venv/" not in gitignore.splitlines():
        raise PolicyError("PR Head 的 .gitignore 必须继续忽略根本地虚拟环境 .venv/。")

    python_version = git_blob(repo_root, head_sha, ".python-version")
    if python_version is None or python_version.strip() != manifest.get("python_version"):
        raise PolicyError(
            f"PR Head 的 .python-version 必须保持 {manifest.get('python_version')}。"
        )

    pyproject = git_blob(repo_root, head_sha, "pyproject.toml") or ""
    required_uv = f'required-version = "=={manifest.get("uv_version")}"'
    if required_uv not in pyproject:
        raise PolicyError(
            f"PR Head 的 pyproject.toml 必须继续固定 uv {manifest.get('uv_version')}。"
        )

    for path in required:
        if path.startswith(".github/workflows/"):
            workflow = git_blob(repo_root, head_sha, path) or ""
            problems = workflow_toolchain_violations(path, workflow, manifest)
            if problems:
                raise PolicyError("; ".join(problems))


def validate_changed_python_workflows(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    changed_paths: Iterable[str],
    manifest: dict[str, Any],
) -> list[str]:
    violations: list[str] = []
    for path in sorted(changed_paths):
        if not path.startswith(".github/workflows/") or not path.endswith((".yml", ".yaml")):
            continue
        base_content = git_blob(repo_root, base_sha, path) or ""
        head_content = git_blob(repo_root, head_sha, path) or ""
        if not is_python_scope_path(path, base_content + "\n" + head_content):
            continue
        if not head_content:
            violations.append(
                f"WORKFLOW_REMOVED: {path} — 不得删除或清空根 Python 工程必需的 Python Workflow。"
            )
            continue
        violations.extend(workflow_toolchain_violations(path, head_content, manifest))
    return violations


def validate_dependency_lock(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    changed_paths: set[str],
) -> list[str]:
    if ".python-version" in changed_paths and "uv.lock" not in changed_paths:
        return [
            "DEPENDENCY_LOCK: .python-version 解释器基线发生变化，但同一 PR 未更新 uv.lock。"
        ]
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
    if not has_python_scope(repo_root, base_sha, head_sha, changed_paths):
        return True, [], sorted(changed_paths)

    validate_base_tip(repo_root, base_ref, base_sha)
    validate_base_ref(manifest, base_ref, base_sha, pr_number)
    validate_base_contents(repo_root, base_sha, pr_number, manifest)
    validate_head_contents(repo_root, head_sha, manifest)

    violations = policy_control_file_violations(changed_paths, pr_number, manifest)
    violations.extend(validate_changed_python_workflows(
        repo_root, base_sha, head_sha, changed_paths, manifest
    ))

    lockfiles = forbidden_root_lockfiles(changed_paths)
    violations.extend(
        f"SECOND_LOCKFILE: {path} — 根 Python 工程只允许 pyproject.toml + uv.lock。"
        for path in lockfiles
    )

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
    if not has_python_scope(args.repo_root.resolve(), args.base_sha, args.head_sha, changed_paths):
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
