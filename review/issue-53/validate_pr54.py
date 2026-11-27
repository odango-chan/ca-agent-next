#!/usr/bin/env python3
"""PR #54 独立静态验证（Issue #53）。

只读取固定 Git 对象，不修改 PR、restore、refresh 或 main。
依赖：Python 3.11+、markdown-it-py 3.x。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import posixpath
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

BASE = "34e99e0cc54cc82b6b40040286fc84673432ef76"
HEAD = "7452f60ccbc68e1468b52018f59bdc2347cc32d5"
REFRESH = "f63bbce2709284c97d8cd150343d491a3f2958db"
EXPECTED_FILES = [
    "docs/IR/IR 总登记册.md",
    "docs/SR/SR-016-工作台设计移交与条件编辑.md",
    "docs/SR/SR-025-MAS Owner Interface Package Publisher.md",
    "docs/参考与审计/跨仓依赖与可行性审计.md",
    "docs/参考与审计/跨仓设计资产迁移与一致性审计.md",
    "docs/架构设计/CA Agent Next 架构设计.md",
    "docs/架构设计/外部能力域架构总览.md",
    "docs/治理/SR 总索引.md",
    "docs/治理/功能树与需求追踪基线.md",
    "docs/治理/实施状态总览.md",
    "docs/治理/文档总目录与索引.md",
    "docs/治理/现有文档盘点与收敛计划.md",
    "docs/设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md",
    "docs/设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md",
    "docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md",
    "docs/验收与实施/演示验收基线.md",
]
EXPECTED_SR = {
    **{number: "DRAFT" for number in list(range(4, 14)) + list(range(16, 24)) + [26, 27, 28]},
    1: "VERIFIED",
    2: "VERIFIED",
    3: "VERIFIED",
    15: "IMPLEMENTED",
    24: "VERIFIED",
    25: "READY",
}


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.decode('utf-8', 'replace')}")
    return proc.stdout.decode("utf-8")


def lines_from_head(repo: Path, path: str, ref: str = HEAD) -> list[str]:
    return git(repo, "show", f"{ref}:{path}").splitlines()


def inline_text(token) -> str:
    if not token.children:
        return token.content
    parts = []
    for child in token.children:
        if child.type in {"text", "code_inline"}:
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append(" ")
        elif child.type == "image":
            parts.append(child.content)
    return "".join(parts)


def github_slug(text: str) -> str:
    text = text.strip().lower()
    output = []
    for char in text:
        category = unicodedata.category(char)
        if char.isspace():
            output.append("-")
        elif char in "-_" or category[0] in {"L", "N", "M"}:
            output.append(char)
    return "".join(output)


def heading_anchors(tokens) -> set[str]:
    anchors: set[str] = set()
    for index, token in enumerate(tokens[:-1]):
        if token.type == "heading_open" and tokens[index + 1].type == "inline":
            base = github_slug(inline_text(tokens[index + 1]))
            candidate = base
            suffix = 1
            while candidate in anchors:
                candidate = f"{base}-{suffix}"
                suffix += 1
            anchors.add(candidate)
    return anchors


def add_issue(target: list[dict], kind: str, path: str, line: int | None, detail: str) -> None:
    target.append({"kind": kind, "path": path, "line": line, "detail": detail})


def markdown_pipe_count(line: str) -> int:
    """统计表格列数，忽略转义管道与行内代码中的管道。"""
    count = 0
    in_code = False
    escaped = False
    for char in line:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "`":
            in_code = not in_code
        elif char == "|" and not in_code:
            count += 1
    return count - 1 if line.rstrip().endswith("|") else count + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    errors: list[dict] = []
    warnings: list[dict] = []
    metrics: dict = {}
    per_file: dict[str, dict] = {}

    actual_files = [line for line in git(repo, "diff", "--name-only", f"{BASE}..{HEAD}", "--", "docs").splitlines() if line]
    metrics["changed_files"] = len(actual_files)
    if set(actual_files) != set(EXPECTED_FILES) or len(actual_files) != 16:
        add_issue(errors, "DIFF_SCOPE", "", None, f"实际 {len(actual_files)} 文件，与固定 16 文件清单不一致")

    recursive = git(repo, "ls-tree", "-r", "-t", HEAD).splitlines()
    blobs = [line for line in recursive if line.split()[1] == "blob"]
    trees = [line for line in recursive if line.split()[1] == "tree"]
    head_paths = {line.split(None, 3)[3] for line in blobs}
    markdown_paths = sorted(path for path in head_paths if path.lower().endswith(".md"))
    metrics.update({"tracked_blobs": len(blobs), "directory_trees": len(trees), "recursive_entries": len(recursive), "markdown_files": len(markdown_paths)})
    if (len(blobs), len(trees), len(recursive), len(markdown_paths)) != (197, 50, 247, 157):
        add_issue(errors, "TREE_COUNT", "", None, "实际 blob/tree/Markdown 数量不为 197/50/247/157")

    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    anchors_by_path: dict[str, set[str]] = {}
    tokens_by_path: dict[str, list] = {}
    texts_by_path: dict[str, list[str]] = {}
    for path in markdown_paths:
        texts = lines_from_head(repo, path)
        texts_by_path[path] = texts
        tokens = md.parse("\n".join(texts) + "\n")
        tokens_by_path[path] = tokens
        anchors_by_path[path] = heading_anchors(tokens)

    total_links = 0
    local_links = 0
    checked_anchors = 0
    for path in EXPECTED_FILES:
        texts = texts_by_path[path]
        tokens = tokens_by_path[path]
        file_errors_before = len(errors)
        file_links = 0
        for token in tokens:
            if token.type != "inline" or not token.children:
                continue
            for child in token.children:
                if child.type not in {"link_open", "image"}:
                    continue
                href = child.attrGet("href") if child.type == "link_open" else child.attrGet("src")
                if not href:
                    continue
                total_links += 1
                file_links += 1
                split = urlsplit(href)
                if split.scheme or split.netloc or href.startswith("//"):
                    continue
                local_links += 1
                decoded_path = unquote(split.path)
                fragment = unquote(split.fragment)
                if decoded_path:
                    combined = posixpath.join(posixpath.dirname(path), decoded_path)
                    target_path = posixpath.normpath(combined).lstrip("/")
                else:
                    target_path = path
                if target_path.startswith("../"):
                    add_issue(errors, "LINK_ESCAPE", path, getattr(child, "map", [None, None])[0], href)
                    continue
                is_directory = any(candidate.startswith(target_path.rstrip("/") + "/") for candidate in head_paths)
                if target_path not in head_paths and not is_directory:
                    add_issue(errors, "MISSING_PATH", path, None, f"{href} -> {target_path}")
                    continue
                if fragment and target_path.lower().endswith(".md"):
                    checked_anchors += 1
                    if fragment not in anchors_by_path.get(target_path, set()):
                        add_issue(errors, "MISSING_ANCHOR", path, None, f"{href} -> {target_path}#{fragment}")

        metadata: dict[str, list[tuple[int, str]]] = collections.defaultdict(list)
        for number, line in enumerate(texts[:30], 1):
            match = re.match(r"^\s*>\s*([^：]+)：\s*(.*?)\s*$", line)
            if match:
                metadata[match.group(1).strip()].append((number, match.group(2).strip()))
        for key in ("修订日期", "文档版本", "SR 版本"):
            values = metadata.get(key, [])
            distinct = {value for _, value in values}
            if len(values) > 1:
                add_issue(errors, "DUPLICATE_METADATA", path, values[-1][0], f"{key} 重复：{values}")
            if len(distinct) > 1:
                add_issue(errors, "CONFLICTING_METADATA", path, values[-1][0], f"{key} 冲突：{values}")
        header_version = (metadata.get("文档版本") or metadata.get("SR 版本") or [(None, "")])[0][1]
        revision_versions = []
        for number, line in enumerate(texts, 1):
            match = re.match(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*v?(0\.\d+\.\d+)(?:\s|\|)", line)
            if match:
                revision_versions.append((number, match.group(1)))
        if header_version and revision_versions and revision_versions[-1][1] != header_version:
            add_issue(errors, "REVISION_VERSION", path, revision_versions[-1][0], f"头部 {header_version}，最后修订记录 {revision_versions[-1][1]}")
        fence_count = sum(1 for line in texts if re.match(r"^\s*(~~~|```)", line))
        if fence_count % 2:
            add_issue(errors, "UNCLOSED_FENCE", path, None, f"围栏标记数 {fence_count}")
        table_count = 0
        for number, line in enumerate(texts, 1):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            table_count += 1
            expected_columns = len(cells)
            row_number = number - 1
            while row_number >= 1 and texts[row_number - 1].lstrip().startswith("|"):
                actual_columns = markdown_pipe_count(texts[row_number - 1])
                if actual_columns != expected_columns:
                    add_issue(errors, "TABLE_COLUMNS", path, row_number, f"预期 {expected_columns} 列，实际 {actual_columns} 列")
                row_number -= 1
            row_number = number + 1
            while row_number <= len(texts) and texts[row_number - 1].lstrip().startswith("|"):
                actual_columns = markdown_pipe_count(texts[row_number - 1])
                if actual_columns != expected_columns:
                    add_issue(errors, "TABLE_COLUMNS", path, row_number, f"预期 {expected_columns} 列，实际 {actual_columns} 列")
                row_number += 1
        per_file[path] = {
            "markdown_parse": "PASS",
            "tokens": len(tokens),
            "links": file_links,
            "headings": len(anchors_by_path[path]),
            "tables": table_count,
            "errors_new": len(errors) - file_errors_before,
        }

    sr_states: dict[int, str] = {}
    for path in markdown_paths:
        match = re.fullmatch(r"docs/SR/SR-(\d{3})-.+\.md", path)
        if not match:
            continue
        number = int(match.group(1))
        if number in sr_states:
            add_issue(errors, "SR_DUPLICATE", path, None, "SR 编号重复")
        state = None
        for line in texts_by_path[path][:20]:
            state_match = re.match(r"^>\s*状态：\s*([A-Z_]+)", line)
            if state_match:
                state = state_match.group(1)
                break
        if state is None:
            add_issue(errors, "SR_STATE_MISSING", path, None, "缺少状态头")
        else:
            sr_states[number] = state
    if set(sr_states) != set(EXPECTED_SR):
        add_issue(errors, "SR_COVERAGE", "", None, f"实际 SR ID：{sorted(sr_states)}")
    for number, expected in EXPECTED_SR.items():
        actual = sr_states.get(number)
        if actual != expected:
            add_issue(errors, "SR_STATE", f"SR-{number:03d}", None, f"预期 {expected}，实际 {actual}")
    state_counts = dict(sorted(collections.Counter(sr_states.values()).items()))
    metrics["sr_total"] = len(sr_states)
    metrics["sr_states"] = state_counts
    metrics["sr_ids"] = {f"SR-{number:03d}": state for number, state in sorted(sr_states.items())}
    if state_counts != {"DRAFT": 21, "IMPLEMENTED": 1, "READY": 1, "VERIFIED": 4}:
        add_issue(errors, "SR_COUNT", "", None, f"状态统计 {state_counts}")

    diff_check = subprocess.run(
        ["git", "-C", str(repo), "diff", "--check", f"{BASE}..{HEAD}"],
        capture_output=True,
        check=False,
    )
    diff_check_text = diff_check.stdout.decode("utf-8", "replace") + diff_check.stderr.decode("utf-8", "replace")
    trailing_lines = [line for line in diff_check_text.splitlines() if line.endswith("trailing whitespace.")]
    metrics["diff_check_trailing_whitespace_count"] = len(trailing_lines)
    if trailing_lines:
        add_issue(warnings, "TRAILING_WHITESPACE", "", None, f"git diff --check 报告 {len(trailing_lines)} 处行尾空格")

    metrics.update({"markdown_links": total_links, "local_links": local_links, "checked_anchors": checked_anchors})
    result = {
        "issue": 53,
        "pr": 54,
        "base": BASE,
        "head": HEAD,
        "refresh": REFRESH,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python": sys.version,
        "markdown_it": __import__("markdown_it").__version__,
        "overall": "PASS" if not errors else "FAIL",
        "metrics": metrics,
        "per_file": per_file,
        "errors": errors,
        "warnings": warnings,
        "not_run": [
            "外部 HTTP URL 的实时可达性",
            "SR-003 Linux/Windows 测试的本地重跑（本脚本仅核验固定文档与 Git 对象）",
            "外部仓库测试与产品 Acceptance",
            "DeepSeek Harness 自动消费 Review Context Artifact",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall": result["overall"], "metrics": metrics, "errors": len(errors), "warnings": len(warnings)}, ensure_ascii=False, indent=2))
    for issue in errors:
        print(f"ERROR {issue['kind']} {issue['path']}:{issue['line']} {issue['detail']}")
    for issue in warnings:
        print(f"WARNING {issue['kind']} {issue['detail']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
