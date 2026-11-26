"""Build examples/echo/plugin and run the A-batch Native Plugin IPC tests.

Usage from the repository root:

    python tests/run_batch_a.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conformance import host_a  # noqa: E402
from conformance.common import EVIDENCE, PLUGIN_DIR, REPO_ROOT, TESTS_ROOT, CaseResult, rel, write_json  # noqa: E402

MANIFEST_EXTENSIONS = {"event.ingress", "event.delivery", "tools"}


def plugin_binary() -> Path:
    name = "echo-plugin.exe" if os.name == "nt" else "echo-plugin"
    return PLUGIN_DIR / "bin" / name


def build_plugin() -> Path:
    binary = plugin_binary()
    binary.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GOWORK"] = "off"
    command = ["go", "build", "-trimpath", "-o", str(binary), "."]
    completed = subprocess.run(command, cwd=str(PLUGIN_DIR), env=env, capture_output=True, text=True)
    log = EVIDENCE / "batchA" / "go-build.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f"$ {' '.join(command)}\ncwd={PLUGIN_DIR}\nexit={completed.returncode}\n{completed.stdout}{completed.stderr}",
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise SystemExit(f"go build failed, see {log}")
    if not binary.exists():
        raise SystemExit(f"go build reported success but {binary} is missing")
    print(f"[build] {rel(binary)}")
    return binary


def verify_example_layout() -> None:
    import yaml

    manifest_path = PLUGIN_DIR / "plugin.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["apiVersion"] == "connectionagent.io/plugin-package/v1alpha1"
    assert manifest["kind"] == "Plugin"
    assert manifest["metadata"]["id"] == "example.echo"
    assert manifest["process"]["protocol"] == "connectionagent.io/plugin-ipc/v1alpha1"
    assert manifest["process"]["args"] == ["serve"]
    assert set(manifest["extensions"]) == MANIFEST_EXTENSIONS
    executable = PLUGIN_DIR / manifest["process"]["executable"]
    assert executable.name.startswith("echo-plugin"), executable
    for extension in manifest["extensions"].values():
        for field in ("events", "responses"):
            for entry in extension.get(field, []):
                schema = PLUGIN_DIR / (entry.get("requestSchema") or entry.get("responseSchema"))
                assert schema.exists(), schema
                json.loads(schema.read_text(encoding="utf-8"))
    print(f"[layout] {rel(manifest_path)} and schemas valid")


def write_report(results: list[CaseResult], started_at: str, finished_at: str) -> Path:
    lines = [
        "# A 批 Echo Plugin 原生 IPC 对测结果",
        "",
        f"- 运行时间：{started_at} → {finished_at}",
        "- 设计基线：`odango-chan/ca-agent-next@5b097e28e7197603cf3f00e103a0315c4bce0d79`",
        f"- 示例 Plugin：`{rel(PLUGIN_DIR / 'plugin.yaml')}`",
        f"- 实际二进制：`{rel(plugin_binary())}`",
        "- 构建命令：`go build -trimpath -o bin/echo-plugin.exe .`（cwd=`examples/echo/plugin/`；Linux/macOS 输出 `bin/echo-plugin`）",
        "- 测试命令：`python tests/run_batch_a.py`（cwd=仓库根目录）",
        f"- 实际启动的进程：`{rel(plugin_binary())} serve`（每个用例一份全新进程；同一未修改二进制）",
        "- 测试 Host：`tests/conformance/host_a.py`；负例注入：`tests/conformance/host_a.py::Mutator`",
        "",
        "| 用例 ID | 两端进程及版本 | 输入或变异 | 预期 | 实测 | 状态 | 证据路径 |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in results:
        cells = [
            item.case_id,
            item.processes,
            item.input_mutation,
            item.expected,
            item.actual,
            item.status,
            "<br>".join(f"`{path}`" for path in item.evidence),
        ]
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    lines += [
        "",
        "## 判定说明",
        "",
        "- `PASS` 只用于真实 Go 子进程用例；`A00-fixture` 是文档 JSONL 解析检查，不计作真实进程 PASS。",
        "- 负例不由示例 Plugin 内置模式产生：测试端在 Host 收发边界改写/复制帧；示例实现每个用例都是同一份未修改二进制。",
        "- 证据目录 `tests/evidence/batchA/<case>/` 含脱敏 NDJSON、Plugin stderr 与 summary。",
        "",
        f"总入口：`python tests/run_batch_a.py`（从仓库根目录执行）；本次退出码 {0 if not any(r.status == 'FAIL' for r in results) else 1}。",
    ]
    report = EVIDENCE / "A_BATCH_RESULTS.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report


def main() -> int:
    started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    verify_example_layout()
    binary = build_plugin()
    results = host_a.run(binary)
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(
        TESTS_ROOT / "evidence" / "results.json",
        {
            "startedAt": started_at,
            "finishedAt": finished_at,
            "designSha": "5b097e28e7197603cf3f00e103a0315c4bce0d79",
            "examplePlugin": rel(PLUGIN_DIR / "plugin.yaml"),
            "binary": rel(binary),
            "results": [item.as_dict() for item in results],
        },
    )
    report = write_report(results, started_at, finished_at)
    print("")
    for item in results:
        print(f"{item.status:8} {item.case_id:38} {item.actual[:110]}")
    failed = sum(1 for item in results if item.status == "FAIL")
    print("")
    print(f"cases={len(results)} fail={failed} report={report}")
    print(f"stable report: {TESTS_ROOT / 'A_BATCH_RESULTS.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
