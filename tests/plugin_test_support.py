"""SR-003 测试支持：真实 Go Echo Plugin 构建、临时包、Fake Host。

本模块只被 ``tests/test_plugin.py`` 使用，不进入生产包。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "examples" / "echo" / "plugin"
TESTS_DIR = REPO_ROOT / "tests"
GOLDEN_PATH = TESTS_DIR / "fixtures" / "echo-12-frames.jsonl"
PROVENANCE_PATH = TESTS_DIR / "fixtures" / "echo-12-frames.provenance.json"

try:  # 允许未执行 ``pip install -e .`` 时直接从仓库根运行测试
    import ca_agent_next  # noqa: F401
except ImportError:  # pragma: no cover - 取决于调用方式
    sys.path.insert(0, str(REPO_ROOT / "src"))

from ca_agent_next.contracts import (  # noqa: E402
    Event,
    HostResult,
    ModelProposal,
    Run,
)


def echo_binary_name() -> str:
    return "echo-plugin.exe" if os.name == "nt" else "echo-plugin"


def ensure_echo_binary() -> Path:
    """按固定命令构建 Go Echo Plugin。

    每次都重新构建，避免使用与当前 ``main.go`` 不一致的陈旧二进制。
    """
    binary = PLUGIN_DIR / "bin" / echo_binary_name()
    go = shutil.which("go")
    if go is None:
        if binary.is_file():
            return binary
        raise RuntimeError(
            "Go toolchain is required to build examples/echo/plugin; "
            "install Go and rebuild before running the SR-003 acceptance tests"
        )
    env = dict(os.environ)
    # 宿主环境可能存在仓库外的 go.work；构建固定为独立模块。
    env["GOWORK"] = "off"
    command = [go, "build", "-trimpath", "-o", f"bin/{binary.name}", "."]
    completed = subprocess.run(
        command,
        cwd=str(PLUGIN_DIR),
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0 or not binary.is_file():
        raise RuntimeError(
            "go build failed: " + (completed.stderr or completed.stdout).strip()
        )
    return binary


def manifest_text() -> str:
    return (PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8")


def replace_args(text: str, args: list[str] | tuple[str, ...]) -> str:
    if args:
        block = "\n".join(["  args:"] + [f"    - '{arg}'" for arg in args])
    else:
        block = "  args: []"
    updated, count = re.subn(r"(?m)^  args: \[.*\]$", block, text)
    if count != 1:
        raise AssertionError("manifest does not contain a replaceable args line")
    return updated


def copy_package(
    destination: Path,
    *,
    args: list[str] | tuple[str, ...] | None = None,
    text: str | None = None,
) -> Path:
    """把示例包复制到临时目录，并放入已构建的可执行文件。"""
    shutil.copytree(
        PLUGIN_DIR,
        destination,
        ignore=shutil.ignore_patterns("bin"),
    )
    binary_dir = destination / "bin"
    binary_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ensure_echo_binary(), binary_dir / echo_binary_name())
    manifest = manifest_text() if text is None else text
    if args is not None:
        manifest = replace_args(manifest, args)
    (destination / "plugin.yaml").write_text(manifest, encoding="utf-8")
    return destination


def write_manifest(package: Path, text: str) -> None:
    (package / "plugin.yaml").write_text(text, encoding="utf-8")


def load_golden() -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                frames.append(json.loads(line))
    return frames


def load_provenance() -> dict[str, Any]:
    return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))


def golden_sha256() -> str:
    """golden fixture 的规范化字节摘要（CRLF 折叠为 LF）。

    摘要必须与 checkout 的 ``core.autocrlf`` 设置无关：同一提交在 CRLF 与
    LF 工作区必须得到相同结果，否则“逐帧一致”的证据会退化为平台相关的
    行尾证据。``tests/fixtures/.gitattributes`` 另外固定该文件以 LF 检出。
    """
    data = GOLDEN_PATH.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def make_dir_link(link: Path, target: Path) -> str:
    """创建目录链接；Windows 无符号链接特权时退化为 junction。"""
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError):
        if os.name == "nt":
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
            )
            if completed.returncode == 0 and link.exists():
                return "junction"
        raise RuntimeError("this platform cannot create a directory link")


class FakeHost:
    """记录 Event 的 Host 替身；Manager 只依赖 ``handle_event``。"""

    def __init__(self) -> None:
        self.calls: list[Event] = []
        self.error: Exception | None = None

    def handle_event(self, event: Event) -> HostResult:
        self.calls.append(event)
        if self.error is not None:
            raise self.error
        return HostResult(
            run=Run(run_id="run-test-001", event_id=event.event_id),
            proposal=ModelProposal(kind="test.echo", payload={"ok": True}),
        )
